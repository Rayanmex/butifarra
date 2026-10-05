from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, Count
from django.utils import timezone
from django.db import transaction
from decimal import Decimal, InvalidOperation

from .models import (
    Expositor,
    Producto,
    FotoProducto,
    CambioPendiente,
    ComentarioAdmin,
    Festival,
    HistoriaFestival,
    Artista,
    ProgramaDia,
    FotoGaleria,
    VideoGaleria,
    Patrocinador,
)
from .forms import (
    ExpositorAdminForm,
    ProductoForm,
    RevisionSolicitudForm,
    CrearUsuarioExpositorForm,
    ResetPasswordForm,
    ComentarioAdminForm,
)

# Decoradores de rol
from accounts.decorators import admin_requerido


# =============================================================
#  VISTAS PÚBLICAS
# =============================================================

def index(request):
    festival = Festival.objects.filter(activo=True).order_by('-edicion').first()
    return render(request, 'core/index.html', {
        'festival': festival,
        'historia': festival.historia.all() if festival else [],
        'artistas': festival.artistas.all() if festival else [],
        'dias_programa': festival.programa.all() if festival else [],
        'galeria_fotos': festival.galeria_fotos.all() if festival else [],
        'galeria_videos': festival.galeria_videos.all() if festival else [],
        'patrocinadores': festival.patrocinadores.all() if festival else [],
    })


def contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        asunto = request.POST.get('asunto', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()

        if nombre and email and asunto and mensaje:
            messages.success(
                request,
                '¡Gracias por escribirnos! Te responderemos a la brevedad.'
            )
            return redirect('core:contacto')
        else:
            messages.error(request, 'Por favor completa todos los campos.')

    return render(request, 'core/contact.html')


def historia(request):
    festival = Festival.objects.filter(activo=True).order_by('-edicion').first()
    return render(request, 'core/historia.html', {
        'festival': festival,
        'historia': festival.historia.all() if festival else [],
    })


def programa(request):
    festival = Festival.objects.filter(activo=True).order_by('-edicion').first()

    if not festival:
        return render(request, 'core/programa.html', {
            'festival': None,
            'dias_programa': [],
            'artistas': [],
        })

    dias_programa = festival.programa.all()
    artistas = festival.artistas.all()

    artistas_por_dia = {}
    for art in artistas:
        if art.dia_presentacion:
            artistas_por_dia.setdefault(art.dia_presentacion, []).append(art)

    for dia in dias_programa:
        dia.artistas_del_dia = artistas_por_dia.get(dia.dia, [])

    return render(request, 'core/programa.html', {
        'festival': festival,
        'dias_programa': dias_programa,
        'artistas': artistas,
    })


def productores(request):
    return redirect('core:expositores_list')


# =============================================================
#  EXPOSITORES: LISTA + LANDING FUSIONADAS
# =============================================================

def expositores_list(request):
    """
    Catálogo con filtros + contenido editorial del festival.
    Muestra expositores ACTIVOS que estén APROBADOS o con
    CAMBIOS PENDIENTES (revision_pendiente). En el segundo caso,
    el público ve la versión aprobada anterior porque los cambios
    viven en CambioPendiente hasta que el admin los aprueba.
    """
    festival = Festival.objects.filter(activo=True).order_by('-edicion').first()
    modo = request.GET.get('modo', 'expositores')

    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    especialidad = request.GET.get('especialidad', '').strip()
    precio_min = request.GET.get('precio_min', '').strip()
    precio_max = request.GET.get('precio_max', '').strip()
    acepta_tarjeta = request.GET.get('tarjeta', '') == '1'
    solo_con_fotos = request.GET.get('fotos', '') == '1'
    orden = request.GET.get('orden', 'nombre')
    categoria_producto = request.GET.get('cat_prod', '').strip()

    # Base: visibles (aprobados + revisión pendiente)
    expositores = Expositor.visibles_en_catalogo()

    if q:
        expositores = expositores.filter(
            Q(nombre_empresa__icontains=q) |
            Q(nombre_expositor__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(especialidades__icontains=q) |
            Q(menu_completo__icontains=q) |
            Q(productos__nombre__icontains=q)
        ).distinct()

    if categoria:
        expositores = expositores.filter(categoria=categoria)

    if especialidad:
        expositores = expositores.filter(especialidades__icontains=especialidad)

    if precio_min or precio_max:
        filtro_precio = Q()
        if precio_min:
            try:
                filtro_precio &= Q(productos__precio__gte=Decimal(precio_min))
            except InvalidOperation:
                pass
        if precio_max:
            try:
                filtro_precio &= Q(productos__precio__lte=Decimal(precio_max))
            except InvalidOperation:
                pass
        expositores = expositores.filter(filtro_precio).distinct()

    if acepta_tarjeta:
        expositores = expositores.filter(acepta_tarjeta=True)

    if solo_con_fotos:
        expositores = expositores.filter(fotos__isnull=False).distinct()

    ordenamientos = {
        'nombre': 'nombre_empresa',
        'precio_asc': 'precio_desde',
        'precio_desc': '-precio_desde',
        'stand': 'numero_stand',
        'reciente': '-fecha_registro',
    }
    expositores = expositores.order_by(
        '-es_destacado',
        ordenamientos.get(orden, 'nombre_empresa')
    )

    # Categorías disponibles
    visibles_ids = Expositor.visibles_en_catalogo().values_list('id', flat=True)
    categorias_disponibles = Expositor.objects.filter(
        id__in=visibles_ids
    ).values_list('categoria', flat=True).distinct()
    categorias_disponibles = [
        (c, dict(Expositor.CATEGORIA_CHOICES).get(c, c))
        for c in categorias_disponibles if c
    ]

    # Especialidades top
    especialidades_raw = Expositor.objects.filter(
        id__in=visibles_ids,
        especialidades__isnull=False
    ).exclude(especialidades='').values_list('especialidades', flat=True)

    contador_esp = {}
    for esp_str in especialidades_raw:
        for esp in esp_str.split(','):
            esp = esp.strip()
            if esp:
                contador_esp[esp] = contador_esp.get(esp, 0) + 1
    especialidades_top = sorted(contador_esp.items(), key=lambda x: -x[1])[:12]

    # Rango de precios
    rango_precios = Producto.objects.filter(
        expositor__id__in=visibles_ids,
    ).aggregate(min_p=Min('precio'), max_p=Max('precio'))

    # Contadores globales
    total_expositores = Expositor.objects.filter(id__in=visibles_ids).count()
    total_destacados = Expositor.objects.filter(
        id__in=visibles_ids, es_destacado=True
    ).count()
    total_con_menu = Expositor.objects.filter(
        id__in=visibles_ids
    ).exclude(menu_completo='').count()

    # Modo productos
    productos_qs = None
    if modo == 'productos':
        productos_qs = Producto.objects.filter(
            expositor__id__in=visibles_ids,
            disponible=True
        ).select_related('expositor')

        if q:
            productos_qs = productos_qs.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(expositor__nombre_empresa__icontains=q)
            )
        if categoria:
            productos_qs = productos_qs.filter(expositor__categoria=categoria)
        if categoria_producto:
            productos_qs = productos_qs.filter(categoria=categoria_producto)
        if precio_min:
            try:
                productos_qs = productos_qs.filter(precio__gte=Decimal(precio_min))
            except InvalidOperation:
                pass
        if precio_max:
            try:
                productos_qs = productos_qs.filter(precio__lte=Decimal(precio_max))
            except InvalidOperation:
                pass
        if acepta_tarjeta:
            productos_qs = productos_qs.filter(expositor__acepta_tarjeta=True)

        if orden == 'precio_asc':
            productos_qs = productos_qs.order_by('precio')
        elif orden == 'precio_desc':
            productos_qs = productos_qs.order_by('-precio')
        elif orden == 'nombre':
            productos_qs = productos_qs.order_by('nombre')
        else:
            productos_qs = productos_qs.order_by('categoria', 'nombre')

    if modo == 'productos':
        paginator = Paginator(productos_qs, 24)
    else:
        paginator = Paginator(expositores, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    total_resultados = paginator.count

    qs = request.GET.copy()
    qs.pop('page', None)
    qs.pop('modo', None)
    querystring = qs.urlencode()

    contexto = {
        'festival': festival,
        'modo': modo,
        'page_obj': page_obj,
        'expositores': page_obj if modo == 'expositores' else None,
        'productos': page_obj if modo == 'productos' else None,
        'total_resultados': total_resultados,
        'total_expositores': total_expositores,
        'total_destacados': total_destacados,
        'total_con_menu': total_con_menu,
        'categorias_disponibles': categorias_disponibles,
        'especialidades_top': especialidades_top,
        'categorias_producto': Producto.CATEGORIA_CHOICES,
        'rango_precios': rango_precios,
        'querystring': querystring,
        'filtros': {
            'q': q,
            'categoria': categoria,
            'especialidad': especialidad,
            'precio_min': precio_min,
            'precio_max': precio_max,
            'tarjeta': acepta_tarjeta,
            'fotos': solo_con_fotos,
            'orden': orden,
            'cat_prod': categoria_producto,
        },
    }
    return render(request, 'core/expositores_list.html', contexto)


def expositor_detail(request, pk):
    """
    Detalle público. Visible si está activo y (aprobado o con cambios pendientes).
    """
    expositor = get_object_or_404(
        Expositor.visibles_en_catalogo(),
        pk=pk,
    )
    productos = expositor.productos.filter(disponible=True)
    fotos = expositor.fotos.all()

    productos_por_categoria = {}
    for prod in productos:
        cat_display = prod.get_categoria_display()
        productos_por_categoria.setdefault(cat_display, []).append(prod)

    relacionados = (
        Expositor.visibles_en_catalogo()
        .filter(categoria=expositor.categoria)
        .exclude(pk=expositor.pk)
        .order_by('-es_destacado')[:3]
    )

    contexto = {
        'expositor': expositor,
        'productos': productos,
        'productos_por_categoria': productos_por_categoria,
        'fotos': fotos,
        'relacionados': relacionados,
    }
    return render(request, 'core/expositor_detail.html', contexto)


# =============================================================
#  PANEL DE CONTROL — SOLO ADMIN
# =============================================================

@admin_requerido
def panel_dashboard(request):
    """Dashboard principal del panel."""
    total_expositores = Expositor.objects.count()
    activos = Expositor.objects.filter(activo=True).count()
    inactivos = total_expositores - activos
    destacados = Expositor.objects.filter(es_destacado=True).count()

    total_fotos = FotoProducto.objects.count()
    total_productos = Producto.objects.count()

    ultimos = Expositor.objects.order_by('-fecha_registro')[:5]

    sin_logo = Expositor.objects.filter(Q(logo='') | Q(logo__isnull=True)).count()
    sin_fotos = Expositor.objects.annotate(n_fotos=Count('fotos')).filter(n_fotos=0).count()
    sin_menu = Expositor.objects.filter(Q(menu_completo='') | Q(menu_completo__isnull=True)).count()

    # ===== Conteos de solicitudes =====
    solicitudes_pendientes = Expositor.objects.filter(estado_solicitud='pendiente').count()
    solicitudes_observadas = Expositor.objects.filter(estado_solicitud='observado').count()
    solicitudes_aprobadas = Expositor.objects.filter(estado_solicitud='aprobado').count()
    solicitudes_rechazadas = Expositor.objects.filter(estado_solicitud='rechazado').count()
    solicitudes_borrador = Expositor.objects.filter(estado_solicitud='borrador').count()
    solicitudes_en_revision = Expositor.objects.filter(estado_solicitud='revision_pendiente').count()

    contexto = {
        'total_expositores': total_expositores,
        'activos': activos,
        'inactivos': inactivos,
        'destacados': destacados,
        'total_fotos': total_fotos,
        'total_productos': total_productos,
        'ultimos': ultimos,
        'sin_logo': sin_logo,
        'sin_fotos': sin_fotos,
        'sin_menu': sin_menu,
        # Solicitudes
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_observadas': solicitudes_observadas,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'solicitudes_borrador': solicitudes_borrador,
        'solicitudes_en_revision': solicitudes_en_revision,
    }
    return render(request, 'core/panel/dashboard.html', contexto)


# =============================================================
#  PANEL: SOLICITUDES (revisión por admin)
# =============================================================

@admin_requerido
def panel_solicitudes(request):
    """Lista de solicitudes, filtrable por estado."""
    estado = request.GET.get('estado', 'requieren_accion').strip()
    q = request.GET.get('q', '').strip()

    solicitudes = Expositor.objects.all()

    if estado == 'requieren_accion':
        solicitudes = solicitudes.filter(
            estado_solicitud__in=['pendiente', 'revision_pendiente', 'observado']
        )
    elif estado and estado != 'todas':
        solicitudes = solicitudes.filter(estado_solicitud=estado)

    if q:
        solicitudes = solicitudes.filter(
            Q(nombre_empresa__icontains=q) |
            Q(nombre_expositor__icontains=q) |
            Q(email_contacto__icontains=q) |
            Q(numero_contacto__icontains=q)
        )

    solicitudes = solicitudes.order_by('-fecha_envio', '-fecha_registro')

    contadores = {
        'todas': Expositor.objects.count(),
        'requieren_accion': Expositor.objects.filter(
            estado_solicitud__in=['pendiente', 'revision_pendiente', 'observado']
        ).count(),
        'borrador': Expositor.objects.filter(estado_solicitud='borrador').count(),
        'pendiente': Expositor.objects.filter(estado_solicitud='pendiente').count(),
        'observado': Expositor.objects.filter(estado_solicitud='observado').count(),
        'aprobado': Expositor.objects.filter(estado_solicitud='aprobado').count(),
        'rechazado': Expositor.objects.filter(estado_solicitud='rechazado').count(),
        'revision_pendiente': Expositor.objects.filter(estado_solicitud='revision_pendiente').count(),
    }

    contexto = {
        'solicitudes': solicitudes,
        'total': solicitudes.count(),
        'estado_actual': estado,
        'q': q,
        'contadores': contadores,
        'estados': Expositor.ESTADO_SOLICITUD_CHOICES,
    }
    return render(request, 'core/panel/solicitudes.html', contexto)


@admin_requerido
def panel_solicitud_detalle(request, pk):
    """
    Detalle de una solicitud.
    - Si hay un CambioPendiente, muestra los cambios propuestos y permite aprobar/rechazar.
    - Si no hay, permite aprobar/observar/rechazar la solicitud inicial.
    """
    expositor = get_object_or_404(Expositor, pk=pk)
    fotos = expositor.fotos.all()
    productos = expositor.productos.all().order_by('categoria', 'nombre')
    cambio = getattr(expositor, 'cambio_pendiente', None)
    comentarios = expositor.comentarios_admin.all()[:10]

    if request.method == 'POST':
        form = RevisionSolicitudForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            comentario = form.cleaned_data['comentario'].strip()

            with transaction.atomic():
                if accion == 'aprobar':
                    if cambio:
                        # Aplicar los cambios al Expositor y marcar el cambio como aprobado
                        expositor.aplicar_cambio_pendiente(cambio, request.user)
                    else:
                        # Aprobar la solicitud inicial (no había cambios pendientes)
                        expositor.estado_solicitud = 'aprobado'
                        expositor.activo = True
                        expositor.fecha_revision = timezone.now()
                        expositor.save(update_fields=[
                            'estado_solicitud', 'activo', 'fecha_revision'
                        ])

                    # Registrar comentario de aprobación
                    ComentarioAdmin.objects.create(
                        expositor=expositor,
                        autor=request.user,
                        tipo='aprobacion',
                        texto=comentario or 'Solicitud aprobada.',
                    )

                elif accion in ('observar', 'rechazar'):
                    # NO se toca el Expositor (mantiene su versión aprobada anterior)
                    # Solo se marca el cambio como rechazado y se registra el comentario.
                    if cambio:
                        cambio.estado = 'rechazado'
                        cambio.fecha_resolucion = timezone.now()
                        cambio.resuelto_por = request.user
                        cambio.save(update_fields=[
                            'estado', 'fecha_resolucion', 'resuelto_por'
                        ])

                    tipo = 'observacion' if accion == 'observar' else 'rechazo'
                    ComentarioAdmin.objects.create(
                        expositor=expositor,
                        autor=request.user,
                        tipo=tipo,
                        texto=comentario,
                    )

                    # Actualizar estado del expositor
                    expositor.estado_solicitud = (
                        'observado' if accion == 'observar' else 'rechazado'
                    )
                    expositor.nota_admin = comentario
                    expositor.fecha_revision = timezone.now()
                    expositor.save(update_fields=[
                        'estado_solicitud', 'nota_admin', 'fecha_revision'
                    ])

            mensajes_por_accion = {
                'aprobar': f'✅ Solicitud aprobada: {expositor.nombre_empresa}',
                'observar': f'📝 Observaciones enviadas: {expositor.nombre_empresa}',
                'rechazar': f'❌ Solicitud rechazada: {expositor.nombre_empresa}',
            }
            messages.success(request, mensajes_por_accion.get(accion, 'Acción realizada.'))
            return redirect('core:panel_solicitudes')
        else:
            messages.error(request, 'Revisa el formulario: falta el comentario o hay errores.')
    else:
        form = RevisionSolicitudForm()

    contexto = {
        'expositor': expositor,
        'fotos': fotos,
        'productos': productos,
        'cambio': cambio,
        'comentarios': comentarios,
        'form': form,
    }
    return render(request, 'core/panel/solicitud_detalle.html', contexto)


# =============================================================
#  PANEL: GESTIÓN DE USUARIOS (expositores)
# =============================================================

@admin_requerido
def panel_usuarios(request):
    """Lista de usuarios con perfil expositor."""
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()  # activo / inactivo / sin_perfil

    perfiles = (
        User.objects
        .select_related('perfil', 'perfil__expositor')
        .order_by('-date_joined')
    )

    if q:
        perfiles = perfiles.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(perfil__expositor__nombre_empresa__icontains=q)
        )

    if estado == 'activo':
        perfiles = perfiles.filter(is_active=True)
    elif estado == 'inactivo':
        perfiles = perfiles.filter(is_active=False)

    contexto = {
        'usuarios': perfiles,
        'total': perfiles.count(),
        'filtros': {'q': q, 'estado': estado},
    }
    return render(request, 'core/panel/usuarios.html', contexto)


@admin_requerido
def panel_usuario_create(request):
    """Crear un nuevo usuario expositor desde el panel admin."""
    if request.method == 'POST':
        form = CrearUsuarioExpositorForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Usuario creado: {user.username} → {user.perfil.expositor.nombre_empresa}'
            )
            return redirect('core:panel_usuarios')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = CrearUsuarioExpositorForm()

    return render(request, 'core/panel/usuario_form.html', {
        'form': form,
        'modo': 'crear',
    })


