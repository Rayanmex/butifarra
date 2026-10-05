from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Expositor(models.Model):
    # ============ CATEGORÍAS ============
    CATEGORIA_CHOICES = [
        ('tradicional', 'Butifarra Tradicional'),
        ('especialidad', 'Especialidades'),
        ('mixto', 'Mixto (varios productos)'),
        ('quesos', 'Quesos y Embutidos'),
        ('bebidas', 'Bebidas y Postres'),
    ]

    ESTADO_SOLICITUD_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente de revisión'),
        ('observado', 'Con observaciones'),
        ('aprobado', 'Aprobado y publicado'),
        ('rechazado', 'Rechazado'),
        ('revision_pendiente', 'Cambios pendientes de aprobación'),
    ]

    # ============ Información básica ============
    nombre_expositor = models.CharField(
        max_length=200,
        verbose_name="Nombre del expositor",
        blank=True,
        null=True,
    )
    nombre_empresa = models.CharField(
        max_length=200,
        verbose_name="Marca o nombre de la empresa",
        default='Por definir',
    )
    logo = models.ImageField(
        upload_to='expositores/logos/',
        verbose_name="Logo de la marca o negocio",
        null=True,
        blank=True,
    )

    # ============ Contacto ============
    email_contacto = models.EmailField(
        verbose_name="Correo electrónico de contacto",
        blank=True,
        null=True,
    )
    numero_contacto = models.CharField(
        max_length=50,
        verbose_name="Número de contacto",
        help_text="Formato: 914 123 4567",
        blank=True,
        null=True,
    )

    # ============ Ubicación en el festival ============
    numero_stand = models.CharField(
        max_length=50,
        verbose_name="Número de stand",
        blank=True,
        null=True,
        help_text="Número del stand en el festival. Puede dejarse pendiente."
    )

    # ============ Redes sociales ============
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

    # ============ Menú ============
    menu_completo = models.TextField(
        verbose_name="Menú completo (Lista de productos y precios)",
        help_text="Ingresa cada producto con su precio.",
        blank=True,
        null=True,
    )

    # ============ Pagos ============
    acepta_tarjeta = models.BooleanField(
        default=False,
        verbose_name="¿Aceptan pago con tarjeta?"
    )
    acepta_efectivo = models.BooleanField(
        default=True,
        verbose_name="¿Acepta efectivo?"
    )

    # ============ Ubicación del negocio ============
    link_google_maps = models.URLField(
        max_length=500,
        verbose_name="Link de Google Maps de la ubicación del negocio",
        blank=True,
        null=True,
    )
    direccion_negocio = models.CharField(
        max_length=300,
        verbose_name="Dirección del negocio",
        blank=True,
        null=True,
        help_text="Escribe la dirección si no tienes link de Google Maps"
    )

    # ============ Enriquecimiento ============
    descripcion = models.TextField(
        verbose_name="Descripción corta del negocio",
        blank=True,
        null=True,
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
        null=True,
    )
    precio_desde = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio desde",
        blank=True,
        null=True,
    )
    es_destacado = models.BooleanField(
        default=False,
        verbose_name="¿Expositor destacado?"
    )

    # ============ Administración ============
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    # ============ Solicitud ============
    estado_solicitud = models.CharField(
        max_length=20,
        choices=ESTADO_SOLICITUD_CHOICES,
        default='borrador',
        verbose_name="Estado de solicitud"
    )
    fecha_envio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de envío de solicitud"
    )
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de revisión por admin"
    )
    nota_admin = models.TextField(
        blank=True,
        null=True,
        verbose_name="Nota del administrador",
        help_text="Explicación de aprobación, observaciones o rechazo (visible para el expositor)."
    )

    class Meta:
        verbose_name = "Expositor"
        verbose_name_plural = "Expositores"
        ordering = ['-es_destacado', 'numero_stand', 'nombre_empresa']

    def __str__(self):
        stand = self.numero_stand if self.numero_stand else "Sin asignar"
        return f"{self.nombre_empresa} - Stand #{stand}"

    # ============ Propiedades de estado ============
    @property
    def puede_editar(self):
        """
        El expositor SIEMPRE puede editar sus datos.
        Los cambios se guardan como CambioPendiente hasta que el admin apruebe.
        """
        return True

    @property
    def esta_pendiente(self):
        return self.estado_solicitud == 'pendiente'

    @property
    def esta_aprobado(self):
        return self.estado_solicitud == 'aprobado'

    @property
    def esta_rechazado(self):
        return self.estado_solicitud == 'rechazado'

    @property
    def esta_observado(self):
        return self.estado_solicitud == 'observado'

    @property
    def esta_en_revision(self):
        return self.estado_solicitud == 'revision_pendiente'

    @property
    def tiene_cambio_pendiente(self):
        """¿Tiene cambios sin aprobar?"""
        return hasattr(self, 'cambio_pendiente') and self.cambio_pendiente is not None

    @property
    def campos_requeridos_completos(self):
        """
        Campos mínimos para poder enviar la solicitud:
        datos básicos + al menos 1 producto registrado.
        """
        datos_basicos_ok = all([
            self.nombre_empresa and self.nombre_empresa != 'Por definir',
            self.nombre_expositor,
            self.email_contacto,
            self.numero_contacto,
            self.descripcion,
            self.categoria,
        ])
        return datos_basicos_ok and self.productos.exists()

    @classmethod
    def visibles_en_catalogo(cls):
        """
        Devuelve un queryset con los expositores que deben aparecer
        en el catálogo público:
          - activos
          - aprobados O con cambios pendientes de aprobación
            (en el segundo caso, el público ve la versión aprobada anterior,
             porque los cambios están en CambioPendiente, no en el Expositor)
        """
        from django.db.models import Q
        return cls.objects.filter(activo=True).filter(
            Q(estado_solicitud='aprobado') |
            Q(estado_solicitud='revision_pendiente')
        )


    

    # ============ Helpers de presentación ============
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

    # ============ Aplicar un cambio pendiente ============
    def aplicar_cambio_pendiente(self, cambio, admin_user=None):
        """
        Aplica el JSON de un CambioPendiente al Expositor actual.
        Es llamado por el admin al aprobar.
        """
        datos = cambio.datos
        campos = datos.get('expositor', {})

        # 1) Aplicar campos del Expositor
        for campo, valor in campos.items():
            if hasattr(self, campo) and campo not in ('id', 'pk'):
                setattr(self, campo, valor)

        self.estado_solicitud = 'aprobado'
        self.fecha_revision = timezone.now()
        self.nota_admin = ''
        self.save()

        # 2) Aplicar operaciones sobre productos y fotos
        for op in datos.get('operaciones', []):
            tipo = op.get('tipo')
            if tipo == 'producto_crear':
                Producto.objects.create(
                    expositor=self,
                    **op.get('datos', {})
                )
            elif tipo == 'producto_editar':
                producto_id = op.get('producto_id')
                try:
                    producto = Producto.objects.get(pk=producto_id, expositor=self)
                    for campo, valor in op.get('datos', {}).items():
                        setattr(producto, campo, valor)
                    producto.save()
                except Producto.DoesNotExist:
                    pass
            elif tipo == 'producto_eliminar':
                Producto.objects.filter(
                    pk=op.get('producto_id'), expositor=self
                ).delete()
            elif tipo == 'foto_eliminar':
                FotoProducto.objects.filter(
                    pk=op.get('foto_id'), expositor=self
                ).delete()
            # las fotos que se agregan ya están creadas (ver accounts/views.py)

        # 3) Recalcular precio_desde
        self.recalcular_precio_desde()

        # 4) Marcar el cambio como aprobado
        cambio.estado = 'aprobado'
        cambio.fecha_resolucion = timezone.now()
        cambio.resuelto_por = admin_user
        cambio.save()


