"""
Importa expositores desde un archivo Excel y asigna automáticamente
sus logos (carpeta 'logos/') y fotos de productos (carpeta 'fotos/').

Uso:
    python manage.py importar_expositores_excel --dry-run
    python manage.py importar_expositores_excel
    python manage.py importar_expositores_excel --excel ruta\al\archivo.xlsx
    python manage.py importar_expositores_excel --limpiar
"""
import re
import unicodedata
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Expositor, FotoProducto


# =============================================================
#  UTILIDADES
# =============================================================

def normalizar(texto):
    """Quita acentos, minúsculas, sin espacios ni símbolos. Para comparar nombres."""
    if texto is None:
        return ""
    if isinstance(texto, float) and pd.isna(texto):
        return ""
    texto = str(texto)
    # Quitar acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    # Minúsculas y sin caracteres raros
    texto = re.sub(r'[^a-z0-9]+', '', texto.lower())
    return texto


def limpiar_numero(valor):
    """Convierte '9141120014.0' o '99 33 88 55 63' en '9141120014' o '9933885563'."""
    if valor is None:
        return ''
    if isinstance(valor, float) and pd.isna(valor):
        return ''

    s = str(valor).strip()

    # Si es algo tipo "9141120014.0" → quitar el ".0"
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]

    # Buscar el primer número de 10 dígitos (formato de teléfono mexicano)
    limpio = s.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
    m = re.search(r'\d{10}', limpio)
    if m:
        return m.group(0)

    # Fallback: solo los dígitos que haya
    return re.sub(r'\D', '', s)


def parsear_si_no(valor):
    """Devuelve True/False desde 'Si', 'No', 'Sí', 'si', etc."""
    if valor is None:
        return False
    if isinstance(valor, float) and pd.isna(valor):
        return False
    if isinstance(valor, (int, float)):
        return bool(valor)
    return str(valor).strip().lower() in ('si', 'sí', 'yes', 'y', 'true', '1')


def parsear_stand(valor):
    """
    Limpia el número de stand.
    Solo acepta números cortos (1-999). Cualquier otra cosa → vacío.
    """
    if valor is None:
        return ''
    if isinstance(valor, float) and pd.isna(valor):
        return ''

    s = str(valor).strip()

    # Casos comunes de "vacío"
    vacios = ('', 'none', 'ninguno', 'pendiente', 'todavía está pendiente.',
              'no asignado aun', 'sin número', 'sin numero', 's/n', '0', '0.0')
    if s.lower() in vacios:
        return ''

    # Quitar el ".0" de los números tipo "10.0"
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]

    # Solo aceptar números cortos (1-999)
    if re.match(r'^\d{1,3}$', s):
        return s

    # Si no es un número válido → vacío
    return ''


def parsear_categoria(menu_texto):
    """
    Infiere la categoría principal del expositor según su menú.
    Regla: si tiene butifarra (de cualquier tipo) → tradicional.
    Solo se clasifica como quesos/bebidas si NO tiene butifarra.
    """
    # Castear todo a string primero (algunos menús vienen como número)
    t = str(menu_texto or '').lower()

    tiene_butifarra = 'butifarra' in t
    tiene_queso = 'queso' in t
    tiene_longaniza = 'longaniza' in t
    tiene_bebidas = 'refresco' in t or 'coca' in t or 'agua' in t
    tiene_postres = 'postre' in t or 'flan' in t or 'gelatina' in t

    # Prioridad: si vende butifarra, es tradicional (es el producto estrella)
    if tiene_butifarra:
        return 'tradicional'

    # Solo si NO vende butifarra:
    if tiene_queso or tiene_longaniza:
        return 'quesos'
    if tiene_bebidas or tiene_postres:
        return 'bebidas'

    return 'tradicional'


