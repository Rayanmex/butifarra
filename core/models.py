from django.db import models
from django.core.validators import URLValidator


class Expositor(models.Model):
    # ============ CATEGORÍAS ============
    CATEGORIA_CHOICES = [
        ('tradicional', 'Butifarra Tradicional'),
        ('especialidad', 'Especialidades'),
        ('mixto', 'Mixto (varios productos)'),
        ('quesos', 'Quesos y Embutidos'),
        ('bebidas', 'Bebidas y Postres'),
    ]

    # Información básica
    nombre_expositor = models.CharField(max_length=200, verbose_name="Nombre del expositor")
    nombre_empresa = models.CharField(max_length=200, verbose_name="Marca o nombre de la empresa")
    logo = models.ImageField(upload_to='expositores/logos/', verbose_name="Logo de la marca o negocio",
                             null=True, blank=True)

    # Contacto
    email_contacto = models.EmailField(verbose_name="Correo electrónico de contacto")
    numero_contacto = models.CharField(max_length=50, verbose_name="Número de contacto",
                                       help_text="Formato: 914 123 4567")

    # Ubicación en el festival
    numero_stand = models.CharField(
        max_length=50,
        verbose_name="Número de stand",
        blank=True,
        null=True,
        help_text="Número del stand en el festival. Puede dejarse pendiente."
    )

    # Redes sociales — AHORA SON CharField (aceptan texto libre)
    enlace_red_social_1 = models.CharField(
        max_length=500,
        verbose_name="Red social principal",
        blank=True,
        null=True,
        help_text="URL completa o nombre de usuario"
    )
    enlace_red_social_2 = models.CharField(
        max_length=500,
        verbose_name="Red social adicional",
        blank=True,
        null=True,
        help_text="URL completa o nombre de usuario"
    )
    redes_sociales_texto = models.CharField(
        max_length=300,
        verbose_name="Redes sociales (texto)",
        blank=True,
        null=True,
        help_text="Si no tienes URLs completas, escribe los nombres de usuario aquí"
    )

    # Menú
    menu_completo = models.TextField(
        verbose_name="Menú completo (Lista de productos y precios)",
        help_text="Ingresa cada producto con su precio."
    )

    # Pagos
    acepta_tarjeta = models.BooleanField(default=False, verbose_name="¿Aceptan pago con tarjeta?")
    acepta_efectivo = models.BooleanField(default=True, verbose_name="¿Acepta efectivo?")

    # Ubicación del negocio
    link_google_maps = models.URLField(
        max_length=500,
        verbose_name="Link de Google Maps de la ubicación del negocio",
        blank=True,
        null=True
    )
    direccion_negocio = models.CharField(
        max_length=300,
        verbose_name="Dirección del negocio",
        blank=True,
        null=True,
        help_text="Escribe la dirección si no tienes link de Google Maps"
    )

    # Enriquecimiento
    descripcion = models.TextField(
        verbose_name="Descripción corta del negocio",
        blank=True,
        null=True
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='tradicional',
        verbose_name="Categoría"
    )
    especialidades = models.CharField(
        max_length=300,
        verbose_name="Especialidades",
        blank=True,
        null=True
    )
    precio_desde = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio desde",
        blank=True,
        null=True
    )
    es_destacado = models.BooleanField(
        default=False,
        verbose_name="¿Expositor destacado?"
    )

    # Administración
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Expositor"
        verbose_name_plural = "Expositores"
        ordering = ['-es_destacado', 'numero_stand', 'nombre_empresa']

    def __str__(self):
        stand = self.numero_stand if self.numero_stand else "Sin asignar"
        return f"{self.nombre_empresa} - Stand #{stand}"

    def get_menu_list(self):
        if not self.menu_completo:
            return []
        if '\n' in self.menu_completo:
            items = self.menu_completo.strip().split('\n')
        else:
            items = self.menu_completo.strip().split(',')
        return [item.strip() for item in items if item.strip()]

    def get_redes_sociales(self):
        redes = []
        if self.enlace_red_social_1:
            redes.append(self.enlace_red_social_1)
        if self.enlace_red_social_2:
            redes.append(self.enlace_red_social_2)
        return redes

    def get_stand_display(self):
        if self.numero_stand and self.numero_stand.strip() not in ['', '0', 'Ninguno', 'Todavía está pendiente.']:
            return f"Stand #{self.numero_stand}"
        return "Stand por asignar"

    def get_especialidades_list(self):
        if not self.especialidades:
            return []
        return [e.strip() for e in self.especialidades.split(',') if e.strip()]

    def tiene_fotos(self):
        return self.fotos.exists()

    def get_categoria_display_corta(self):
        return dict(self.CATEGORIA_CHOICES).get(self.categoria, 'General')

    def recalcular_precio_desde(self):
        from django.db.models import Min
        minimo = self.productos.aggregate(m=Min('precio'))['m']
        self.precio_desde = minimo
        self.save(update_fields=['precio_desde'])

    ESTADO_SOLICITUD_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente de revisión'),
        ('aprobado', 'Aprobado y publicado'),
        ('rechazado', 'Rechazado'),
    ]

    estado_solicitud = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD_CHOICES,
        default='borrador',
        verbose_name="Estado de solicitud"
    )
    fecha_envio = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha de envío de solicitud"
    )
    nota_admin = models.TextField(
        blank=True, null=True,
        verbose_name="Nota del administrador",
        help_text="Explicación de aprobación o rechazo (visible para el expositor)."
    )


