"""
Script de diagnóstico del catálogo de expositores.
Ejecutar con: python manage.py shell < diagnostico.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festivalbutifarra.settings')
django.setup()

from collections import Counter
from core.models import Expositor, Producto


def separador(titulo):
    print("\n" + "=" * 70)
    print(f"  {titulo}")
    print("=" * 70)


# =============================================================
#  1. ESTADÍSTICAS GENERALES
# =============================================================
separador("1. ESTADÍSTICAS GENERALES")
print(f"Expositores: {Expositor.objects.count()}")
print(f"Productos:   {Producto.objects.count()}")


# =============================================================
#  2. EXPOSITORES SIN PRODUCTOS
# =============================================================
separador("2. EXPOSITORES SIN PRODUCTOS")
from django.db.models import Count
sin_prod = Expositor.objects.annotate(n=Count('productos')).filter(n=0)
print(f"Total: {sin_prod.count()}\n")
for e in sin_prod:
    tiene_menu = "SÍ" if e.menu_completo else "NO"
    print(f"  - {e.nombre_empresa}")
    print(f"      Menú texto: {tiene_menu}")
    if e.menu_completo:
        print(f"      Contenido: {e.menu_completo[:100]}...")


# =============================================================
#  3. PRODUCTOS CON DESCRIPCIÓN REDUNDANTE
# =============================================================
separador("3. PRODUCTOS CON DESCRIPCIÓN = NOMBRE")
repetidos = []
for p in Producto.objects.all():
    if p.descripcion and p.nombre:
        if p.descripcion.strip().lower() == p.nombre.strip().lower():
            repetidos.append(p)
print(f"Total: {len(repetidos)}\n")
for p in repetidos[:30]:
    print(f"  ID {p.pk}: '{p.nombre}'")
    print(f"      desc: '{p.descripcion}'")


# =============================================================
#  4. PRODUCTOS POR CATEGORÍA
# =============================================================
separador("4. PRODUCTOS POR CATEGORÍA")
cats = Counter(Producto.objects.values_list('categoria', flat=True))
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt}")


# =============================================================
#  5. PRODUCTOS POR UNIDAD
# =============================================================
separador("5. PRODUCTOS POR UNIDAD")
unidades = Counter(Producto.objects.values_list('unidad', flat=True))
for u, cnt in sorted(unidades.items(), key=lambda x: -x[1]):
    print(f"  {u}: {cnt}")


# =============================================================
#  6. PRODUCTOS SIN PRECIO
# =============================================================
separador("6. PRODUCTOS SIN PRECIO")
sin_precio = Producto.objects.filter(precio__isnull=True)
print(f"Total: {sin_precio.count()}\n")
for p in sin_precio[:30]:
    print(f"  ID {p.pk}: '{p.nombre}' (exp: {p.expositor.nombre_empresa})")


# =============================================================
#  7. LISTADO COMPLETO POR EXPOSITOR
# =============================================================
separador("7. PRODUCTOS POR EXPOSITOR")
for e in Expositor.objects.order_by('nombre_empresa'):
    prods = e.productos.all()
    if not prods:
        continue
    print(f"\n▸ {e.nombre_empresa} ({prods.count()} productos)")
    for p in prods:
        precio = f"${p.precio}" if p.precio else "sin precio"
        unidad = p.get_unidad_display() if p.unidad else "?"
        desc = f" | desc: {p.descripcion[:40]}" if p.descripcion else ""
        print(f"    [{p.categoria}] {p.nombre} | {unidad} | {precio}{desc}")