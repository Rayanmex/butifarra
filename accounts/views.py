from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count

from .forms import LoginForm, RegistroExpositorForm
from core.forms import ExpositorForm, ProductoForm, FotoProductoForm

from .decorators import admin_requerido, expositor_requerido
from .models import PerfilUsuario
from core.models import Expositor, Producto, FotoProducto


# ============================================================
#  LOGIN
# ============================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')

            perfil = getattr(user, 'perfil', None)
            if user.is_superuser or (perfil and perfil.rol == 'admin'):
                return redirect('core:panel_dashboard')
            elif perfil and perfil.rol == 'expositor':
                return redirect('accounts:panel_expositor')
            else:
                return redirect('core:index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


# ============================================================
#  LOGOUT
# ============================================================
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión.')
    return redirect('accounts:login')


# ============================================================
#  REGISTRO (solo expositores)
# ============================================================
def registro_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = RegistroExpositorForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido al panel de expositores.')
            return redirect('accounts:panel_expositor')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = RegistroExpositorForm()

    return render(request, 'accounts/registro.html', {'form': form})


# ============================================================
#  REDIRECT INTELIGENTE
# ============================================================
@login_required(login_url='accounts:login')
def dashboard_redirect(request):
    perfil = getattr(request.user, 'perfil', None)

    if request.user.is_superuser or (perfil and perfil.rol == 'admin'):
        return redirect('core:panel_dashboard')
    elif perfil and perfil.rol == 'expositor':
        return redirect('accounts:panel_expositor')

    messages.warning(request, 'Tu cuenta no tiene un rol asignado.')
    return redirect('core:index')


# ============================================================
#  PANEL DEL EXPOSITOR — DASHBOARD
# ============================================================
@expositor_requerido
def panel_expositor(request):
    perfil = request.user.perfil
    expositor = perfil.expositor

    if not expositor:
        messages.error(request, 'Tu cuenta no tiene un expositor vinculado. Contacta al administrador.')
        return redirect('core:index')

    # ¿Perfil incompleto?
    campos_requeridos = [
        expositor.nombre_empresa and expositor.nombre_empresa != 'Por definir',
        expositor.nombre_expositor,
        expositor.email_contacto,
        expositor.numero_contacto,
        expositor.descripcion,
        expositor.menu_completo,
        expositor.categoria,
    ]
    perfil_incompleto = not all(campos_requeridos)

    contexto = {
        'expositor': expositor,
        'perfil_incompleto': perfil_incompleto,
        'n_productos': expositor.productos.count(),
        'n_fotos': expositor.fotos.count(),
        'n_activos': expositor.productos.filter(disponible=True).count(),
    }
    return render(request, 'accounts/panel_expositor.html', contexto)


# ============================================================
#  REGISTRO COMPLETO (todos los campos del modelo)
# ============================================================
@expositor_requerido
def expositor_registro_completo(request):
    expositor = request.user.perfil.expositor

    if not expositor:
        messages.error(request, 'Tu cuenta no tiene un expositor vinculado.')
        return redirect('core:index')

    if request.method == 'POST':
        form = ExpositorForm(request.POST, request.FILES, instance=expositor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos guardados. Ya puedes enviar tu solicitud.')
            return redirect('accounts:panel_expositor')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = ExpositorForm(instance=expositor)

    return render(request, 'accounts/expositor_registro.html', {
        'expositor': expositor,
        'form': form,
    })


# ============================================================
#  ENVIAR SOLICITUD DE PUBLICACIÓN
# ============================================================
@expositor_requerido
def expositor_enviar_solicitud(request):
    if request.method != 'POST':
        return redirect('accounts:panel_expositor')

    expositor = request.user.perfil.expositor

    # Validar que esté completo
    if not all([
        expositor.nombre_empresa and expositor.nombre_empresa != 'Por definir',
        expositor.nombre_expositor,
        expositor.email_contacto,
        expositor.numero_contacto,
        expositor.descripcion,
        expositor.menu_completo,
        expositor.categoria,
    ]):
        messages.error(request, 'Completa todos los datos requeridos antes de enviar tu solicitud.')
        return redirect('accounts:expositor_registro_completo')

    expositor.estado_solicitud = 'pendiente'
    expositor.fecha_envio = timezone.now()
    expositor.activo = False
    expositor.save(update_fields=['estado_solicitud', 'fecha_envio', 'activo'])

    messages.success(
        request,
        '¡Solicitud enviada! El equipo del festival la revisará pronto.'
    )
    return redirect('accounts:panel_expositor')


# ============================================================
#  PRODUCTOS DEL EXPOSITOR
# ============================================================
@expositor_requerido
def expositor_productos(request):
    expositor = request.user.perfil.expositor
    productos = expositor.productos.all().order_by('categoria', 'nombre')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.expositor = expositor
            producto.save()
            expositor.recalcular_precio_desde()
            messages.success(request, f'Producto "{producto.nombre}" añadido.')
            return redirect('accounts:expositor_productos')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'accounts/expositor_productos.html', {
        'expositor': expositor,
        'productos': productos,
        'form': form,
    })


@expositor_requerido
def expositor_producto_delete(request, prod_pk):
    expositor = request.user.perfil.expositor
    producto = get_object_or_404(Producto, pk=prod_pk, expositor=expositor)
    nombre = producto.nombre
    producto.delete()
    expositor.recalcular_precio_desde()
    messages.success(request, f'Producto "{nombre}" eliminado.')
    return redirect('accounts:expositor_productos')


# ============================================================
#  FOTOS DEL EXPOSITOR
# ============================================================
@expositor_requerido
def expositor_fotos(request):
    expositor = request.user.perfil.expositor
    fotos = expositor.fotos.all()

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
        return redirect('accounts:expositor_fotos')

    return render(request, 'accounts/expositor_fotos.html', {
        'expositor': expositor,
        'fotos': fotos,
    })


@expositor_requerido
def expositor_foto_delete(request, foto_pk):
    expositor = request.user.perfil.expositor
    foto = get_object_or_404(FotoProducto, pk=foto_pk, expositor=expositor)
    foto.delete()
    messages.success(request, 'Foto eliminada.')
    return redirect('accounts:expositor_fotos')


@expositor_requerido
def expositor_logo_delete(request):
    expositor = request.user.perfil.expositor
    if expositor.logo:
        expositor.logo.delete(save=True)
        messages.success(request, 'Logo eliminado.')
    return redirect('accounts:expositor_registro_completo')