@admin_requerido
def panel_usuario_edit(request, pk):
    """Editar los datos del User (username, email, first_name, is_active)."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        errores = []
        if not username:
            errores.append('El usuario es obligatorio.')
        if User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
            errores.append('Ese nombre de usuario ya existe.')
        if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            errores.append('Ese correo ya está en uso.')

        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.is_active = is_active
            user.save(update_fields=['username', 'email', 'first_name', 'is_active'])
            messages.success(request, f'Usuario actualizado: {user.username}')
            return redirect('core:panel_usuarios')

    contexto = {
        'usuario': user,
        'modo': 'editar',
    }
    return render(request, 'core/panel/usuario_edit.html', contexto)


@admin_requerido
def panel_usuario_reset_password(request, pk):
    """Resetear la contraseña de un usuario."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            nueva = form.cleaned_data['password1']
            user.set_password(nueva)
            user.save(update_fields=['password'])
            messages.success(
                request,
                f'Contraseña actualizada para {user.username}.'
            )
            return redirect('core:panel_usuarios')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = ResetPasswordForm()

    return render(request, 'core/panel/usuario_reset_password.html', {
        'form': form,
        'usuario': user,
    })


@admin_requerido
def panel_usuario_toggle_activo(request, pk):
    """Activa/desactiva un usuario (bloquea su login)."""
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(
        request,
        f"{'Activado' if user.is_active else 'Desactivado'}: {user.username}"
    )
    return redirect(request.META.get('HTTP_REFERER', 'core:panel_usuarios'))


