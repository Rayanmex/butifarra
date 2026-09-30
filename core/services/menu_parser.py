"""
Convierte el campo `menu_completo` (texto libre) en registros `Producto`.
"""
import re
from decimal import Decimal, InvalidOperation
from core.models import Producto


KEYWORDS_CATEGORIA = {
    'butifarra_tradicional': ['tradicional', 'normal', 'clásica', 'clasica'],
    'butifarra_especialidad': ['especial', 'pollo', 'pavo', 'camarón', 'camaron',
                                'jaiba', 'enjamonada', 'picaña', 'picana',
                                'envinada', 'rellena'],
    'queso': ['queso de puerco', 'queso'],
    'longaniza': ['longaniza'],
    'carne': ['carne', 'costilla', 'puerco', 'res', 'barbacoa'],
    'patitas': ['patita', 'patitas', 'cueritos', 'pezuñas', 'pezuñas'],
    'salsa': ['salsa', 'aderezo', 'crema de ajo', 'bbq', 'habanero',
              'tamarindo', 'chiltepín', 'chiltepin'],
    'bebida': ['refresco', 'coca', 'agua', 'peñafiel', 'penafiel',
                'jamaica', 'horchata', 'cerveza', 'pozol'],
    'postre': ['postre', 'flan', 'gelatina', 'dulce'],
    'combo': ['combo', 'paquete', 'familiar', 'orden familiar'],
}

KEYWORDS_UNIDAD = [
    (['1/2 kilo', 'medio kilo', '½', '1/2kg', 'medio kg'], '1/2kg'),
    (['1/4 kilo', 'cuarto kilo', '1/4kg', 'cuarto'], '1/4kg'),
    (['kilo', 'kg', '1k', '1 k'], 'kg'),
    (['orden familiar', 'ord familiar', 'ord. familiar'], 'orden_fam'),
    (['media orden'], 'orden_media'),
    (['orden individual', 'orden personal', 'ord individual'], 'orden_ind'),
    (['orden', 'ord'], 'orden'),
    (['rebanada', 'rebanad'], 'rebanada'),
    (['pieza', 'pza'], 'pieza'),
    (['litro', 'lt', 'lts'], 'litro'),
    (['bote'], 'bote'),
    (['paquete', 'paq'], 'paquete'),
]

RE_PRECIO = re.compile(r'\$\s*(\d+(?:[.,]\d{1,2})?)', re.IGNORECASE)
RE_PRECIO_SIN = re.compile(r'(?:^|\s)(\d{2,5})(?:\s|$|,|\.)')


def _detectar_categoria(texto):
    t = texto.lower()
    for cat, palabras in KEYWORDS_CATEGORIA.items():
        if any(p in t for p in palabras):
            return cat
    return 'otro'


def _detectar_unidad(texto):
    t = texto.lower()
    for palabras, unidad in KEYWORDS_UNIDAD:
        if any(p in t for p in palabras):
            return unidad
    return 'unidad'


def _extraer_precio(texto):
    m = RE_PRECIO.search(texto)
    if m:
        try:
            return Decimal(m.group(1).replace(',', '.'))
        except InvalidOperation:
            pass
    # Fallback: cualquier número entre 10 y 9999
    m = RE_PRECIO_SIN.search(texto)
    if m:
        try:
            n = Decimal(m.group(1))
            if 10 <= n <= 9999:
                return n
        except InvalidOperation:
            pass
    return None


def parse_linea(linea):
    """Convierte una línea del menú en dict de producto."""
    linea = linea.strip(' -•\t\n\r')
    if not linea or len(linea) < 3:
        return None

    precio = _extraer_precio(linea)

    # Nombre: quitar el precio y símbolos
    nombre = RE_PRECIO.sub('', linea)
    nombre = RE_PRECIO_SIN.sub(' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip(' -:,.')
    if not nombre or len(nombre) < 2:
        return None

    return {
        'nombre': nombre[:200],
        'categoria': _detectar_categoria(linea),
        'unidad': _detectar_unidad(linea),
        'precio': precio,
        'descripcion': linea[:300],
    }


def parse_menu_completo(expositor):
    """Devuelve la lista de productos detectados en el menú."""
    items = []
    for linea in expositor.get_menu_list():
        data = parse_linea(linea)
        if data and (data['nombre'] or data['precio']):
            items.append(data)
    return items


def importar_productos_desde_menu(expositor, reemplazar=True):
    """Crea los Productos a partir del menú textual."""
    if reemplazar:
        expositor.productos.all().delete()

    creados = []
    for data in parse_menu_completo(expositor):
        creados.append(Producto.objects.create(expositor=expositor, **data))

    expositor.recalcular_precio_desde()
    return creados