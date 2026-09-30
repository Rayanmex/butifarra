"""
Comando: python manage.py parsear_menus
Parsea el menu_completo de cada expositor y crea objetos Producto.

Uso:
    python manage.py parsear_menus              # Parsea todos los expositores
    python manage.py parsear_menus --limpiar    # Borra productos existentes antes
    python manage.py parsear_menus --expositor "Butifarras Lili"  # Solo uno
"""
import re
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Expositor, Producto


# ============ DICCIONARIOS DE DETECCIÓN ============

# Palabras clave → categoría
CATEGORIA_KW = [
    # Orden importa: primero las más específicas
    ('butifarra_especialidad', ['camarón', 'camaron', 'jaiba', 'pollo', 'pavo',
                                 'enjamonada', 'rellena', 'provolone', 'envinada',
                                 'picaña', 'picana', 'ahumada', 'adobada',
                                 'enchilada', 'pasitas']),
    ('butifarra_tradicional', ['butifarra tradicional', 'butifarras tradicionales',
                                'tradicional', 'butifarra']),
    ('queso', ['queso de puerco', 'queso gourmet', 'queso']),
    ('longaniza', ['longaniza']),
    ('carne', ['carne chinameca', 'barbacoa', 'picaña', 'picana', 'carne']),
    ('patitas', ['patitas curtidas', 'patitas']),
    ('salsa', ['crema de ajo', 'mango habanero', 'bbq', 'barbiquiur',
               'tamarindo', 'chiltepín', 'chiltepin', 'salsa',
               'aderezo', 'aderezos', 'limón pepper', 'limon pepper',
               'ajo parmesano', 'ranchera', 'zanahoria']),
    ('bebida', ['coca', 'refresco', 'agua', 'jamaica', 'horchata',
                'peñafiel', 'cristal', 'bebida', 'jugo']),
    ('postre', ['flan', 'gelatina', 'postre', 'dulce']),
    ('combo', ['combo', 'paquete']),
]

# Palabras clave → unidad
UNIDAD_KW = [
    ('orden_fam', ['familiar', '21 pz', '21 piezas']),
    ('orden_media', ['media orden', '11 pz', '11 piezas']),
    ('orden_ind', ['individual', '5 pz', '5 piezas']),
    ('1/2kg', ['1/2 kg', '1/2kg', 'medio kilo', '½ kg', '½kg', '½ tradicional']),
    ('1/4kg', ['1/4 kg', '1/4kg', 'cuarto']),
    ('kg', ['1 kg', '1kg', '1 kilo', 'el kilo', 'kilo']),
    ('litro', ['litro', 'lt']),
    ('rebanada', ['rebanada']),
    ('pieza', ['pieza', 'pz', 'por pieza']),
    ('bote', ['bote']),
    ('orden', ['orden']),
]

# Regex para precio: captura "$350" o números sueltos
# NO captura números dentro de paréntesis (21 Piezas) ni pegados a "pz"
RE_PRECIO = re.compile(r'(?:\$\s*)?(\d{1,4}(?:[.,]\d{1,2})?)(?!\d)(?!\s*(?:pz|pieza|piezas|kg|kilo|kilos|gr|gramos))')


def normalizar(texto):
    """Minúsculas sin acentos."""
    if not texto:
        return ''
    import unicodedata
    t = texto.lower()
    t = unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('ASCII')
    return t


def detectar_categoria(texto):
    """Detecta la categoría del producto."""
    t = normalizar(texto)
    for cat, kws in CATEGORIA_KW:
        for kw in kws:
            if normalizar(kw) in t:
                return cat
    return 'otro'


def detectar_unidad(texto):
    """Detecta la unidad del producto."""
    t = normalizar(texto)
    for unidad, kws in UNIDAD_KW:
        for kw in kws:
            if normalizar(kw) in t:
                return unidad
    return 'unidad'