def parsear_precio_desde(menu_texto):
    """
    Extrae el precio mínimo del menú.
    Devuelve None si no encuentra nada.
    """
    if menu_texto is None:
        return None

    # Castear a string (por si viene como número)
    texto = str(menu_texto)
    if not texto.strip() or texto.lower() == 'nan':
        return None

    candidatos = []

    # Patrón 1: $N o $N.NN
    for m in re.finditer(r'\$\s*(\d{2,5})(?:\.\d{2})?', texto):
        try:
            candidatos.append(Decimal(m.group(1)))
        except InvalidOperation:
            continue

    # Patrón 2: N (seguido de "pesos", "kg", "kilo", "la orden", etc.)
    for m in re.finditer(
        r'(\d{2,5})\s*(?:pesos|peso|kg|kilo|la orden|el litro)',
        texto,
        re.I
    ):
        try:
            candidatos.append(Decimal(m.group(1)))
        except InvalidOperation:
            continue

    return min(candidatos) if candidatos else None


def match_expositor_por_archivo(filename, expositores):
    """
    Devuelve el Expositor al que pertenece el archivo de foto según su nombre.
    Ej: 'IMG-20260904-WA0007 - Sandibel Taracena.jpg' → buscar 'sandibel taracena'
    """
    base = Path(filename).stem
    if ' - ' in base:
        sufijo = base.rsplit(' - ', 1)[-1]
    else:
        sufijo = base

    norm_sufijo = normalizar(sufijo)
    if not norm_sufijo:
        return None

    for exp in expositores:
        nombre_norm = normalizar(exp.nombre_expositor)
        empresa_norm = normalizar(exp.nombre_empresa)

        if nombre_norm and (nombre_norm in norm_sufijo or norm_sufijo in nombre_norm):
            return exp
        if empresa_norm and (empresa_norm in norm_sufijo or norm_sufijo in empresa_norm):
            return exp
    return None


def match_expositor_por_logo(filename, expositores):
    """
    Los logos tienen nombres como:
        'LOGO - Norma Almeida_1.jpg'
        'LOGO BUTIFARRAS - Sebastian Lopez_1.jpg'
        '3 - NIÑON JR POST - PEDRO ALEJANDRO PÉREZ MONDRAGÓN.png'
    Buscamos por la parte después de ' - '.
    """
    base = Path(filename).stem
    # Quitar sufijos '_1', '~2', etc.
    base = re.sub(r'[_~]\d+$', '', base)

    partes = [p.strip() for p in base.split(' - ')]

    # Probar cada parte del nombre como candidato
    candidatos = []
    if len(partes) >= 2:
        candidatos.append(partes[-1])
        candidatos.append(partes[-2])
    candidatos.extend(partes)

    for cand in candidatos:
        norm = normalizar(cand)
        if not norm:
            continue
        for exp in expositores:
            if normalizar(exp.nombre_expositor) and normalizar(exp.nombre_expositor) in norm:
                return exp
            if normalizar(exp.nombre_empresa) and normalizar(exp.nombre_empresa) in norm:
                return exp
    return None


# =============================================================
#  COMANDO
# =============================================================

