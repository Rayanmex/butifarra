"""
Comando: python manage.py cargar_expositores
Carga expositores desde expositores.xlsx y descarga imágenes de Google Drive.
"""
import re
import time
from decimal import Decimal, InvalidOperation

import requests
import openpyxl
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Expositor, FotoProducto


DRIVE_DOWNLOAD = 'https://drive.google.com/uc?export=download&id={}'


def extraer_id_drive(url):
    if not url:
        return None
    url = url.strip()
    if 'open?id=' in url:
        return url.split('open?id=')[-1].split('&')[0].split(',')[0].strip()
    match = re.search(r'/file/d/([^/]+)', url)
    if match:
        return match.group(1)
    if 'id=' in url:
        return url.split('id=')[-1].split('&')[0].strip()
    return None


def separar_urls(celda):
    if not celda:
        return []
    texto = str(celda).strip()
    if texto.lower() in ['ninguno', 'no', 'n/a', '']:
        return []
    partes = re.split(r'[,\n]+', texto)
    return [p.strip() for p in partes if p.strip()]


def descargar_desde_drive(url, nombre_archivo):
    file_id = extraer_id_drive(url)
    if not file_id:
        return None
    try:
        download_url = DRIVE_DOWNLOAD.format(file_id)
        session = requests.Session()
        response = session.get(download_url, timeout=30, stream=True)
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            confirm_token = None
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    confirm_token = value
                    break
            if confirm_token:
                response = session.get(
                    download_url + '&confirm=' + confirm_token,
                    timeout=30, stream=True
                )
        if response.status_code == 200:
            content = response.content
            if len(content) < 500:
                return None
            return ContentFile(content, name=nombre_archivo)
    except Exception as e:
        print(f"   Error: {e}")
    return None


def limpiar_numero(valor):
    if not valor:
        return ""
    v = str(valor).strip()
    if v.lower() in ['ninguno', 'pendiente', 'no asignado aun',
                     'todavia esta pendiente.', '0', 'no', '']:
        return ""
    return v


def limpiar_url(valor):
    if not valor:
        return None
    v = str(valor).strip()
    if v.lower() in ['ninguno', 'n/a', 'no', '']:
        return None
    return v


def inferir_categoria(menu):
    if not menu:
        return 'tradicional'
    m = menu.lower()
    kw_esp = ['camaron', 'jaiba', 'tamarindo', 'crema de ajo',
              'mango habanero', 'bbq', 'chiltepin', 'ahumada',
              'adobada', 'enchilada', 'picana', 'provolone']
    kw_mix = ['queso de puerco', 'longaniza', 'barbacoa', 'postres', 'flan', 'gelatina']
    if any(k in m for k in kw_esp):
        return 'especialidad'
    if any(k in m for k in kw_mix):
        return 'mixto'
    return 'tradicional'


def inferir_especialidades(menu):
    if not menu:
        return ""
    m = menu.lower()
    pares = [
        ('tradicional', 'tradicional'), ('pollo', 'pollo'), ('pavo', 'pavo'),
        ('camaron', 'camaron'), ('jaiba', 'jaiba'), ('queso', 'queso'),
        ('longaniza', 'longaniza'), ('crema de ajo', 'crema de ajo'),
        ('mango habanero', 'mango habanero'), ('bbq', 'BBQ'),
        ('barbiquiur', 'BBQ'), ('tamarindo', 'tamarindo'),
        ('chiltepin', 'chiltepin'), ('ahumada', 'ahumada'),
        ('adobada', 'adobada'), ('enchilada', 'enchilada'),
        ('picana', 'picana'), ('provolone', 'queso provolone'),
        ('envinada', 'envinadas'), ('enjamonada', 'enjamonada'),
        ('ajo parmesano', 'ajo parmesano'), ('limon pepper', 'limon pepper'),
        ('salsa de zanahoria', 'salsa de zanahoria'), ('ranchera', 'salsa ranchera'),
        ('pasitas', 'pasitas'), ('barbacoa', 'barbacoa'),
        ('carne chinameca', 'carne chinameca'), ('patitas curtidas', 'patitas curtidas'),
    ]
    encontradas = []
    for kw, etiqueta in pares:
        if kw in m and etiqueta not in encontradas:
            encontradas.append(etiqueta)
    return ", ".join(encontradas)


def inferir_precio_minimo(menu):
    if not menu:
        return None
    precios = re.findall(r'\$\s*(\d+(?:[\.,]\d{1,2})?)', menu)
    if not precios:
        return None
    try:
        valores = []
        for p in precios:
            p = p.replace(',', '.')
            valores.append(Decimal(p))
        valores = [v for v in valores if Decimal("5") < v < Decimal("5000")]
        return min(valores) if valores else None
    except (InvalidOperation, ValueError):
        return None


