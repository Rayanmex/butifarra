"""
Asigna fotos de productos a expositores por índice del Excel.

Las fotos están en 'fotos_renombradas/NN-MMM.ext' donde NN es el
índice del expositor (01-31) y MMM es el número de foto.

Uso:
    python manage.py asignar_fotos_por_indice --dry-run
    python manage.py asignar_fotos_por_indice
    python manage.py asignar_fotos_por_indice --limpiar
"""
import re
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Expositor, FotoProducto


class Command(BaseCommand):
    help = "Asigna fotos de productos por índice del Excel (01-001.jpg, ...)"

    def add_arguments(self, parser):
        parser.add_argument('--excel', default='formulario.xlsx')
        parser.add_argument('--fotos-dir', default='fotos_renombradas')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limpiar', action='store_true')

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR)
        excel_path = base / opts['excel']
        fotos_dir = base / opts['fotos_dir']
        dry_run = opts['dry_run']

        if not excel_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ No existe: {excel_path}"))
            return
        if not fotos_dir.exists():
            self.stdout.write(self.style.ERROR(f"❌ No existe: {fotos_dir}"))
            return

        # Leer Excel para mapear índice → nombre de empresa
        self.stdout.write(f"\n📄 Leyendo Excel: {excel_path}")
        df = pd.read_excel(excel_path, header=0, engine='openpyxl')
        df.columns = [str(c).replace('<br>', '\n').strip() for c in df.columns]

        col_empresa = None
        for c in df.columns:
            if c.startswith('Marca o nombre de la empresa'):
                col_empresa = c
                break

        if not col_empresa:
            self.stdout.write(self.style.ERROR("❌ Falta columna de empresa"))
            return

        mapa = {}
        for i, row in df.iterrows():
            empresa = str(row[col_empresa]).strip()
            if empresa and empresa.lower() != 'nan':
                mapa[i + 1] = empresa

        self.stdout.write(f"   {len(mapa)} expositores mapeados")

        # Recolectar fotos
        archivos = []
        for archivo in sorted(fotos_dir.iterdir()):
            if archivo.is_dir() or archivo.name.startswith('.'):
                continue
            if archivo.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                continue
            m = re.match(r'^(\d+)-(\d+)', archivo.stem)
            if m:
                archivos.append((int(m.group(1)), int(m.group(2)), archivo))

        archivos.sort(key=lambda x: (x[0], x[1]))
        self.stdout.write(f"   {len(archivos)} fotos encontradas\n")

        if opts['limpiar'] and not dry_run:
            n, _ = FotoProducto.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"🧹 Borradas {n} fotos previas"))

        asignadas = 0
        errores = 0

        for idx, num, archivo in archivos:
            empresa = mapa.get(idx)
            if not empresa:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️  {archivo.name}: índice {idx} sin empresa"
                ))
                errores += 1
                continue

            exp = Expositor.objects.filter(nombre_empresa=empresa).first()
            if not exp:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️  {archivo.name}: '{empresa}' no existe en BD"
                ))
                errores += 1
                continue

            if dry_run:
                if num <= 2:
                    self.stdout.write(f"   [DRY] {archivo.name}  →  {exp.nombre_empresa}")
                asignadas += 1
                continue

            try:
                foto = FotoProducto(expositor=exp, descripcion=archivo.name[:200])
                with open(archivo, 'rb') as f:
                    foto.imagen.save(archivo.name, File(f), save=True)
                asignadas += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ {archivo.name}: {e}"))
                errores += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Fotos asignadas: {asignadas} | errores: {errores}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  DRY RUN: no se guardó nada."
            ))