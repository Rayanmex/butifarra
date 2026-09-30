"""
Normaliza nombres, categorías, unidades y precios de productos.
"""
import re


# ============================================================
#  UNIDADES
# ============================================================
UNIDAD_REGEX = [
    (re.compile(r'\b1\s*/\s*2\s*(kilo|kg|k)?\b', re.I), '1/2kg'),
    (re.compile(r'\b½\b|medio\s+kilo|medio\s+kg', re.I), '1/2kg'),
    (re.compile(r'\b1\s*/\s*4\s*(kilo|kg|k)?\b', re.I), '1/4kg'),
    (re.compile(r'\bcuarto\s+(kilo|kg)?\b', re.I), '1/4kg'),
    (re.compile(r'\borden\s+familiar\b', re.I), 'orden_fam'),
    (re.compile(r'\bmedia\s+orden\b', re.I), 'orden_media'),
    (re.compile(r'\borden\s+(individual|personal)\b', re.I), 'orden_ind'),
    (re.compile(r'\b\d*\s*(kilo|kilos|kg|k)\b', re.I), 'kg'),
    (re.compile(r'\borden\b', re.I), 'orden'),
    (re.compile(r'\brebanada\b', re.I), 'rebanada'),
    (re.compile(r'\bpieza|pza\b', re.I), 'pieza'),
    (re.compile(r'\blitro|lt|lts\b', re.I), 'litro'),
    (re.compile(r'\bbote\b', re.I), 'bote'),
    (re.compile(r'\bpaquete|paq\b', re.I), 'paquete'),
]


def detectar_unidad(texto):
    if not texto:
        return 'unidad'
    for regex, unidad in UNIDAD_REGEX:
        if regex.search(texto):
            return unidad
    return 'unidad'


# ============================================================
#  CATEGORÍAS
# ============================================================
KEYWORDS_CATEGORIA = {
    'butifarra_especialidad': [
        'especial', 'pollo', 'pavo', 'camaron', 'camarón', 'jaiba',
        'enjamonada', 'enjamonado', 'picaña', 'picana', 'envinada',
        'rellena', 'queso de hebra',
    ],
    'butifarra_tradicional': ['butifarra', 'butifarras'],
    'queso': ['queso'],
    'longaniza': ['longaniza'],
    'patitas': ['patita', 'patitas', 'cuerito', 'cueritos', 'pezuña', 'pezuñas'],
    'carne': ['carne', 'costilla', 'barbacoa', 'puerco', 'res'],
    'salsa': ['salsa', 'crema', 'aderezo', 'bbq', 'habanero', 'tamarindo',
              'chiltepin', 'chiltepín', 'ajo'],
    'bebida': ['refresco', 'refrescos', 'coca', 'coca-cola', 'coca cola',
               'agua', 'peñafiel', 'penafiel', 'cerveza', 'pozol',
               'jamaica', 'horchata', 'bebida'],
    'postre': ['flan', 'gelatina', 'postre', 'dulce'],
}


def detectar_categoria(texto):
    if not texto:
        return 'otro'
    t = texto.lower()

    # Especialidad primero
    if any(p in t for p in KEYWORDS_CATEGORIA['butifarra_especialidad']):
        if 'butifarra' in t:
            return 'butifarra_especialidad'

    if 'butifarra' in t:
        return 'butifarra_tradicional'

    for cat, palabras in KEYWORDS_CATEGORIA.items():
        if cat.startswith('butifarra'):
            continue
        if any(p in t for p in palabras):
            return cat

    return 'otro'


# ============================================================
#  NOMBRES (limpieza)
# ============================================================

