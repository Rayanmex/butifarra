from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Min

from .models import (
    # Expositores
    Expositor,
    FotoProducto,
    Producto,
    # Festival
    Festival,
    HistoriaFestival,
    Artista,
    ProgramaDia,
    FotoGaleria,
    VideoGaleria,
    Patrocinador,
)


# =============================================================
#  EXPOSITORES
# =============================================================

class FotoProductoInline(admin.TabularInline):
    model = FotoProducto
    extra = 1
    fields = ('imagen', 'descripcion')
    verbose_name = "Foto"
    verbose_name_plural = "Fotos de productos"


class ProductoInline(admin.TabularInline):
    model = Producto
    extra = 0
    fields = ('nombre', 'categoria', 'unidad', 'precio', 'disponible')
    show_change_link = True


@admin.register(Expositor)
class ExpositorAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_empresa',
        'nombre_expositor',
        'categoria',
        'numero_stand',
        'precio_desde_display',
        'acepta_tarjeta',
        'es_destacado',
        'activo',
        'fecha_registro',
    )
    list_display_links = ('nombre_empresa',)
    list_filter = (
        'categoria',
        'acepta_tarjeta',
        'acepta_efectivo',
        'es_destacado',
        'activo',
        'fecha_registro',
    )
    search_fields = (
        'nombre_empresa',
        'nombre_expositor',
        'email_contacto',
        'numero_contacto',
        'especialidades',
        'descripcion',
    )
    list_editable = ('numero_stand', 'es_destacado', 'activo')
    readonly_fields = ('fecha_registro', 'precio_desde', 'logo_preview')
    date_hierarchy = 'fecha_registro'
    list_per_page = 25
    save_on_top = True
    inlines = [ProductoInline, FotoProductoInline]
    actions = ['marcar_destacado', 'quitar_destacado', 'activar', 'desactivar', 'recalcular_precio']

    fieldsets = (
        ('Información básica', {
            'fields': (
                'nombre_expositor',
                'nombre_empresa',
                'categoria',
                'descripcion',
                'logo',
                'logo_preview',
            )
        }),
        ('Contacto', {
            'fields': (
                'email_contacto',
                'numero_contacto',
                'enlace_red_social_1',
                'enlace_red_social_2',
                'redes_sociales_texto',
            )
        }),
        ('Ubicación del negocio', {
            'fields': (
                'direccion_negocio',
                'link_google_maps',
            )
        }),
        ('Festival', {
            'fields': (
                'numero_stand',
                'acepta_tarjeta',
                'acepta_efectivo',
                'precio_desde',
                'es_destacado',
                'activo',
            )
        }),
        ('Menú', {
            'fields': ('menu_completo',),
            'description': 'Un producto por línea. Ejemplo: "1 kilo de butifarra tradicional - $350"'
        }),
        ('Administración', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Logo')
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 80px; border-radius: 6px;" />',
                obj.logo.url
            )
        return "—"

    @admin.display(description='Precio desde', ordering='precio_desde')
    def precio_desde_display(self, obj):
        if obj.precio_desde:
            return f"${obj.precio_desde:,.0f}"
        return "—"

    @admin.action(description='⭐ Marcar como destacado')
    def marcar_destacado(self, request, queryset):
        n = queryset.update(es_destacado=True)
        self.message_user(request, f"{n} expositor(es) marcados como destacados.")

    @admin.action(description='☆ Quitar de destacados')
    def quitar_destacado(self, request, queryset):
        n = queryset.update(es_destacado=False)
        self.message_user(request, f"{n} expositor(es) ya no son destacados.")

    @admin.action(description='✅ Activar')
    def activar(self, request, queryset):
        n = queryset.update(activo=True)
        self.message_user(request, f"{n} expositor(es) activados.")

    @admin.action(description='🚫 Desactivar')
    def desactivar(self, request, queryset):
        n = queryset.update(activo=False)
        self.message_user(request, f"{n} expositor(es) desactivados.")

    @admin.action(description='🔄 Recalcular precio mínimo')
    def recalcular_precio(self, request, queryset):
        for exp in queryset:
            exp.recalcular_precio_desde()
        self.message_user(request, f"Precio recalculado para {queryset.count()} expositor(es).")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'expositor',
        'categoria',
        'unidad',
        'precio_display',
        'disponible',
    )
    list_display_links = ('nombre',)
    list_filter = ('categoria', 'unidad', 'disponible', 'expositor__categoria')
    search_fields = ('nombre', 'descripcion', 'expositor__nombre_empresa')
    list_editable = ('disponible',)  # ← quitamos 'precio' porque 'precio_display' no es el campo real
    autocomplete_fields = ['expositor']
    list_per_page = 50
    save_on_top = True

    @admin.display(description='Precio', ordering='precio')
    def precio_display(self, obj):
        return obj.get_precio_display()


