"""
Comando: python manage.py asignar_imagenes
Asigna logos y fotos locales a los expositores ya cargados.
Los archivos se identifican por el nombre que aparece después del último ' - '.
"""
import os
import re
import unicodedata
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Expositor, FotoProducto


# Rutas de las carpetas
DIR_FOTOS = Path('Fotos_productos')
DIR_LOGOS = Path('Logo_marca')

# Extensiones válidas
EXTS_IMG = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Mapa de nombres en archivo -> nombre_empresa en BD
# Basado en tu Excel + inspección de archivos
MAPA_NOMBRES = {
    'juan antonio ribera': 'Butifarras Lili',
    'sebastian lopez': 'Tany Jr.',
    'gerardo madrigal': 'La Glorieta de la Jicara',
    'sandibel taracena': 'Butifarras de Sandy',
    'marco antonio magaña': 'Butifarras Marco Antonio',
    'maria jimenez': 'Yoko ixikob xalpan',
    'guadalupe ricardez': 'Butifarras Lupita',
    'maria magaña lopez': 'Butifarras mary',
    'juan carlos dominguez': 'Butifarras la Palapa del Biólogo',
    'poncho rocher': "D' Rocher",
    'niñon jr': 'Centro Botanero Niñon Jr',
    'eduardo castillo': 'Butifarras y barbacoa don karina',
    'rocio guadalupe madrigal': 'Butifarras y Embutidos la Flor de la Jícara',
    'iris jimenez': 'Butifarras Don Toño',
    'ana garcía': 'Butifarras Doña Anita',
    'francisca perez': 'Butifarras Doña Panchita',
    'teresa garcía': 'Butifarra Don Dago',
    'julio cesar alamilla': 'Autoservicio Alamilla',
    'luis almeida': 'BUTIFARRAS EL SABOR DE JALPA',
    'beto lopez': None,      # no identificado
    'butifarras don julian': 'Butifarras don Julián',
    'yuliana mañana': 'Butifarras don Julián',
}


def normalizar(texto):
    """Quita acentos, deja minúsculas, quita espacios extra."""
    if not texto:
        return ''
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def extraer_remitente(nombre_archivo):
    """Extrae el nombre después del último ' - ' del archivo."""
    base = Path(nombre_archivo).stem
    # Buscar patrón '... - nombre'
    if ' - ' in base:
        return normalizar(base.rsplit(' - ', 1)[-1].rstrip('_0123456789 '))
    return ''


def buscar_expositor(remitente):
    """Busca el expositor correspondiente al remitente."""
    if not remitente:
        return None
    # Buscar en el mapa
    for key, empresa in MAPA_NOMBRES.items():
        if key in remitente or remitente in key:
            if not empresa:
                return None
            # Buscar por nombre_empresa (case-insensitive)
            try:
                return Expositor.objects.get(nombre_empresa__iexact=empresa)
            except Expositor.DoesNotExist:
                # Intentar por aproximación
                return Expositor.objects.filter(nombre_empresa__icontains=empresa.split()[0]).first()
            except Expositor.MultipleObjectsReturned:
                return Expositor.objects.filter(nombre_empresa__iexact=empresa).first()
    return None


class Command(BaseCommand):
    help = 'Asigna logos y fotos locales a los expositores'

    def add_arguments(self, parser):
        parser.add_argument('--solo-fotos', action='store_true', help='Solo asignar fotos')
        parser.add_argument('--solo-logos', action='store_true', help='Solo asignar logos')
        parser.add_argument('--limpiar', action='store_true',
                            help='Borrar fotos existentes antes de asignar')

    def handle(self, *args, **options):
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('Borrando fotos existentes...'))
            FotoProducto.objects.all().delete()

        hacer_fotos = not options['solo_logos']
        hacer_logos = not options['solo_fotos']

        if hacer_logos:
            self.asignar_logos()
        if hacer_fotos:
            self.asignar_fotos()

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Expositores: {Expositor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Fotos totales: {FotoProducto.objects.count()}'))
        self.stdout.write('=' * 50)

    def asignar_logos(self):
        self.stdout.write('\n--- LOGOS ---\n')
        if not DIR_LOGOS.exists():
            self.stdout.write(self.style.ERROR(f'No existe {DIR_LOGOS}'))
            return

        asignados = 0
        no_id = []

        for archivo in sorted(DIR_LOGOS.iterdir()):
            if archivo.suffix.lower() not in EXTS_IMG:
                continue

            remitente = extraer_remitente(archivo.name)
            exp = buscar_expositor(remitente)

            if not exp:
                no_id.append(archivo.name)
                self.stdout.write(self.style.WARNING(f'[?] {archivo.name}'))
                continue

            # Guardar logo
            with open(archivo, 'rb') as f:
                nombre = f"{slugify(exp.nombre_empresa)}_logo{archivo.suffix}"
                exp.logo.save(nombre, File(f), save=True)
            asignados += 1
            self.stdout.write(self.style.SUCCESS(f'[✓] {archivo.name} -> {exp.nombre_empresa}'))

        self.stdout.write(f'\nLogos asignados: {asignados}')
        if no_id:
            self.stdout.write(self.style.WARNING(f'Sin identificar ({len(no_id)}):'))
            for n in no_id:
                self.stdout.write(f'   - {n}')

    def asignar_fotos(self):
        self.stdout.write('\n--- FOTOS ---\n')
        if not DIR_FOTOS.exists():
            self.stdout.write(self.style.ERROR(f'No existe {DIR_FOTOS}'))
            return

        # Agrupar por expositor
        por_expositor = {}
        no_id = []

        for archivo in sorted(DIR_FOTOS.iterdir()):
            if archivo.suffix.lower() not in EXTS_IMG:
                continue

            remitente = extraer_remitente(archivo.name)
            exp = buscar_expositor(remitente)

            if not exp:
                no_id.append(archivo.name)
                continue

            por_expositor.setdefault(exp, []).append(archivo)

        # Crear fotos
        total = 0
        for exp, archivos in por_expositor.items():
            # Contar fotos existentes para numerar sin duplicar
            inicio = exp.fotos.count()
            for idx, archivo in enumerate(archivos, start=1):
                num = inicio + idx
                with open(archivo, 'rb') as f:
                    nombre = f"{slugify(exp.nombre_empresa)}_foto{num}{archivo.suffix}"
                    FotoProducto.objects.create(
                        expositor=exp,
                        imagen=File(f, name=nombre),
                        descripcion=f"Foto {num}"
                    )
                total += 1
            self.stdout.write(self.style.SUCCESS(
                f'[✓] {exp.nombre_empresa}: +{len(archivos)} fotos'
            ))

        self.stdout.write(f'\nFotos creadas: {total}')
        if no_id:
            self.stdout.write(self.style.WARNING(f'Sin identificar ({len(no_id)}):'))
            for n in no_id:
                self.stdout.write(f'   - {n}')