# Correcciones EXACTAS (diccionario, se busca coincidencia completa)
CORRECCIONES_EXACTAS = {
    'refrescos': 'Refrescos',
    'refresco': 'Refresco',
    'coca cola': 'Coca-Cola',
    'coca-cola': 'Coca-Cola',
    'coca cola 3l': 'Coca-Cola 3 L',
    'coca cola 600ml': 'Coca-Cola 600 ml',
    'coca cristal 500ml': 'Coca-Cola 500 ml',
    'peñafiel varios sabores de 600ml': 'Peñafiel 600 ml',
    'peñafiel 600ml': 'Peñafiel 600 ml',
    'peñafiel': 'Peñafiel',
    'agua de jamaica y horchata': 'Agua de Jamaica / Horchata',
    'agua de jamaica': 'Agua de Jamaica',
    'agua de horchata': 'Agua de Horchata',
    'aguas frescas de sabor natural': 'Aguas Frescas',
    'refresco de sabor 2l': 'Refresco 2 L',
    'refresco 2l': 'Refresco 2 L',
    'flan': 'Flan',
    'gelatina': 'Gelatina',
    'queso de puerco': 'Queso de Puerco',
    'longaniza casera': 'Longaniza Casera',
    'longaniza enjamonada': 'Longaniza Enjamonada',
    'patitas curtidas': 'Patitas Curtidas',
    'medio kilo de butifarras': '½ kg Butifarras',
    '1 kilo de butifarras': '1 kg Butifarras',
    '1 kilo de butifarra': '1 kg Butifarra',
    'medio kilo de butifarra': '½ kg Butifarra',
    'orden de frijol y platanos fritos': 'Orden de Frijol con Plátanos Fritos',
    'orden de frijol y plátanos fritos': 'Orden de Frijol con Plátanos Fritos',
    'platanito con butifarra': 'Platanito con Butifarra',
}


# Prefijos de cantidad que deben quitarse del nombre
PREFIJOS_CANTIDAD = [
    (re.compile(r'^1\s*kg?\b', re.I), '1 kg '),
    (re.compile(r'^1\s*kilo\b', re.I), '1 kg '),
    (re.compile(r'^medio\s+(kilo|kg)\b', re.I), '½ kg '),
    (re.compile(r'^1\s*/\s*2\s*(kilo|kg|k)?\b', re.I), '½ kg '),
    (re.compile(r'^½\b', re.I), '½ kg '),
    (re.compile(r'^1\s*/\s*4\s*(kilo|kg|k)?\b', re.I), '¼ kg '),
    (re.compile(r'^1\s*kilo\b', re.I), '1 kg '),
]


def _titulo_inteligente(texto):
    """Pone mayúscula solo en la primera letra de cada palabra significativa."""
    # Palabras que NO deben ir en mayúscula (excepto si son la primera)
    minusculas = {'de', 'del', 'la', 'las', 'el', 'los', 'y', 'con', 'en', 'a', 'al'}
    palabras = texto.split()
    resultado = []
    for i, palabra in enumerate(palabras):
        # Si es un número o unidad, dejar como está
        if palabra.lower() in ('kg', 'ml', 'l', 'lt', 'g'):
            resultado.append(palabra.lower())
            continue
        # Si es un número con unidad, dejar
        if re.match(r'^\d+$', palabra):
            resultado.append(palabra)
            continue
        # Conectores en minúscula (excepto la primera palabra)
        if i > 0 and palabra.lower() in minusculas:
            resultado.append(palabra.lower())
        else:
            resultado.append(palabra.capitalize())
    return ' '.join(resultado)


def limpiar_nombre(nombre):
    """Aplica todas las reglas de limpieza al nombre."""
    if not nombre:
        return nombre

    original = nombre.strip()

    # 1. Correcciones exactas (prioridad alta)
    key = original.lower()
    if key in CORRECCIONES_EXACTAS:
        return CORRECCIONES_EXACTAS[key]

    # 2. Aplicar prefijos de cantidad
    resultado = original
    for regex, reemplazo in PREFIJOS_CANTIDAD:
        if regex.match(resultado):
            resto = regex.sub('', resultado).strip()
            resultado = reemplazo + resto
            break

    # 3. Título inteligente
    resultado = _titulo_inteligente(resultado)

    # 4. Limpiar símbolos y espacios
    resultado = re.sub(r'\s+', ' ', resultado).strip()
    resultado = re.sub(r'\s*,\s*$', '', resultado)  # comas al final
    resultado = re.sub(r'^\s*[-•·]\s*', '', resultado)  # guiones al inicio

    return resultado[:200]


# ============================================================
#  PRECIOS
# ============================================================
def normalizar_precio(valor):
    """Convierte '350', '$350', '350.00' → Decimal('350.00')."""
    if valor is None or valor == '':
        return None
    if isinstance(valor, (int, float)):
        return valor
    # Limpiar texto
    texto = str(valor).replace('$', '').replace(',', '.').strip()
    # Buscar número
    m = re.search(r'(\d+(?:\.\d{1,2})?)', texto)
    if not m:
        return None
    try:
        return float(m.group(1))
    except (ValueError, TypeError):
        return None