@admin.register(FotoProducto)
class FotoProductoAdmin(admin.ModelAdmin):
    list_display = ('expositor', 'descripcion', 'fecha_subida', 'imagen_preview')
    list_filter = ('expositor', 'fecha_subida')
    search_fields = ('expositor__nombre_empresa', 'descripcion')
    readonly_fields = ('fecha_subida', 'imagen_preview')
    list_per_page = 50

    @admin.display(description='Vista previa')
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.imagen.url
            )
        return "—"


# =============================================================
#  FESTIVAL
# =============================================================

class HistoriaFestivalInline(admin.TabularInline):
    model = HistoriaFestival
    extra = 1
    fields = ('orden', 'titulo', 'parrafo')


class ArtistaInline(admin.TabularInline):
    model = Artista
    extra = 1
    fields = ('orden', 'nombre', 'dia_presentacion', 'cartel_url', 'descripcion')
    ordering = ('orden',)


class ProgramaDiaInline(admin.TabularInline):
    model = ProgramaDia
    extra = 0
    fields = ('orden', 'dia', 'descripcion', 'imagen_url')
    ordering = ('orden', 'dia')


class FotoGaleriaInline(admin.TabularInline):
    model = FotoGaleria
    extra = 0
    fields = ('orden', 'imagen_url', 'descripcion')
    ordering = ('orden',)


class VideoGaleriaInline(admin.TabularInline):
    model = VideoGaleria
    extra = 0
    fields = ('orden', 'titulo', 'video_url', 'destacado')
    ordering = ('-destacado', 'orden')


class PatrocinadorInline(admin.TabularInline):
    model = Patrocinador
    extra = 0
    fields = ('orden', 'nombre', 'logo_url')
    ordering = ('orden',)


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = (
        'edicion',
        'nombre',
        'fecha_inicio',
        'fecha_fin',
        'dias_duracion',
        'lugar',
        'activo',
    )
    list_filter = ('activo', 'fecha_inicio')
    search_fields = ('nombre', 'lugar', 'slogan', 'descripcion_corta')
    list_editable = ('activo',)
    readonly_fields = ('dias_duracion', 'estadisticas')
    save_on_top = True

    fieldsets = (
        ('Información principal', {
            'fields': (
                'nombre',
                'edicion',
                'slogan',
                'descripcion_corta',
                'logo',
            )
        }),
        ('Fechas y lugar', {
            'fields': (
                'fecha_inicio',
                'fecha_fin',
                'dias_duracion',
                'lugar',
            )
        }),
        ('Redes sociales', {
            'fields': (
                'facebook_url',
                'instagram_url',
            )
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Estadísticas', {
            'fields': ('estadisticas',),
            'classes': ('collapse',),
        }),
    )

    inlines = [
        HistoriaFestivalInline,
        ArtistaInline,
        ProgramaDiaInline,
        FotoGaleriaInline,
        VideoGaleriaInline,
        PatrocinadorInline,
    ]

    @admin.display(description='Días')
    def dias_duracion(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            delta = (obj.fecha_fin - obj.fecha_inicio).days + 1
            return f"{delta} días"
        return "—"

    @admin.display(description='Estadísticas')
    def estadisticas(self, obj):
        if not obj.pk:
            return "Guarda primero el festival para ver estadísticas."
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Artistas:</strong> {}<br>'
            '<strong>Días de programa:</strong> {}<br>'
            '<strong>Fotos en galería:</strong> {}<br>'
            '<strong>Videos en galería:</strong> {}<br>'
            '<strong>Patrocinadores:</strong> {}<br>'
            '<strong>Bloques de historia:</strong> {}'
            '</div>',
            obj.artistas.count(),
            obj.programa.count(),
            obj.galeria_fotos.count(),
            obj.galeria_videos.count(),
            obj.patrocinadores.count(),
            obj.historia.count(),
        )