def extraer_precios(texto):
    """
    Extrae precios del texto.
    - Prioriza números con $ adelante.
    - Ignora números dentro de paréntesis (ej: "(21 Piezas)").
    - Ignora números pegados a "pz", "pieza", "kg", etc.
    """
    # Primero: quitar todo lo que esté entre paréntesis para no confundir
    texto_sin_parentesis = re.sub(r'\([^)]*\)', '', texto)

    precios = []
    # Buscar números con $ (más confiables)
    for m in re.finditer(r'\$\s*(\d{1,4}(?:[.,]\d{1,2})?)', texto_sin_parentesis):
        try:
            v = Decimal(m.group(1).replace(',', '.'))
            if Decimal("15") <= v <= Decimal("9999"):
                precios.append(v)
        except (InvalidOperation, ValueError):
            continue

    # Si no hay con $, buscar números sueltos
    if not precios:
        for m in re.finditer(
            r'(?<!\d)(\d{2,4})(?!\d)(?!\s*(?:pz|pieza|piezas|kg|kilo|kilos|gr|gramos|personas))',
            texto_sin_parentesis
        ):
            try:
                v = Decimal(m.group(1))
                if Decimal("15") <= v <= Decimal("9999"):
                    precios.append(v)
            except (InvalidOperation, ValueError):
                continue

    return precios


def limpiar_nombre(texto):
    """Limpia el texto para usarlo como nombre de producto."""
    t = texto.strip()
    # Quitar precios
    t = RE_PRECIO.sub('', t)
    # Quitar unidades al inicio: "1kg", "1 kilo", "1kilo", "1/2 kg", etc.
    t = re.sub(r'^\s*\d+(?:[/\.]\d+)?\s*(?:kg|kilo|kilos|g|gr|gramos|litro|lt|pz|pieza|piezas)?\b',
               '', t, flags=re.IGNORECASE)
    # Quitar unidades sueltas
    t = re.sub(r'\b\d+\s*(?:kg|kilo|kilos|pz|pieza|piezas|litro|lt)\b',
               '', t, flags=re.IGNORECASE)
    # Quitar "( 21 Piezas)" o "(21 piezas)"
    t = re.sub(r'\(\s*\d+\s*(?:pz|pieza|piezas)\s*\)', '', t, flags=re.IGNORECASE)
    # Quitar paréntesis sueltos
    t = re.sub(r'\(\s*\)', '', t)
    t = re.sub(r'\(\s*\d*\s*(?:pz|pieza|piezas)?\s*\)?', '', t, flags=re.IGNORECASE)
    # Quitar paréntesis sin cerrar al final
    t = re.sub(r'\([^)]*$', '', t)
    # Quitar "el cuartito", "la orden", etc. al final
    t = re.sub(r'\b(el|la|los|las)\s+(cuartito|orden|kilo|litro|pieza|rebanada|bote)\b',
               '', t, flags=re.IGNORECASE)
    # Quitar signos sueltos
    t = re.sub(r'[:;\-\*\•]+', ' ', t)
    # Quitar letras sueltas al final (residuo de "Piezas" -> "s")
    t = re.sub(r'\s+[a-zA-Z]$', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' .,-•()')
    return t or None



def separar_lineas_menu(menu):
    """
    Divide el menú en items, arrastrando el título de sección cuando aparezca.
    Retorna lista de tuplas (item, titulo_seccion).
    """
    if not menu:
        return []

    if '\n' in menu:
        lineas = menu.split('\n')
    else:
        lineas = menu.split(',')

    resultado = []
    titulo_actual = None

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        # ¿Tiene precio? Si no, es un título de sección
        precios = RE_PRECIO.findall(linea)
        tiene_precio = any(Decimal(p.replace(',', '.')) >= Decimal("15")
                          for p in precios
                          if p.replace(',', '.').replace('.', '').isdigit())

        if not tiene_precio:
            # Es un título de sección
            titulo_actual = linea.strip(' :•-*')
            continue

        resultado.append((linea, titulo_actual))

    return resultado