# =============================================================
#  PANEL: COMENTARIOS DEL ADMIN
# =============================================================

@admin_requerido
def panel_comentarios(request, pk):
    """Historial completo de comentarios de un expositor."""
    expositor = get_object_or_404(Expositor, pk=pk)
    comentarios = expositor.comentarios_admin.all()

    if request.method == 'POST':
        form = ComentarioAdminForm(request.POST)
        if form.is_valid():
            ComentarioAdmin.objects.create(
                expositor=expositor,
                autor=request.user,
                tipo=form.cleaned_data['tipo'],
                texto=form.cleaned_data['texto'],
            )
            messages.success(request, 'Comentario añadido.')
            return redirect('core:panel_comentarios', pk=expositor.pk)
    else:
        form = ComentarioAdminForm()

    contexto = {
        'expositor': expositor,
        'comentarios': comentarios,
        'form': form,
    }
    return render(request, 'core/panel/comentarios.html', contexto)


# =============================================================
#  PANEL: EXPOSITORES (gestión general)
# =============================================================

@admin_requerido
def panel_expositores(request):
    """Lista de expositores con búsqueda y filtros."""
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    estado_solicitud = request.GET.get('estado_solicitud', '').strip()
    categoria = request.GET.get('categoria', '')
    tiene_logo = request.GET.get('logo', '')
    tiene_fotos = request.GET.get('fotos', '')

    expositores = Expositor.objects.annotate(n_fotos=Count('fotos'))

    if q:
        expositores = expositores.filter(
            Q(nombre_empresa__icontains=q) |
            Q(nombre_expositor__icontains=q) |
            Q(email_contacto__icontains=q) |
            Q(numero_contacto__icontains=q) |
            Q(numero_stand__icontains=q)
        )

    if estado == 'activo':
        expositores = expositores.filter(activo=True)
    elif estado == 'inactivo':
        expositores = expositores.filter(activo=False)

    if estado_solicitud:
        expositores = expositores.filter(estado_solicitud=estado_solicitud)

    if categoria:
        expositores = expositores.filter(categoria=categoria)

    if tiene_logo == 'si':
        expositores = expositores.exclude(Q(logo='') | Q(logo__isnull=True))
    elif tiene_logo == 'no':
        expositores = expositores.filter(Q(logo='') | Q(logo__isnull=True))

    if tiene_fotos == 'si':
        expositores = expositores.filter(n_fotos__gt=0)
    elif tiene_fotos == 'no':
        expositores = expositores.filter(n_fotos=0)

    expositores = expositores.order_by('-es_destacado', 'nombre_empresa')

    contexto = {
        'expositores': expositores,
        'total': expositores.count(),
        'filtros': {
            'q': q,
            'estado': estado,
            'estado_solicitud': estado_solicitud,
            'categoria': categoria,
            'logo': tiene_logo,
            'fotos': tiene_fotos,
        },
        'categorias': Expositor.CATEGORIA_CHOICES,
        'estados_solicitud': Expositor.ESTADO_SOLICITUD_CHOICES,
    }
    return render(request, 'core/panel/expositores.html', contexto)