class FotoProducto(models.Model):
    """Fotos de productos de cada expositor."""
    expositor = models.ForeignKey(
        Expositor,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Expositor"
    )
    imagen = models.ImageField(
        upload_to='expositores/productos/',
        verbose_name="Foto del producto"
    )
    descripcion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de producto"
        verbose_name_plural = "Fotos de productos"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Foto de {self.expositor.nombre_empresa}"


class Producto(models.Model):
    """Producto individual de un expositor."""

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
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del producto"
    )
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
        null=True,
    )
    descripcion = models.CharField(
        max_length=300,
        verbose_name="Descripción corta",
        blank=True,
        null=True,
    )
    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible en el festival"
    )
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
#  CAMBIOS PENDIENTES DE APROBACIÓN
# =============================================================

class CambioPendiente(models.Model):
    """
    Cambios que el expositor ha hecho y que esperan aprobación del admin.
    Solo hay UNO activo por expositor (se sobreescribe al editar de nuevo).
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    expositor = models.OneToOneField(
        Expositor,
        on_delete=models.CASCADE,
        related_name='cambio_pendiente',
        verbose_name='Expositor'
    )
    datos = models.JSONField(
        verbose_name='Datos del cambio',
        help_text='JSON con los campos del expositor y las operaciones sobre productos/fotos.'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cambios_resueltos'
    )

    class Meta:
        verbose_name = 'Cambio pendiente'
        verbose_name_plural = 'Cambios pendientes'
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Cambio de {self.expositor.nombre_empresa} ({self.get_estado_display()})"

    def resumen_campos(self):
        """Lista de campos que cambiaron (para mostrar en el admin)."""
        campos = self.datos.get('expositor', {})
        return list(campos.keys())

    def resumen_operaciones(self):
        """Lista legible de las operaciones."""
        ops = self.datos.get('operaciones', [])
        resumen = []
        for op in ops:
            tipo = op.get('tipo', '')
            if tipo == 'producto_crear':
                resumen.append(f"➕ Crear producto: {op.get('datos', {}).get('nombre', '?')}")
            elif tipo == 'producto_editar':
                resumen.append(f"✏️ Editar producto #{op.get('producto_id')}")
            elif tipo == 'producto_eliminar':
                resumen.append(f"🗑️ Eliminar producto #{op.get('producto_id')}")
            elif tipo == 'foto_eliminar':
                resumen.append(f"🗑️ Eliminar foto #{op.get('foto_id')}")
            elif tipo == 'foto_agregar':
                resumen.append(f"📷 Agregar foto: {op.get('datos', {}).get('descripcion', '')}")
            elif tipo == 'logo_actualizar':
                resumen.append("🖼️ Actualizar logo")
        return resumen


# =============================================================
#  HISTORIAL DE COMENTARIOS DEL ADMIN
# =============================================================

class ComentarioAdmin(models.Model):
    """
    Historial de comentarios que el admin hace sobre un expositor.
    El expositor los ve en su panel.
    """
    TIPO_CHOICES = [
        ('observacion', 'Observación'),
        ('aprobacion', 'Aprobación'),
        ('rechazo', 'Rechazo'),
        ('info', 'Información'),
    ]

    expositor = models.ForeignKey(
        Expositor,
        on_delete=models.CASCADE,
        related_name='comentarios_admin',
        verbose_name='Expositor'
    )
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Autor'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='observacion',
        verbose_name='Tipo'
    )
    texto = models.TextField(
        verbose_name='Comentario'
    )
    leido = models.BooleanField(
        default=False,
        verbose_name='¿Leído por el expositor?'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario del admin'
        verbose_name_plural = 'Comentarios del admin'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.expositor.nombre_empresa}"


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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='historia'
    )
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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='artistas'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=300, blank=True)
    cartel_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(
        upload_to='festival/artistas/',
        blank=True,
        null=True
    )
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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='programa'
    )
    dia = models.DateField()
    imagen_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(
        upload_to='festival/programa/',
        blank=True,
        null=True
    )
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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='galeria_fotos'
    )
    imagen_url = models.CharField(max_length=500, blank=True)
    imagen_local = models.ImageField(
        upload_to='festival/galeria/',
        blank=True,
        null=True
    )
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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='galeria_videos'
    )
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
    festival = models.ForeignKey(
        Festival,
        on_delete=models.CASCADE,
        related_name='patrocinadores'
    )
    nombre = models.CharField(max_length=200, blank=True)
    logo_url = models.CharField(max_length=500, blank=True)
    logo_local = models.ImageField(
        upload_to='festival/patrocinadores/',
        blank=True,
        null=True
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Patrocinador"
        verbose_name_plural = "Patrocinadores"

    def __str__(self):
        return self.nombre or f"Patrocinador #{self.pk}"