def parsear_item(item_con_titulo):
    """
    Parsea un item (línea + título de sección).
    Retorna lista de dicts.
    """
    if isinstance(item_con_titulo, tuple):
        texto, titulo = item_con_titulo
    else:
        texto, titulo = item_con_titulo, None

    resultados = []
    precios = extraer_precios(texto)
    if not precios:
        return resultados

    # Unidades detectadas
    unidades = []
    t_norm = normalizar(texto)
    for unidad, kws in UNIDAD_KW:
        for kw in kws:
            if normalizar(kw) in t_norm:
                if unidad not in [u for u, _ in unidades]:
                    unidades.append((unidad, kw))
                break

    # Nombre base
    nombre_base = limpiar_nombre(texto)

    # Si el nombre base es muy corto (<15 chars) y hay título, combinarlo
    if titulo and (not nombre_base or len(nombre_base) < 15):
        nombre_base = f"{titulo} - {nombre_base}" if nombre_base else titulo
    elif titulo and nombre_base:
        # Detectar si el nombre base NO menciona el título → agregarlo
        if normalizar(titulo) not in normalizar(nombre_base):
            nombre_base = f"{titulo} - {nombre_base}"

    # Categoría: usar el título + el texto para mejor detección
    texto_categoria = f"{titulo or ''} {texto}"
    categoria = detectar_categoria(texto_categoria)

    if len(precios) == len(unidades) and len(precios) > 1:
        for precio, (unidad, _) in zip(precios, unidades):
            if nombre_base:
                resultados.append({
                    'nombre': nombre_base[:200],
                    'categoria': categoria,
                    'unidad': unidad,
                    'precio': precio,
                    'descripcion': texto[:300],
                })
    else:
        unidad = unidades[0][0] if unidades else 'unidad'
        if nombre_base:
            resultados.append({
                'nombre': nombre_base[:200],
                'categoria': categoria,
                'unidad': unidad,
                'precio': precios[0],
                'descripcion': texto[:300],
            })

    return resultados


class Command(BaseCommand):
    help = 'Parsea los menús de expositores y crea Productos'

    def add_arguments(self, parser):
        parser.add_argument('--limpiar', action='store_true',
                            help='Borra todos los productos antes de parsear')
        parser.add_argument('--expositor', type=str, default=None,
                            help='Parsear solo un expositor (nombre_empresa)')

    def handle(self, *args, **options):
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('Borrando productos existentes...'))
            Producto.objects.all().delete()

        if options['expositor']:
            expositores = Expositor.objects.filter(
                nombre_empresa__iexact=options['expositor']
            )
            if not expositores.exists():
                self.stdout.write(self.style.ERROR(
                    f'No se encontró expositor: {options["expositor"]}'
                ))
                return
        else:
            expositores = Expositor.objects.all()

        total_creados = 0
        sin_productos = []
        resumen_por_categoria = {}

        for exp in expositores:
            self.stdout.write(f'\n[{exp.nombre_empresa}]')
            if not exp.menu_completo:
                self.stdout.write('   Sin menú')
                sin_productos.append(exp.nombre_empresa)
                continue

            items = separar_lineas_menu(exp.menu_completo)
            creados_este = 0

            with transaction.atomic():
                # Si no borramos global, evitamos duplicar borrando los productos previos de este expositor
                # Solo si no es un re-parseo parcial
                if not options['limpiar']:
                    exp.productos.all().delete()

                for item in items:
                    productos_parseados = parsear_item(item)
                    for pdata in productos_parseados:
                        Producto.objects.create(
                            expositor=exp,
                            nombre=pdata['nombre'],
                            categoria=pdata['categoria'],
                            unidad=pdata['unidad'],
                            precio=pdata['precio'],
                            descripcion=pdata['descripcion'],
                            disponible=True,
                        )
                        creados_este += 1
                        resumen_por_categoria[pdata['categoria']] = \
                            resumen_por_categoria.get(pdata['categoria'], 0) + 1

            if creados_este == 0:
                self.stdout.write(self.style.WARNING('   Sin productos parseables'))
                sin_productos.append(exp.nombre_empresa)
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'   {creados_este} productos creados'
                ))
            total_creados += creados_este

        # ============ RESUMEN ============
        self.stdout.write('\n' + '=' * 55)
        self.stdout.write(self.style.SUCCESS(
            f'Total productos creados: {total_creados}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Total en BD: {Producto.objects.count()}'
        ))
        self.stdout.write('=' * 55)

        if resumen_por_categoria:
            self.stdout.write('\nPor categoría:')
            for cat, count in sorted(resumen_por_categoria.items(),
                                     key=lambda x: -x[1]):
                self.stdout.write(f'   {cat}: {count}')

        if sin_productos:
            self.stdout.write(self.style.WARNING(
                f'\nExpositores sin productos ({len(sin_productos)}):'
            ))
            for n in sin_productos:
                self.stdout.write(f'   - {n}')