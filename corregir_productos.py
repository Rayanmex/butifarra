"""
Corrige todos los productos: nombres, categorías, unidades y precios.
También agrega los 2 productos que se perdieron en el parseo original.
Ejecutar con: python corregir_productos.py
"""
import os
import shutil
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festivalbutifarra.settings')
django.setup()

from django.db import transaction
from core.models import Producto, Expositor


# =============================================================
#  CORRECCIONES POR ID
# =============================================================

CORRECCIONES = {
    # ========== BUTIFARRAS DON TOÑO ==========
    1: {'nombre': 'Butifarra Tradicional',        'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    2: {'nombre': 'Butifarra Tradicional (½ kg)', 'categoria': 'butifarra_tradicional',  'unidad': '1/2kg',     'precio': 180},
    3: {'nombre': 'Butifarra Enjamonada',         'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},
    4: {'nombre': 'Butifarra Picaña',             'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 550},
    5: {'nombre': 'Orden de Frijol con Plátanos Fritos', 'categoria': 'otro',            'unidad': 'orden',     'precio': 35},
    6: {'nombre': 'Coca-Cola 500 ml',             'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    7: {'nombre': 'Peñafiel 600 ml',              'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    8: {'nombre': 'Agua de Jamaica / Horchata',   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    9: {'nombre': 'Refresco 2 L',                 'categoria': 'bebida',                 'unidad': 'litro',     'precio': 50},

    # ========== AUTOSERVICIO ALAMILLA ==========
    10: {'nombre': 'Butifarra',                   'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 320},
    11: {'nombre': 'Refrescos',                   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 25},
    110:{'nombre': 'Flan',                        'categoria': 'postre',                 'unidad': 'unidad',    'precio': 25},

    # ========== BUTIFARRAS EL SABOR DE JALPA ==========
    12: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 360},
    13: {'nombre': 'Butifarra con Crema de Ajo',  'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 380},
    14: {'nombre': 'Butifarra Envinada Rellena de Queso Provolone', 'categoria': 'butifarra_especialidad', 'unidad': 'kg', 'precio': 400},
    15: {'nombre': 'Queso de Puerco',             'categoria': 'queso',                  'unidad': 'kg',        'precio': 400},

    # ========== BUTIFARRA DON DAGO ==========
    16: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 420},
    17: {'nombre': 'Longaniza Tradicional o Enjamonada (½ kg)', 'categoria': 'longaniza', 'unidad': '1/2kg',   'precio': 135},

    # ========== DOÑA ANITA ==========
    18: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    19: {'nombre': 'Butifarra de Pavo y Pollo',   'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 400},
    20: {'nombre': 'Butifarra Enjamonada Rellena de Queso', 'categoria': 'butifarra_especialidad', 'unidad': 'kg', 'precio': 380},

    # ========== DOÑA PANCHITA ==========
    21: {'nombre': 'Butifarra',                   'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    22: {'nombre': 'Refrescos',                   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    23: {'nombre': 'Patitas Curtidas',            'categoria': 'patitas',                'unidad': 'bote',      'precio': 150},

    # ========== BUTIFARRAS DE SANDY ==========
    24: {'nombre': 'Butifarra',                   'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    25: {'nombre': 'Coca-Cola',                   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 60},

    # ========== LA PALAPA DEL BIÓLOGO ==========
    29: {'nombre': 'Butifarra Tradicional, Ahumada, Adobada o Enchilada', 'categoria': 'butifarra_especialidad', 'unidad': 'kg', 'precio': 360},
    30: {'nombre': 'Butifarra (½ kg)',            'categoria': 'butifarra_tradicional',  'unidad': '1/2kg',     'precio': 180},
    31: {'nombre': 'Butifarra (Pieza)',           'categoria': 'butifarra_tradicional',  'unidad': 'pieza',     'precio': 18},
    32: {'nombre': 'Refresco 600 ml',             'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    33: {'nombre': 'Refresco 3 L',                'categoria': 'bebida',                 'unidad': 'litro',     'precio': 65},

    # ========== BUTIFARRAS MARY ==========
    34: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 400},
    35: {'nombre': 'Butifarra de Pollo',          'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 500},
    36: {'nombre': 'Butifarra de Pavo',           'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 600},
    37: {'nombre': 'Queso de Puerco',             'categoria': 'queso',                  'unidad': 'kg',        'precio': 500},
    38: {'nombre': 'Aguas Frescas',               'categoria': 'bebida',                 'unidad': 'litro',     'precio': 30},

    # ========== LA FLOR DE LA JÍCARA ==========
    39: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 400},
    40: {'nombre': 'Butifarra Especialidad (Limón Pepper, Ajo Parmesano)', 'categoria': 'butifarra_especialidad', 'unidad': 'kg', 'precio': 450},
    41: {'nombre': 'Rebanada de Queso de Puerco', 'categoria': 'queso',                  'unidad': 'rebanada',  'precio': 70},
    42: {'nombre': 'Longaniza Casera',            'categoria': 'longaniza',              'unidad': 'kg',        'precio': 250},

    # ========== DON KARINA ==========
    43: {'nombre': 'Butifarra (1 kg)',            'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 400},
    44: {'nombre': 'Orden de Butifarra',          'categoria': 'butifarra_tradicional',  'unidad': 'orden',     'precio': 100},
    45: {'nombre': 'Butifarra (½ kg)',            'categoria': 'butifarra_tradicional',  'unidad': '1/2kg',     'precio': 200},
    46: {'nombre': 'Bañada en Salsa + Extras',    'categoria': 'salsa',                  'unidad': 'unidad',    'precio': 50},
    47: {'nombre': 'Refrescos',                   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 50},
    48: {'nombre': 'Aguas Naturales',             'categoria': 'bebida',                 'unidad': 'litro',     'precio': 40},
    49: {'nombre': 'Queso de Puerco',             'categoria': 'queso',                  'unidad': 'kg',        'precio': 450},

    # ========== NIÑON JR ==========
    50: {'nombre': 'Orden Familiar de Butifarra Tradicional (21 piezas)', 'categoria': 'butifarra_tradicional', 'unidad': 'orden_fam', 'precio': 350},
    51: {'nombre': 'Media Orden de Butifarra Tradicional (11 piezas)',    'categoria': 'butifarra_tradicional', 'unidad': 'orden_media', 'precio': 180},
    52: {'nombre': 'Orden Individual de Butifarra Tradicional (5 piezas)', 'categoria': 'butifarra_tradicional', 'unidad': 'orden_ind', 'precio': 100},
    53: {'nombre': 'Orden Familiar con Crema de Ajo (21 piezas)',      'categoria': 'butifarra_especialidad', 'unidad': 'orden_fam',   'precio': 410},
    54: {'nombre': 'Media Orden con Crema de Ajo (11 piezas)',         'categoria': 'butifarra_especialidad', 'unidad': 'orden_media', 'precio': 210},
    55: {'nombre': 'Orden Individual con Crema de Ajo (5 piezas)',     'categoria': 'butifarra_especialidad', 'unidad': 'orden_ind',   'precio': 130},
    56: {'nombre': 'Orden Familiar con Salsa de Tamarindo (21 piezas)','categoria': 'butifarra_especialidad', 'unidad': 'orden_fam',   'precio': 410},
    57: {'nombre': 'Media Orden con Salsa de Tamarindo (11 piezas)',   'categoria': 'butifarra_especialidad', 'unidad': 'orden_media', 'precio': 210},
    58: {'nombre': 'Orden Individual con Salsa de Tamarindo (5 piezas)','categoria': 'butifarra_especialidad', 'unidad': 'orden_ind',  'precio': 130},
    59: {'nombre': 'Orden Familiar con Chiltepín (21 piezas)',         'categoria': 'butifarra_especialidad', 'unidad': 'orden_fam',   'precio': 410},
    60: {'nombre': 'Media Orden con Chiltepín (11 piezas)',            'categoria': 'butifarra_especialidad', 'unidad': 'orden_media', 'precio': 210},
    61: {'nombre': 'Orden Individual con Chiltepín (5 piezas)',        'categoria': 'butifarra_especialidad', 'unidad': 'orden_ind',   'precio': 150},

    # ========== D' ROCHER ==========
    62: {'nombre': 'Butifarra Tradicional Cruda (½ kg)',          'categoria': 'butifarra_tradicional', 'unidad': '1/2kg', 'precio': 165},
    63: {'nombre': 'Butifarra Tradicional Cruda (1 kg)',          'categoria': 'butifarra_tradicional', 'unidad': 'kg',    'precio': 320},
    64: {'nombre': 'Butifarra Tradicional Frita (½ kg)',          'categoria': 'butifarra_tradicional', 'unidad': '1/2kg', 'precio': 180},
    65: {'nombre': 'Butifarra Tradicional Frita (1 kg)',          'categoria': 'butifarra_tradicional', 'unidad': 'kg',    'precio': 350},
    66: {'nombre': 'Queso de Puerco Natural (1 kg)',              'categoria': 'queso',                 'unidad': 'kg',    'precio': 380},
    67: {'nombre': 'Queso de Puerco Gourmet (1 kg)',              'categoria': 'queso',                 'unidad': 'kg',    'precio': 420},
    68: {'nombre': 'Longaniza Enjamonada Frita (1 kg)',           'categoria': 'longaniza',             'unidad': 'kg',    'precio': 320},
    69: {'nombre': 'Longaniza Enjamonada Cruda (1 kg)',           'categoria': 'longaniza',             'unidad': 'kg',    'precio': 260},
    70: {'nombre': 'Longaniza Casera Roja Cruda (½ kg)',          'categoria': 'longaniza',             'unidad': '1/2kg', 'precio': 130},
    71: {'nombre': 'Longaniza Casera Roja Cruda (1 kg)',          'categoria': 'longaniza',             'unidad': 'kg',    'precio': 260},
    72: {'nombre': 'Combo: ½ kg Butifarra + ½ kg Longaniza Enjamonada', 'categoria': 'combo',           'unidad': 'paquete', 'precio': 330},
    73: {'nombre': 'Carne Chinameca Cruda (½ kg)',                'categoria': 'carne',                 'unidad': '1/2kg', 'precio': 165},
    74: {'nombre': 'Carne Chinameca Cruda (1 kg)',                'categoria': 'carne',                 'unidad': 'kg',    'precio': 330},
    75: {'nombre': 'Carne Chinameca Frita (½ kg)',                'categoria': 'carne',                 'unidad': '1/2kg', 'precio': 190},
    76: {'nombre': 'Carne Chinameca Frita (1 kg)',                'categoria': 'carne',                 'unidad': 'kg',    'precio': 380},

    # ========== LA GLORIETA DE LA JICARA ==========
    77: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    78: {'nombre': 'Butifarra con Queso',         'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},
    79: {'nombre': 'Butifarra de Pollo',          'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 500},
    80: {'nombre': 'Butifarra de Pavo',           'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 600},
    81: {'nombre': 'Butifarra de Camarón',        'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 750},
    82: {'nombre': 'Butifarra de Jaiba',          'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 500},
    83: {'nombre': 'Queso de Puerco',             'categoria': 'queso',                  'unidad': 'kg',        'precio': 350},
    84: {'nombre': 'Butifarra Tradicional en Salsa de Tamarindo', 'categoria': 'butifarra_especialidad', 'unidad': 'kg', 'precio': 450},
    85: {'nombre': 'Longaniza Casera',            'categoria': 'longaniza',              'unidad': 'kg',        'precio': 250},

    # ========== YOKO ==========
    86: {'nombre': 'Butifarra',                   'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 330},
    87: {'nombre': 'Coca-Cola',                   'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 35},

    # ========== BUTIFARRAS LILI ==========
    88: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    89: {'nombre': 'Butifarra de Pollo',          'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 400},
    90: {'nombre': 'Butifarra de Pavo',           'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},

    # ========== MARCO ANTONIO ==========
    91: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    92: {'nombre': 'Butifarra de Especialidad',   'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},
    93: {'nombre': 'Longaniza Casera',            'categoria': 'longaniza',              'unidad': 'kg',        'precio': 250},
    94: {'nombre': 'Queso de Puerco',             'categoria': 'queso',                  'unidad': 'kg',        'precio': 500},
    95: {'nombre': 'Salsa BBQ / Mango Habanero (¼ kg)', 'categoria': 'salsa',            'unidad': '1/4kg',     'precio': 100},

    # ========== BUTIFARRASLUPITA ==========
    96: {'nombre': 'Butifarra Tradicional',       'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 350},
    97: {'nombre': 'Butifarra de Especialidad',   'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 400},
    98: {'nombre': 'Rebanada de Queso de Puerco', 'categoria': 'queso',                  'unidad': 'rebanada',  'precio': 70},
    99: {'nombre': 'Longaniza Casera',            'categoria': 'longaniza',              'unidad': 'kg',        'precio': 250},

    # ========== TANY JR ==========
    100: {'nombre': 'Butifarra Tradicional',      'categoria': 'butifarra_tradicional',  'unidad': 'kg',        'precio': 340},
    101: {'nombre': 'Butifarra con Aderezo BBQ',  'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 380},
    102: {'nombre': 'Butifarra con Pasitas',      'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},
    103: {'nombre': 'Butifarra Enjamonada',       'categoria': 'butifarra_especialidad', 'unidad': 'kg',        'precio': 450},
    104: {'nombre': 'Queso de Puerco',            'categoria': 'queso',                  'unidad': 'kg',        'precio': 450},
    105: {'nombre': 'Longaniza Casera',           'categoria': 'longaniza',              'unidad': 'kg',        'precio': 250},
    106: {'nombre': 'Longaniza Enjamonada',       'categoria': 'longaniza',              'unidad': 'kg',        'precio': 300},
    107: {'nombre': 'Coca-Cola 3 L',              'categoria': 'bebida',                 'unidad': 'litro',     'precio': 58},
    108: {'nombre': 'Coca-Cola 600 ml',           'categoria': 'bebida',                 'unidad': 'unidad',    'precio': 30},
    109: {'nombre': 'Aguas Frescas',              'categoria': 'bebida',                 'unidad': 'litro',     'precio': 30},
}


# =============================================================
#  PRODUCTOS EXTRA A AGREGAR (recuperados del parseo original)
# =============================================================

PRODUCTOS_EXTRA = [
    {
        'expositor_match': 'Flor de la Jícara',
        'nombre': 'Patitas Curtidas',
        'categoria': 'patitas',
        'unidad': 'bote',
        'precio': 130,
    },
    {
        'expositor_match': 'Butifarraslupita',
        'nombre': 'Queso de Puerco (1 kg)',
        'categoria': 'queso',
        'unidad': 'kg',
        'precio': 450,
    },
]


# =============================================================
#  HELPERS
# =============================================================

def backup_db():
    if not os.path.exists('db.sqlite3'):
        print("⚠️  No se encontró db.sqlite3")
        return
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    destino = f'db.sqlite3.bak_{ts}'
    shutil.copy2('db.sqlite3', destino)
    print(f"💾 Backup: {destino}")


def aplicar_correcciones(correcciones):
    actualizados = 0
    errores = 0
    for pk, cambios in correcciones.items():
        try:
            p = Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            print(f"  ⚠️  ID {pk} no existe")
            errores += 1
            continue
        modificado = False
        for campo, valor in cambios.items():
            if getattr(p, campo) != valor:
                setattr(p, campo, valor)
                modificado = True
        if modificado:
            p.save()
            actualizados += 1
    return actualizados, errores


def arreglar_don_julian():
    """Los productos 26, 27 y 28 (don Julián) están rotos. Los reconstruimos."""
    ids_rotos = [26, 27, 28]
    productos = Producto.objects.filter(pk__in=ids_rotos)
    if not productos.exists():
        return 0

    expositor = productos.first().expositor
    productos.delete()

    Producto.objects.create(
        expositor=expositor, nombre='Butifarra Tradicional (1 kg)',
        categoria='butifarra_tradicional', unidad='kg', precio=400, disponible=True,
    )
    Producto.objects.create(
        expositor=expositor, nombre='Butifarra Tradicional (½ kg)',
        categoria='butifarra_tradicional', unidad='1/2kg', precio=200, disponible=True,
    )
    Producto.objects.create(
        expositor=expositor, nombre='Orden de Butifarra',
        categoria='butifarra_tradicional', unidad='orden', precio=100, disponible=True,
    )
    return 3


def agregar_productos_extra(productos_extra):
    """Agrega los 2 productos que se perdieron en el parseo."""
    creados = 0
    for datos in productos_extra:
        expositor = Expositor.objects.filter(
            nombre_empresa__icontains=datos['expositor_match']
        ).first()

        if not expositor:
            print(f"  ⚠️  No se encontró expositor para '{datos['expositor_match']}'")
            continue

        # Verificar que no exista ya
        ya_existe = Producto.objects.filter(
            expositor=expositor,
            nombre=datos['nombre'],
        ).exists()

        if ya_existe:
            print(f"  ℹ️  Ya existe: {datos['nombre']} en {expositor.nombre_empresa}")
            continue

        Producto.objects.create(
            expositor=expositor,
            nombre=datos['nombre'],
            categoria=datos['categoria'],
            unidad=datos['unidad'],
            precio=datos['precio'],
            disponible=True,
        )
        print(f"  ✅ Creado: {datos['nombre']} en {expositor.nombre_empresa}")
        creados += 1

    return creados


def limpiar_descripciones():
    return Producto.objects.exclude(descripcion='').exclude(descripcion__isnull=True).update(descripcion='')


# =============================================================
#  MAIN
# =============================================================

def main():
    print("=" * 70)
    print("  CORRECCIÓN DE PRODUCTOS — Festival de la Butifarra")
    print("=" * 70)
    print()

    backup_db()
    print()

    print(f"📊 Estado actual:")
    print(f"   Productos totales: {Producto.objects.count()}")
    print(f"   Expositores:       {Expositor.objects.count()}")
    print()

    print("🔍 Análisis de cambios:")
    print(f"   Correcciones por ID:  {len(CORRECCIONES)}")
    print(f"   Productos de don Julián a reconstruir: 3")
    print(f"   Productos extra a agregar: {len(PRODUCTOS_EXTRA)}")
    print()

    print("⚠️  ¿Aplicar? (s/N): ", end='')
    respuesta = input().strip().lower()

    if respuesta != 's':
        print("❌ Cancelado.")
        return

    print()
    print("🚀 Aplicando cambios...")

    with transaction.atomic():
        # 1. Correcciones por ID
        actualizados, errores = aplicar_correcciones(CORRECCIONES)
        print(f"   ✅ {actualizados} productos actualizados ({errores} errores)")

        # 2. Don Julián
        creados_julian = arreglar_don_julian()
        print(f"   ✅ {creados_julian} productos de don Julián recreados")

        # 3. Limpiar descripciones ANTES de agregar extras
        desc_borradas = limpiar_descripciones()
        print(f"   ✅ {desc_borradas} descripciones limpiadas")

        # 4. Productos extra
        print(f"   Agregando productos extra:")
        creados_extra = agregar_productos_extra(PRODUCTOS_EXTRA)

    print()
    print("=" * 70)
    print("  ✅ CORRECCIONES APLICADAS")
    print("=" * 70)
    print()

    print(f"📊 Estado final:")
    print(f"   Productos totales: {Producto.objects.count()}")
    print()

    from collections import Counter
    print("📂 Distribución por categoría:")
    cats = Counter(Producto.objects.values_list('categoria', flat=True))
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {cnt}")

    print()
    print("🎉 Listo. Verifica en /panel/expositores/")


if __name__ == '__main__':
    main()