@admin.register(HistoriaFestival)
class HistoriaFestivalAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'orden', 'festival')
    list_display_links = ('titulo_corto',)
    list_filter = ('festival',)
    search_fields = ('titulo', 'parrafo')
    list_editable = ('orden',)
    autocomplete_fields = ['festival']
    list_per_page = 50

    @admin.display(description='Título')
    def titulo_corto(self, obj):
        return obj.titulo[:80] + ('…' if len(obj.titulo) > 80 else '')


@admin.register(Artista)
class ArtistaAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'dia_presentacion',
        'festival',
        'orden',
        'imagen_preview',
    )
    list_display_links = ('nombre',)
    list_filter = ('festival', 'dia_presentacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('orden',)
    autocomplete_fields = ['festival']
    readonly_fields = ('imagen_preview',)
    list_per_page = 50
    save_on_top = True

    fields = (
        'festival',
        'nombre',
        'dia_presentacion',
        'descripcion',
        'cartel_url',
        'imagen_local',
        'imagen_preview',
        'orden',
    )

    @admin.display(description='Cartel')
    def imagen_preview(self, obj):
        url = obj.imagen_url
        if url:
            return format_html(
                '<img src="{}" style="max-height: 80px; border-radius: 6px;" />',
                url
            )
        return "—"


@admin.register(ProgramaDia)
class ProgramaDiaAdmin(admin.ModelAdmin):
    list_display = ('dia', 'festival', 'descripcion', 'orden', 'imagen_preview')
    list_display_links = ('dia',)
    list_filter = ('festival', 'dia')
    search_fields = ('descripcion',)
    list_editable = ('orden',)
    autocomplete_fields = ['festival']
    readonly_fields = ('imagen_preview',)
    list_per_page = 50

    @admin.display(description='Programa')
    def imagen_preview(self, obj):
        if obj.imagen_url:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.imagen_url
            )
        return "—"


@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    list_display = ('descripcion_corta', 'festival', 'orden', 'imagen_preview')
    list_display_links = ('descripcion_corta',)
    list_filter = ('festival',)
    search_fields = ('descripcion',)
    list_editable = ('orden',)
    autocomplete_fields = ['festival']
    readonly_fields = ('imagen_preview',)
    list_per_page = 50

    @admin.display(description='Descripción')
    def descripcion_corta(self, obj):
        return obj.descripcion or f"Foto #{obj.pk}"

    @admin.display(description='Foto')
    def imagen_preview(self, obj):
        url = obj.imagen
        if url:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                url
            )
        return "—"


@admin.register(VideoGaleria)
class VideoGaleriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'festival', 'destacado', 'orden', 'video_preview')
    list_display_links = ('titulo',)
    list_filter = ('festival', 'destacado')
    search_fields = ('titulo',)
    list_editable = ('destacado', 'orden')
    autocomplete_fields = ['festival']
    list_per_page = 50

    @admin.display(description='Video')
    def video_preview(self, obj):
        if obj.video_url:
            return format_html(
                '<video src="{}" style="max-height: 60px;" controls preload="metadata"></video>',
                obj.video_url
            )
        return "—"


@admin.register(Patrocinador)
class PatrocinadorAdmin(admin.ModelAdmin):
    list_display = ('nombre_o_id', 'festival', 'orden', 'logo_preview')
    list_display_links = ('nombre_o_id',)
    list_filter = ('festival',)
    search_fields = ('nombre',)
    list_editable = ('orden',)
    autocomplete_fields = ['festival']
    readonly_fields = ('logo_preview',)
    list_per_page = 50

    @admin.display(description='Nombre')
    def nombre_o_id(self, obj):
        return obj.nombre or f"Patrocinador #{obj.pk}"

    @admin.display(description='Logo')
    def logo_preview(self, obj):
        url = obj.logo_url
        if not url and obj.logo_local:
            url = obj.logo_local.url
        if url:
            return format_html(
                '<img src="{}" style="max-height: 60px; background: #f5f5f5; padding: 4px; border-radius: 4px;" />',
                url
            )
        return "—"


# =============================================================
#  ADMIN GLOBAL
# =============================================================

admin.site.site_header = "Administración · Festival de la Butifarra"
admin.site.site_title = "Festival de la Butifarra"
admin.site.index_title = "Panel de administración"