class FotoProducto(models.Model):
    """Fotos de productos de cada expositor"""
    expositor = models.ForeignKey(
        Expositor,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Expositor"
    )
    imagen = models.ImageField(upload_to='expositores/productos/', verbose_name="Foto del producto")
    descripcion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de producto"
        verbose_name_plural = "Fotos de productos"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Foto de {self.expositor.nombre_empresa}"


class Producto(models.Model):
    """Producto individual de un expositor, extraído del menú o agregado a mano."""

    CATEGORIA_CHOICES = [
        ('butifarra_tradicional', 'Butifarra Tradicional'),
        ('butifarra_especialidad', 'Butifarra de Especialidad'),
        ('queso', 'Queso de Puerco'),
        ('longaniza', 'Longaniza'),
        ('carne', 'Carnes'),
        ('patitas', 'Patitas Curtidas'),
        ('salsa', 'Salsas y Aderezos'),
        ('bebida', 'Bebidas'),
        ('postre', 'Postres'),
        ('combo', 'Combos'),
        ('otro', 'Otros'),
    ]

    UNIDAD_CHOICES = [
        ('kg', 'Kilo'),
        ('1/2kg', 'Medio kilo'),
        ('1/4kg', 'Cuarto'),
        ('orden', 'Orden'),
        ('orden_fam', 'Orden familiar'),
        ('orden_media', 'Media orden'),
        ('orden_ind', 'Orden individual'),
        ('pieza', 'Pieza'),
        ('rebanada', 'Rebanada'),
        ('litro', 'Litro'),
        ('bote', 'Bote'),
        ('paquete', 'Paquete'),
        ('unidad', 'Unidad'),
    ]

    expositor = models.ForeignKey(
        Expositor,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name="Expositor"
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre del producto")
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        default='otro',
        verbose_name="Categoría"
    )
    unidad = models.CharField(
        max_length=20,
        choices=UNIDAD_CHOICES,
        default='unidad',
        verbose_name="Unidad de venta"
    )
    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio",
        blank=True,
        null=True
    )
    descripcion = models.CharField(
        max_length=300,
        verbose_name="Descripción corta",
        blank=True,
        null=True
    )
    disponible = models.BooleanField(default=True, verbose_name="Disponible en el festival")

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['categoria', 'nombre']
        indexes = [
            models.Index(fields=['categoria']),
            models.Index(fields=['precio']),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.expositor.nombre_empresa}"

    def get_precio_display(self):
        if self.precio is None:
            return "Consultar"
        if self.precio == int(self.precio):
            return f"${int(self.precio)}"
        return f"${self.precio:.2f}"



# =============================================================
#  FESTIVAL
# =============================================================

class Festival(models.Model):
    nombre = models.CharField(max_length=200, default="Festival de la Butifarra")
    edicion = models.PositiveIntegerField(unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    lugar = models.CharField(max_length=300, blank=True)
    slogan = models.CharField(max_length=300, blank=True)
    descripcion_corta = models.TextField(blank=True)
    logo = models.ImageField(upload_to='festival/logo/', blank=True, null=True)
    facebook_url = models.CharField(max_length=500, blank=True)
    instagram_url = models.CharField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-edicion']
        verbose_name = "Festival"
        verbose_name_plural = "Festivales"

    def __str__(self):
        return f"{self.edicion}° {self.nombre}"


class HistoriaFestival(models.Model):
    """Bloques de historia (aparecen en el index)."""
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='historia')
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True)
    parrafo = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Bloque de historia"
        verbose_name_plural = "Historia del festival"

    def __str__(self):
        return self.titulo


class Artista(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='artistas')
    nombre = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=300, blank=True)
    cartel_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(upload_to='festival/artistas/', blank=True, null=True)
    dia_presentacion = models.DateField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Artista"
        verbose_name_plural = "Artistas"

    def __str__(self):
        return self.nombre

    @property
    def imagen_url(self):
        if self.imagen_local:
            return self.imagen_local.url
        return self.cartel_url or ''


class ProgramaDia(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='programa')
    dia = models.DateField()
    imagen_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(upload_to='festival/programa/', blank=True, null=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'dia']
        verbose_name = "Día del programa"
        verbose_name_plural = "Programa por día"

    def __str__(self):
        return f"Programa {self.dia}"

    @property
    def imagen(self):
        if self.imagen_local:
            return self.imagen_local.url
        return self.imagen_url or ''


class FotoGaleria(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='galeria_fotos')
    imagen_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(upload_to='festival/galeria/', blank=True, null=True)
    descripcion = models.CharField(max_length=200, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Foto de galería"
        verbose_name_plural = "Fotos de galería"

    def __str__(self):
        return self.descripcion or f"Foto #{self.pk}"

    @property
    def imagen(self):
        if self.imagen_local:
            return self.imagen_local.url
        return self.imagen_url or ''


class VideoGaleria(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='galeria_videos')
    titulo = models.CharField(max_length=200)
    video_url = models.CharField(max_length=500)
    poster_url = models.CharField(max_length=500, blank=True)
    destacado = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-destacado', 'orden']
        verbose_name = "Video de galería"
        verbose_name_plural = "Videos de galería"

    def __str__(self):
        return self.titulo


class Patrocinador(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='patrocinadores')
    nombre = models.CharField(max_length=200, blank=True)
    logo_url = models.CharField(max_length=500, blank=True)
    logo_local = models.ImageField(upload_to='festival/patrocinadores/', blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Patrocinador"
        verbose_name_plural = "Patrocinadores"

    def __str__(self):
        return self.nombre or f"Patrocinador #{self.pk}"