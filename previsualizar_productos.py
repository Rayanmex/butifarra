"""
Muestra qué cambiaría el script de corrección sin aplicar nada.
Ejecutar con: python previsualizar_productos.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'festivalbutifarra.settings')
django.setup()

from core.models import Producto
from corregir_productos import CORRECCIONES


def mostrar_diferencias():
    print("=" * 80)
    print("  PREVISUALIZACIÓN DE CAMBIOS")
    print("=" * 80)
    print()

    total = 0
    sin_cambios = 0

    for pk, cambios in sorted(CORRECCIONES.items()):
        try:
            p = Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            print(f"⚠️  ID {pk} no existe")
            continue

        diferencias = {}
        for campo, nuevo_valor in cambios.items():
            actual = getattr(p, campo)
            if actual != nuevo_valor:
                diferencias[campo] = (actual, nuevo_valor)

        if not diferencias:
            sin_cambios += 1
            continue

        total += 1
        print(f"ID {pk:3}  [{p.expositor.nombre_empresa}]")
        for campo, (antes, despues) in diferencias.items():
            print(f"    {campo}:")
            print(f"        ANTES:  {antes!r}")
            print(f"        DESPUÉS:{despues!r}")
        print()

    print("=" * 80)
    print(f"  Total a modificar: {total}")
    print(f"  Sin cambios:       {sin_cambios}")
    print("=" * 80)


if __name__ == '__main__':
    mostrar_diferencias()