class Command(BaseCommand):
    help = "Importa expositores desde Excel y asigna logos/fotos automáticamente"

    def add_arguments(self, parser):
        parser.add_argument(
            '--excel',
            default='formulario.xlsx',
            help='Ruta al archivo Excel (default: formulario.xlsx en la raíz)'
        )
        parser.add_argument(
            '--logos-dir',
            default='logos',
            help='Carpeta con los logos (default: logos)'
        )
        parser.add_argument(
            '--fotos-dir',
            default='fotos',
            help='Carpeta con las fotos de productos (default: fotos)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que haría sin guardar nada'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Borra todos los expositores antes de importar'
        )

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR)
        excel_path = base / opts['excel']
        logos_dir = base / opts['logos_dir']
        fotos_dir = base / opts['fotos_dir']
        dry_run = opts['dry_run']

        if not excel_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ No existe el Excel: {excel_path}"))
            return
        if not logos_dir.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ No existe la carpeta de logos: {logos_dir}"))
        if not fotos_dir.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ No existe la carpeta de fotos: {fotos_dir}"))

        # Limpiar si se pidió
        if opts['limpiar'] and not dry_run:
            n, _ = Expositor.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"🧹 Borrados {n} registros previos"))

        # ---------- Leer Excel ----------
        self.stdout.write(f"\n📄 Leyendo Excel: {excel_path}")
        df = pd.read_excel(excel_path, header=0, engine='openpyxl')

        # Limpiar nombres de columna (quitar \n, espacios extra)
        df.columns = [
            str(c).replace('<br>', '\n').replace('\r\n', '\n').strip()
            for c in df.columns
        ]

        # Renombrar columnas al formato interno
        # (startswith tolera cambios menores en el texto)
        nuevos_nombres = {}
        for c in df.columns:
            if c.startswith('Nombre del expositor'):
                nuevos_nombres[c] = 'nombre_expositor'
            elif c.startswith('Marca o nombre de la empresa'):
                nuevos_nombres[c] = 'nombre_empresa'
            elif c.startswith('Correo electrónico de contacto'):
                nuevos_nombres[c] = 'email'
            elif c.startswith('Número de contacto'):
                nuevos_nombres[c] = 'telefono'
            elif c.startswith('Número de stand'):
                nuevos_nombres[c] = 'stand'
            elif c.startswith('Enlace a redes sociales'):
                nuevos_nombres[c] = 'red1'
            elif c.startswith('Enlace adicional de redes sociales'):
                nuevos_nombres[c] = 'red2'
            elif c.startswith('Menu completo'):
                nuevos_nombres[c] = 'menu'
            elif 'Aceptan pago con tarjeta' in c:
                nuevos_nombres[c] = 'acepta_tarjeta'
            elif c.startswith('Link de Google Maps'):
                nuevos_nombres[c] = 'maps'
            elif c.startswith('Logo de la marca'):
                nuevos_nombres[c] = 'logo_url'
            elif c.startswith('Fotos de productos'):
                nuevos_nombres[c] = 'fotos_urls'

        df = df.rename(columns=nuevos_nombres)

        self.stdout.write(f"   {len(df)} filas leídas\n")

        # ---------- Crear/actualizar expositores ----------
        creados, actualizados, errores = 0, 0, 0

        for idx, row in df.iterrows():
            nombre_expositor = str(row.get('nombre_expositor', '') or '').strip()
            nombre_empresa = str(row.get('nombre_empresa', '') or '').strip()

            if not nombre_expositor or nombre_expositor.lower() == 'nan':
                self.stdout.write(self.style.WARNING(f"   ⏭️  Fila {idx+2}: sin nombre, se omite"))
                continue

            # Forzar que el menú sea string
            menu = row.get('menu', '')
            if menu is None or (isinstance(menu, float) and pd.isna(menu)):
                menu = ''
            menu = str(menu).strip()
            if menu.lower() == 'nan':
                menu = ''

            # Redes sociales
            red1 = row.get('red1', '') or ''
            red2 = row.get('red2', '') or ''
            if str(red1).strip().lower() in ('ninguno', 'nan', ''):
                red1 = ''
            if str(red2).strip().lower() in ('ninguno', 'nan', ''):
                red2 = ''

            # Limpiar campos
            stand = parsear_stand(row.get('stand', ''))
            telefono = limpiar_numero(row.get('telefono', ''))

            # Email
            email = str(row.get('email', '') or '').strip()
            if email.lower() == 'nan':
                email = ''

            # Maps vs dirección
            maps_raw = row.get('maps', '') or ''
            maps_raw = str(maps_raw).strip()
            if maps_raw.lower() == 'nan':
                maps_raw = ''
            link_maps = maps_raw if maps_raw.startswith('http') else ''
            direccion = maps_raw if maps_raw and not maps_raw.startswith('http') else ''

            defaults = {
                'nombre_expositor': nombre_expositor[:200],
                'nombre_empresa': (nombre_empresa or nombre_expositor)[:200],
                'email_contacto': email[:200],
                'numero_contacto': telefono,
                'numero_stand': stand,
                'enlace_red_social_1': str(red1)[:500] if str(red1).startswith('http') else '',
                'enlace_red_social_2': str(red2)[:500] if str(red2).startswith('http') else '',
                'redes_sociales_texto': ' | '.join(
                    s for s in [str(red1)[:200], str(red2)[:200]]
                    if s and not str(s).startswith('http')
                )[:300],
                'menu_completo': menu,
                'acepta_tarjeta': parsear_si_no(row.get('acepta_tarjeta', '')),
                'link_google_maps': link_maps[:500],
                'direccion_negocio': direccion[:300],
                'categoria': parsear_categoria(menu),
                'precio_desde': parsear_precio_desde(menu),
                'activo': True,
            }

            if dry_run:
                self.stdout.write(
                    f"   [DRY] {defaults['nombre_empresa']} | "
                    f"stand={stand or '—'} | cat={defaults['categoria']} | "
                    f"${defaults['precio_desde'] or '—'}"
                )
                creados += 1
                continue

            try:
                obj, created = Expositor.objects.update_or_create(
                    nombre_empresa=defaults['nombre_empresa'],
                    defaults=defaults,
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ {nombre_empresa}: {e}"))
                errores += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Expositores → creados: {creados} | actualizados: {actualizados} | errores: {errores}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  DRY RUN: no se guardó nada ni se copiaron imágenes."
            ))
            return

        # ---------- Asignar logos ----------
        self.stdout.write("\n🖼️  Procesando logos...")
        expositores = list(Expositor.objects.filter(activo=True))
        logos_asignados, logos_sin_match, logos_ya_tenian = 0, 0, 0

        if logos_dir.exists():
            for archivo in sorted(logos_dir.iterdir()):
                if archivo.is_dir() or archivo.name.startswith('.'):
                    continue
                if archivo.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                    continue

                exp = match_expositor_por_logo(archivo.name, expositores)
                if not exp:
                    self.stdout.write(f"   ⚠️  Sin match: {archivo.name}")
                    logos_sin_match += 1
                    continue

                if exp.logo:
                    logos_ya_tenian += 1
                    continue

                try:
                    with open(archivo, 'rb') as f:
                        exp.logo.save(archivo.name, File(f), save=True)
                    self.stdout.write(f"   ✔ {archivo.name}  →  {exp.nombre_empresa}")
                    logos_asignados += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ {archivo.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"   Logos asignados: {logos_asignados} | "
            f"ya tenían: {logos_ya_tenian} | sin match: {logos_sin_match}"
        ))

        # ---------- Asignar fotos ----------
        self.stdout.write("\n📸 Procesando fotos de productos...")
        fotos_asignadas, fotos_sin_match, fotos_ya_tenian = 0, 0, 0

        if fotos_dir.exists():
            for archivo in sorted(fotos_dir.iterdir()):
                if archivo.is_dir() or archivo.name.startswith('.'):
                    continue
                if archivo.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                    continue

                exp = match_expositor_por_archivo(archivo.name, expositores)
                if not exp:
                    self.stdout.write(f"   ⚠️  Sin match: {archivo.name}")
                    fotos_sin_match += 1
                    continue

                # Evitar duplicados por nombre de archivo
                if exp.fotos.filter(descripcion=archivo.name).exists():
                    fotos_ya_tenian += 1
                    continue

                try:
                    foto = FotoProducto(expositor=exp, descripcion=archivo.name[:200])
                    with open(archivo, 'rb') as f:
                        foto.imagen.save(archivo.name, File(f), save=True)
                    fotos_asignadas += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ {archivo.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"   Fotos asignadas: {fotos_asignadas} | "
            f"ya tenían: {fotos_ya_tenian} | sin match: {fotos_sin_match}"
        ))

        # ---------- Resumen final ----------
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Importación completa.\n"
            f"   Expositores: {Expositor.objects.count()}\n"
            f"   Fotos: {FotoProducto.objects.count()}\n"
        ))