@admin_requerido
def panel_expositor_detail(request, pk):
    """Detalle completo de un expositor."""
    expositor = get_object_or_404(Expositor, pk=pk)
    fotos = expositor.fotos.all()
    productos = expositor.productos.all().order_by('categoria', 'nombre')
    cambio = getattr(expositor, 'cambio_pendiente', None)
    comentarios = expositor.comentarios_admin.all()[:5]

    contexto = {
        'expositor': expositor,
        'fotos': fotos,
        'productos': productos,
        'cambio': cambio,
        'comentarios': comentarios,
    }
    return render(request, 'core/panel/expositor_detail.html', contexto)


@admin_requerido
def panel_toggle_activo(request, pk):
    """Activa/desactiva un expositor."""
    exp = get_object_or_404(Expositor, pk=pk)
    exp.activo = not exp.activo
    exp.save(update_fields=['activo'])
    messages.success(request, f"{'Activado' if exp.activo else 'Desactivado'}: {exp.nombre_empresa}")
    return redirect(request.META.get('HTTP_REFERER', 'core:panel_expositores'))


@admin_requerido
def panel_toggle_destacado(request, pk):
    """Marca/desmarca un expositor como destacado."""
    exp = get_object_or_404(Expositor, pk=pk)
    exp.es_destacado = not exp.es_destacado
    exp.save(update_fields=['es_destacado'])
    messages.success(request, f"{'⭐ Destacado' if exp.es_destacado else '☆ Ya no destacado'}: {exp.nombre_empresa}")
    return redirect(request.META.get('HTTP_REFERER', 'core:panel_expositores'))


