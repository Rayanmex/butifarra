"""
Comando Django para importar los datos del 11º Festival de la Butifarra 2026
desde el sitio oficial: https://festivaldelabutifarra.jalpademendez.gob.mx/wp/

Uso:
    python manage.py importar_festival_2026
    python manage.py importar_festival_2026 --url https://otra-url.com
    python manage.py importar_festival_2026 --debug
"""
import re
from datetime import date

from django.core.management.base import BaseCommand

from core.models import (
    Festival,
    HistoriaFestival,
    Artista,
    ProgramaDia,
    FotoGaleria,
    VideoGaleria,
    Patrocinador,
)
from scrapers.festival_2026_scraper import fetch, parse


MESES = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'setiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12,
}


def parsear_fecha(texto):
    """
    Convierte '16 de Octubre de 2026' → datetime.date(2026, 10, 16).
    Devuelve None si no puede.
    """
    if not texto:
        return None
    m = re.match(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", texto, re.IGNORECASE)
    if not m:
        return None
    dia, mes_str, anio = m.groups()
    mes_num = MESES.get(mes_str.lower())
    if not mes_num:
        return None
    try:
        return date(int(anio), mes_num, int(dia))
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Importa los datos del 11º Festival de la Butifarra 2026 desde el sitio oficial"

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            default=None,
            help='URL alternativa (por defecto usa la del scraper)'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Muestra información detallada de lo importado'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Borra todo lo relacionado al festival antes de importar'
        )

    def handle(self, *args, **options):
        url = options.get('url')
        debug = options.get('debug', False)
        limpiar = options.get('limpiar', False)

        # ---------- 1. Obtener HTML ----------
        self.stdout.write(self.style.NOTICE("🌐 Consultando sitio oficial..."))
        try:
            html = fetch(url) if url else fetch()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al obtener HTML: {e}"))
            return

        # ---------- 2. Parsear ----------
        self.stdout.write(self.style.NOTICE("🔍 Parseando contenido..."))
        data = parse(html)

        if debug:
            import json
            self.stdout.write(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
            self.stdout.write("...")

        # ---------- 3. Crear / actualizar Festival ----------
        festival, creado = Festival.objects.update_or_create(
            edicion=11,
            defaults={
                'nombre': 'Festival de la Butifarra',
                'fecha_inicio': date(2026, 10, 16),
                'fecha_fin': date(2026, 10, 18),
                'lugar': 'Parque Recreativo «El Campestre», Jalpa de Méndez, Tabasco',
                'slogan': 'Tradición que se disfruta, orgullo que se comparte',
                'descripcion_corta': data.get('descripcion') or '',
                'facebook_url': data.get('facebook_url') or 'https://www.facebook.com/FestivalDeLaButifarra',
                'instagram_url': data.get('instagram_url') or 'https://www.instagram.com/festivalbutifarra',
                'activo': True,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f"{'✅ Creado' if creado else '♻️  Actualizado'}: {festival}"
        ))

        # ---------- 4. Limpiar si se pidió ----------
        if limpiar:
            self.stdout.write(self.style.WARNING("🧹 Limpiando datos previos..."))
            festival.historia.all().delete()
            festival.artistas.all().delete()
            festival.programa.all().delete()
            festival.galeria_fotos.all().delete()
            festival.galeria_videos.all().delete()
            festival.patrocinadores.all().delete()

        # ---------- 5. Historia ----------
        HistoriaFestival.objects.filter(festival=festival).delete()
        historia_items = data.get('historia', [])
        for i, parrafo in enumerate(historia_items):
            HistoriaFestival.objects.create(
                festival=festival,
                titulo=parrafo[:200],
                parrafo=parrafo,
                orden=i,
            )
        self.stdout.write(f"  📖 Historia: {len(historia_items)} bloques")

        # ---------- 6. Artistas ----------
        Artista.objects.filter(festival=festival).delete()
        artistas_count = 0
        for i, a in enumerate(data.get('artistas', [])):
            nombre = (a.get('nombre') or '').strip()
            if not nombre or len(nombre) > 200:
                continue

            fecha_str = a.get('dia_presentacion_texto') or ''
            dia = parsear_fecha(fecha_str)

            Artista.objects.create(
                festival=festival,
                nombre=nombre[:200],
                cartel_url=a.get('cartel_url') or '',
                dia_presentacion=dia,
                orden=i,
            )
            artistas_count += 1
        self.stdout.write(f"  🎤 Artistas: {artistas_count}")

        # ---------- 7. Programa ----------
        ProgramaDia.objects.filter(festival=festival).delete()
        programa_count = 0
        for i, p in enumerate(data.get('programa', [])):
            dia_num = p.get('dia', 16)
            mes_str = (p.get('mes') or 'octubre').lower()
            mes_num = MESES.get(mes_str, 10)

            try:
                fecha_dia = date(2026, mes_num, int(dia_num))
            except (ValueError, TypeError):
                continue

            ProgramaDia.objects.create(
                festival=festival,
                dia=fecha_dia,
                imagen_url=p.get('imagen_url') or '',
                descripcion=p.get('titulo') or f'{dia_num} DE {mes_str.upper()}',
                orden=i,
            )
            programa_count += 1
        self.stdout.write(f"  📅 Programa: {programa_count} días")

        # ---------- 8. Galería de fotos ----------
        FotoGaleria.objects.filter(festival=festival).delete()
        fotos_count = 0
        for i, url in enumerate(data.get('galeria_fotos', [])):
            if not url:
                continue
            FotoGaleria.objects.create(
                festival=festival,
                imagen_url=url,
                orden=i,
            )
            fotos_count += 1
        self.stdout.write(f"  📸 Galería fotos: {fotos_count}")

        # ---------- 9. Galería de videos ----------
        VideoGaleria.objects.filter(festival=festival).delete()
        videos_count = 0
        for i, v in enumerate(data.get('galeria_videos', [])):
            src = v.get('url')
            if not src:
                continue

            # El primero se considera video oficial
            destacado = (i == 0)
            if destacado:
                titulo = 'Video Oficial del 11º Festival de la Butifarra'
            else:
                # Sacar nombre del archivo como título provisional
                filename = src.split('/')[-1].replace('.mp4', '').replace('-', ' ').replace('_', ' ')
                titulo = f'Entrevista: {filename[:120]}'

            VideoGaleria.objects.create(
                festival=festival,
                titulo=titulo,
                video_url=src,
                poster_url=v.get('poster') or '',
                destacado=destacado,
                orden=i,
            )
            videos_count += 1
        self.stdout.write(f"  🎬 Galería videos: {videos_count}")

        # ---------- 10. Patrocinadores ----------
        Patrocinador.objects.filter(festival=festival).delete()
        patro_count = 0
        for i, url in enumerate(data.get('patrocinadores_logos', [])):
            if not url:
                continue
            Patrocinador.objects.create(
                festival=festival,
                nombre='Patrocinadores oficiales',
                logo_url=url,
                orden=i,
            )
            patro_count += 1
        self.stdout.write(f"  🤝 Patrocinadores: {patro_count}")

        # ---------- 11. Resumen ----------
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS("🎉 Importación completa"))
        self.stdout.write(self.style.SUCCESS(
            f"   {festival.edicion}° {festival.nombre} "
            f"({festival.fecha_inicio} → {festival.fecha_fin})"
        ))