class Command(BaseCommand):
    help = 'Carga expositores desde expositores.xlsx'

    def add_arguments(self, parser):
        parser.add_argument('--excel', default='expositores.xlsx',
                            help='Ruta del archivo Excel')
        parser.add_argument('--borrar', action='store_true',
                            help='Borra todos los expositores antes de cargar')

    def handle(self, *args, **options):
        excel_path = options['excel']

        if options['borrar']:
            self.stdout.write(self.style.WARNING('Borrando expositores existentes...'))
            FotoProducto.objects.all().delete()
            Expositor.objects.all().delete()

        self.stdout.write(f"\nLeyendo {excel_path}...")
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        filas = list(ws.iter_rows(min_row=2, values_only=True))
        self.stdout.write(f"{len(filas)} filas encontradas.\n")

        creados = 0
        actualizados = 0
        errores = []

        for i, fila in enumerate(filas, start=2):
            if not fila or not fila[1]:
                continue

            (marca_temporal, nombre_expositor, nombre_empresa, logo_url,
             email, telefono, stand, red1, red2, menu, acepta_tarjeta,
             maps, fotos_celda) = (list(fila) + [None] * 13)[:13]

            if not nombre_empresa:
                continue

            nombre_empresa = str(nombre_empresa).strip()
            self.stdout.write(f"[{i}] {nombre_empresa}")

            email_limpio = (str(email).strip() if email and '@' in str(email)
                            else 'sin-email@ejemplo.com')
            telefono_limpio = str(telefono).strip() if telefono else ''
            stand_limpio = limpiar_numero(stand)

            red1_limpia = limpiar_url(red1)
            red2_limpia = limpiar_url(red2)
            redes_texto = None
            if red1_limpia and not red1_limpia.startswith('http'):
                redes_texto = red1_limpia
                red1_limpia = None
            if red2_limpia and not red2_limpia.startswith('http'):
                redes_texto = (redes_texto + " | " + red2_limpia) if redes_texto else red2_limpia
                red2_limpia = None

            menu_texto = str(menu).strip() if menu else ''
            acepta_tarjeta_bool = str(acepta_tarjeta).strip().lower() in ['si', 'yes', 'true', '1']

            maps_str = str(maps).strip() if maps else ''
            link_maps = maps_str if maps_str.startswith('http') else None
            direccion = maps_str if not maps_str.startswith('http') and maps_str else None

            categoria = inferir_categoria(menu_texto)
            especialidades = inferir_especialidades(menu_texto)
            precio_min = inferir_precio_minimo(menu_texto)
            descripcion = (f"{nombre_empresa}: {especialidades[:120]}"
                           if especialidades else f"Butifarras y productos de {nombre_empresa}")

            expositor, created = Expositor.objects.update_or_create(
                nombre_empresa=nombre_empresa,
                defaults={
                    'nombre_expositor': str(nombre_expositor).strip() if nombre_expositor else nombre_empresa,
                    'email_contacto': email_limpio,
                    'numero_contacto': telefono_limpio,
                    'numero_stand': stand_limpio,
                    'enlace_red_social_1': red1_limpia,
                    'enlace_red_social_2': red2_limpia,
                    'redes_sociales_texto': redes_texto,
                    'menu_completo': menu_texto,
                    'acepta_tarjeta': acepta_tarjeta_bool,
                    'link_google_maps': link_maps,
                    'direccion_negocio': direccion,
                    'categoria': categoria,
                    'especialidades': especialidades,
                    'precio_desde': precio_min,
                    'descripcion': descripcion,
                    'activo': True,
                }
            )
            if created:
                creados += 1
                self.stdout.write("   Creado")
            else:
                actualizados += 1
                self.stdout.write("   Actualizado")

            # Logo
            if logo_url and not expositor.logo:
                self.stdout.write("   Descargando logo...")
                archivo = descargar_desde_drive(
                    str(logo_url),
                    f"{slugify(nombre_empresa)}_logo.jpg"
                )
                if archivo:
                    expositor.logo.save(
                        f"{slugify(nombre_empresa)}_logo.jpg",
                        archivo, save=True
                    )
                    self.stdout.write("   Logo guardado")
                else:
                    errores.append(f"Logo fallo: {nombre_empresa}")

            # Fotos
            fotos_urls = separar_urls(fotos_celda)
            if fotos_urls:
                self.stdout.write(f"   {len(fotos_urls)} fotos...")
                for idx, url_foto in enumerate(fotos_urls, start=1):
                    archivo = descargar_desde_drive(
                        url_foto,
                        f"{slugify(nombre_empresa)}_foto{idx}.jpg"
                    )
                    if archivo:
                        FotoProducto.objects.create(
                            expositor=expositor,
                            imagen=archivo,
                            descripcion=f"Foto {idx}"
                        )
                    time.sleep(0.3)  # pausa para no saturar Drive

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"Creados: {creados}"))
        self.stdout.write(self.style.SUCCESS(f"Actualizados: {actualizados}"))
        self.stdout.write(self.style.SUCCESS(f"Total en BD: {Expositor.objects.count()}"))
        self.stdout.write("=" * 50)

        if errores:
            self.stdout.write(self.style.WARNING(f"\n{len(errores)} errores:"))
            for e in errores[:15]:
                self.stdout.write(f"   - {e}")