@admin_requerido
def panel_expositor_edit(request, pk):
    """Editar un expositor desde el panel (admin)."""
    expositor = get_object_or_404(Expositor, pk=pk)

    if request.method == 'POST':
        form = ExpositorAdminForm(request.POST, request.FILES, instance=expositor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Expositor actualizado: {expositor.nombre_empresa}')
            return redirect('core:panel_expositor_detail', pk=expositor.pk)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ExpositorAdminForm(instance=expositor)

    return render(request, 'core/panel/expositor_edit.html', {
        'expositor': expositor,
        'form': form,
    })


# =============================================================
#  PANEL: PRODUCTOS
# =============================================================

@admin_requerido
def panel_producto_create(request, pk):
    """Crear un producto desde el panel."""
    expositor = get_object_or_404(Expositor, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.expositor = expositor
            producto.save()
            expositor.recalcular_precio_desde()
            messages.success(request, f'Producto "{producto.nombre}" añadido.')
            return redirect('core:panel_expositor_detail', pk=expositor.pk)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'core/panel/producto_form.html', {
        'expositor': expositor,
        'form': form,
        'modo': 'crear',
    })


@admin_requerido
def panel_producto_edit(request, prod_pk):
    """Editar un producto."""
    producto = get_object_or_404(Producto, pk=prod_pk)
    expositor = producto.expositor

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            expositor.recalcular_precio_desde()
            messages.success(request, f'Producto "{producto.nombre}" actualizado.')
            return redirect('core:panel_expositor_detail', pk=expositor.pk)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'core/panel/producto_form.html', {
        'expositor': expositor,
        'producto': producto,
        'form': form,
        'modo': 'editar',
    })


