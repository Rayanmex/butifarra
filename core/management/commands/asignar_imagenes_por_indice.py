"""
Asigna logos a expositores por ÍNDICE del Excel.

Los archivos de logos/ están renombrados como 01.jpg, 02.jpg, ...,
donde el número coincide con la posición de la fila del Excel.

Uso:
    python manage.py asignar_logos_por_indice --dry-run
    python manage.py asignar_logos_por_indice
"""
import re
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Expositor


class Command(BaseCommand):
    help = "Asigna logos por índice del Excel (archivos 01.jpg, 02.jpg, ...)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--excel',
            default='formulario.xlsx',
            help='Ruta al Excel (default: formulario.xlsx)'
        )
        parser.add_argument(
            '--logos-dir',
            default='logos',
            help='Carpeta con los logos (default: logos)'
        )
        parser.add_argument(
            '--offset',
            type=int,
            default=0,
            help='Offset entre índice de archivo y fila del Excel. '
                 'Si el archivo 01.jpg corresponde a la fila 2 del Excel '
                 '(porque la fila 1 son encabezados), offset=0. '
                 'Si el archivo 01.jpg corresponde a la fila 1, offset=-1.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que haría sin guardar nada'
        )
        parser.add_argument(
            '--sobrescribir',
            action='store_true',
            help='Reemplaza el logo aunque el expositor ya tenga uno'
        )

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR)
        excel_path = base / opts['excel']
        logos_dir = base / opts['logos_dir']
        offset = opts['offset']
        dry_run = opts['dry_run']
        sobrescribir = opts['sobrescribir']

        if not excel_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ No existe el Excel: {excel_path}"))
            return
        if not logos_dir.exists():
            self.stdout.write(self.style.ERROR(f"❌ No existe la carpeta: {logos_dir}"))
            return

        # ---------- Leer Excel ----------
        self.stdout.write(f"\n📄 Leyendo Excel: {excel_path}")
        df = pd.read_excel(excel_path, header=0, engine='openpyxl')
        df.columns = [str(c).replace('<br>', '\n').strip() for c in df.columns]

        # Encontrar columna de nombre de empresa
        col_empresa = None
        for c in df.columns:
            if c.startswith('Marca o nombre de la empresa'):
                col_empresa = c
                break

        if not col_empresa:
            self.stdout.write(self.style.ERROR("❌ No encontré la columna 'Marca o nombre de la empresa'"))
            return

        self.stdout.write(f"   {len(df)} filas leídas")

        # ---------- Recolectar archivos ordenados ----------
        archivos = []
        for archivo in sorted(logos_dir.iterdir()):
            if archivo.is_dir() or archivo.name.startswith('.'):
                continue
            if archivo.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                continue
            # Extraer el número del nombre (01.jpg → 1)
            m = re.match(r'^(\d+)', archivo.stem)
            if m:
                num = int(m.group(1))
                archivos.append((num, archivo))

        archivos.sort(key=lambda x: x[0])
        self.stdout.write(f"   {len(archivos)} archivos de logo encontrados\n")

        # ---------- Asignar por índice ----------
        asignados, sin_match, ya_tenian, errores = 0, 0, 0, 0

        for num, archivo in archivos:
            # El archivo con número N corresponde a la fila N+offset del Excel
            # Si offset=0 → archivo 01 → fila 0 (primera fila de datos)
            # Si offset=-1 → archivo 01 → fila -1 (inválido, no aplica)
            idx_excel = num - 1 + offset

            if idx_excel < 0 or idx_excel >= len(df):
                self.stdout.write(
                    self.style.WARNING(
                        f"   ⚠️  {archivo.name}: índice {idx_excel} fuera de rango"
                    )
                )
                sin_match += 1
                continue

            nombre_empresa = str(df.iloc[idx_excel][col_empresa]).strip()
            if not nombre_empresa or nombre_empresa.lower() == 'nan':
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  {archivo.name}: fila {idx_excel} sin nombre")
                )
                sin_match += 1
                continue

            # Buscar el expositor en la BD
            exp = Expositor.objects.filter(nombre_empresa=nombre_empresa).first()
            if not exp:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  {archivo.name}: no existe '{nombre_empresa}' en BD")
                )
                sin_match += 1
                continue

            if exp.logo and not sobrescribir:
                self.stdout.write(f"   ⏭️  {archivo.name}: {exp.nombre_empresa} ya tiene logo")
                ya_tenian += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"   [DRY] {archivo.name}  →  {exp.nombre_empresa}"
                )
                asignados += 1
                continue

            try:
                with open(archivo, 'rb') as f:
                    exp.logo.save(archivo.name, File(f), save=True)
                self.stdout.write(
                    self.style.SUCCESS(f"   ✔ {archivo.name}  →  {exp.nombre_empresa}")
                )
                asignados += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ {archivo.name}: {e}"))
                errores += 1

        # ---------- Resumen ----------
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Logos asignados: {asignados} | "
            f"ya tenían: {ya_tenian} | "
            f"sin match: {sin_match} | "
            f"errores: {errores}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  DRY RUN: no se guardó nada. Quita --dry-run para aplicar cambios."
            ))