@admin_requerido
def panel_producto_delete(request, prod_pk):
    """Eliminar un producto."""
    producto = get_object_or_404(Producto, pk=prod_pk)
    expositor = producto.expositor
    nombre = producto.nombre 
    producto.delete()
    expositor.recalcular_precio_desde()
    messages.success(request, f'Producto "{nombre}" eliminado.')
    return redirect('core:panel_expositor_detail', pk=expositor.pk)


@admin_requerido
def panel_importar_menu(request, pk):
    """Convierte el menu_completo en Productos individuales."""
    expositor = get_object_or_404(Expositor, pk=pk)

    if request.method != 'POST':
        return redirect('core:panel_expositor_detail', pk=pk)

    if not expositor.menu_completo:
        messages.warning(request, 'Este expositor no tiene menú de texto.')
        return redirect('core:panel_expositor_detail', pk=pk)

    reemplazar = request.POST.get('reemplazar') == '1'
    productos = importar_productos_desde_menu(expositor, reemplazar=reemplazar)

    if productos:
        messages.success(request, f'{len(productos)} productos importados del menú.')
    else:
        messages.warning(request, 'No se pudo detectar ningún producto en el menú.')

    return redirect('core:panel_expositor_detail', pk=pk)


# =============================================================
#  PANEL: FOTOS
# =============================================================

@admin_requerido
def panel_foto_upload(request, pk):
    """Subir una o varias fotos de productos."""
    expositor = get_object_or_404(Expositor, pk=pk)

    if request.method == 'POST':
        files = request.FILES.getlist('imagen')
        descripcion = request.POST.get('descripcion', '').strip()

        subidas = 0
        for f in files:
            FotoProducto.objects.create(
                expositor=expositor,
                imagen=f,
                descripcion=descripcion,
            )
            subidas += 1

        if subidas:
            messages.success(request, f'{subidas} foto(s) subida(s).')
        else:
            messages.warning(request, 'No se subió ninguna foto.')

    return redirect('core:panel_expositor_detail', pk=pk)


@admin_requerido
def panel_foto_delete(request, foto_pk):
    """Eliminar una foto."""
    foto = get_object_or_404(FotoProducto, pk=foto_pk)
    expositor = foto.expositor
    foto.delete()
    messages.success(request, 'Foto eliminada.')
    return redirect('core:panel_expositor_detail', pk=expositor.pk)


# =============================================================
#  PANEL: LOGO
# =============================================================

@admin_requerido
def panel_logo_delete(request, pk):
    """Eliminar el logo del expositor."""
    expositor = get_object_or_404(Expositor, pk=pk)
    if expositor.logo:
        expositor.logo.delete(save=True)
        messages.success(request, 'Logo eliminado.')
    return redirect('core:panel_expositor_detail', pk=pk)


@admin_requerido
def panel_logos_bulk(request):
    """Editor masivo de logos."""
    expositores = Expositor.objects.order_by('nombre_empresa')

    if request.method == 'POST':
        actualizados = 0
        errores = []

        for exp in expositores:
            archivo = request.FILES.get(f'logo_{exp.pk}')
            if not archivo:
                continue

            try:
                if exp.logo:
                    exp.logo.delete(save=False)

                exp.logo = archivo
                exp.save(update_fields=['logo'])
                actualizados += 1
            except Exception as e:
                errores.append(f"{exp.nombre_empresa}: {e}")

        if actualizados:
            messages.success(request, f'✅ {actualizados} logos actualizados correctamente.')
        else:
            messages.warning(request, 'No se subió ningún logo nuevo.')

        if errores:
            for err in errores:
                messages.error(request, f'Error: {err}')

        return redirect('core:panel_logos_bulk')

    return render(request, 'core/panel/logos_bulk.html', {
        'expositores': expositores,
    })