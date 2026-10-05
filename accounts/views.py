from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import os

from .forms import LoginForm, RegistroExpositorForm
from core.forms import ExpositorForm, ProductoForm
from .decorators import admin_requerido, expositor_requerido
from .models import PerfilUsuario
from core.models import Expositor, Producto, FotoProducto, CambioPendiente, ComentarioAdmin


# ============================================================
#  UTILIDADES INTERNAS
# ============================================================

def _obtener_o_crear_cambio(expositor):
    """
    Devuelve el CambioPendiente activo del expositor, o crea uno nuevo vacío.
    Si ya existe, lo devuelve tal cual (se sobreescribirá su contenido).
    """
    cambio, _ = CambioPendiente.objects.get_or_create(
        expositor=expositor,
        defaults={'datos': {'expositor': {}, 'operaciones': []}}
    )
    if 'expositor' not in cambio.datos:
        cambio.datos['expositor'] = {}
    if 'operaciones' not in cambio.datos:
        cambio.datos['operaciones'] = []
    return cambio


def _guardar_campo_cambio(expositor, campo, valor):
    """Añade/actualiza un campo del expositor en el CambioPendiente."""
    cambio = _obtener_o_crear_cambio(expositor)
    cambio.datos['expositor'][campo] = valor
    cambio.estado = 'pendiente'
    cambio.save()

    # Actualizar estado del expositor si estaba aprobado
    if expositor.estado_solicitud == 'aprobado':
        expositor.estado_solicitud = 'revision_pendiente'
        expositor.save(update_fields=['estado_solicitud'])


def _guardar_operacion(expositor, operacion):
    """Añade una operación (producto/foto) al CambioPendiente."""
    cambio = _obtener_o_crear_cambio(expositor)
    cambio.datos['operaciones'].append(operacion)
    cambio.estado = 'pendiente'
    cambio.save()

    if expositor.estado_solicitud == 'aprobado':
        expositor.estado_solicitud = 'revision_pendiente'
        expositor.save(update_fields=['estado_solicitud'])


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
        messages.error(
            request,
            'Tu cuenta no tiene un expositor vinculado. Contacta al administrador.'
        )
        return redirect('core:index')

    cambio = getattr(expositor, 'cambio_pendiente', None)
    comentarios = expositor.comentarios_admin.all()[:5]
    comentarios_no_leidos = expositor.comentarios_admin.filter(leido=False).count()

    contexto = {
        'expositor': expositor,
        'perfil_incompleto': not expositor.campos_requeridos_completos,
        'puede_editar': expositor.puede_editar,
        'cambio': cambio,
        'comentarios': comentarios,
        'comentarios_no_leidos': comentarios_no_leidos,
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
            # Guardamos los cambios en el CambioPendiente
            cambio = _obtener_o_crear_cambio(expositor)

            # Recorremos los campos del formulario
            for campo, valor in form.cleaned_data.items():
                if campo == 'logo':
                    # El logo se sube físicamente y se referencia
                    if valor:
                        expositor.logo = valor
                        expositor.save(update_fields=['logo'])
                        cambio.datos['expositor']['logo'] = str(valor)
                    continue
                # Convertir a JSON serializable
                if hasattr(valor, 'pk'):
                    valor = valor.pk
                elif valor is None or isinstance(valor, (str, int, float, bool)):
                    pass
                else:
                    valor = str(valor)
                cambio.datos['expositor'][campo] = valor

            cambio.estado = 'pendiente'
            cambio.save()

            # Actualizar estado del expositor si estaba aprobado
            if expositor.estado_solicitud == 'aprobado':
                expositor.estado_solicitud = 'revision_pendiente'
                expositor.save(update_fields=['estado_solicitud'])

            messages.success(
                request,
                'Cambios guardados. El administrador los revisará pronto.'
            )
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
    """
    Envía la solicitud (o los cambios pendientes) al admin para revisión.
    Como ahora todos los cambios se guardan como CambioPendiente,
    esta vista solo confirma al usuario.
    """
    if request.method != 'POST':
        return redirect('accounts:panel_expositor')

    expositor = request.user.perfil.expositor

    if not expositor:
        messages.error(request, 'Tu cuenta no tiene un expositor vinculado.')
        return redirect('core:index')

    if not expositor.campos_requeridos_completos:
        messages.error(
            request,
            'Completa todos los datos requeridos antes de enviar tu solicitud.'
        )
        return redirect('accounts:expositor_registro_completo')

    # Si no existe cambio pendiente, creamos uno vacío para marcar el envío
    cambio = _obtener_o_crear_cambio(expositor)
    cambio.estado = 'pendiente'
    cambio.save()

    if expositor.estado_solicitud in ('borrador', 'observado'):
        expositor.estado_solicitud = 'pendiente'
    elif expositor.estado_solicitud == 'aprobado':
        expositor.estado_solicitud = 'revision_pendiente'

    expositor.fecha_envio = timezone.now()
    expositor.nota_admin = ''
    expositor.save(update_fields=[
        'estado_solicitud', 'fecha_envio', 'nota_admin'
    ])

    messages.success(
        request,
        '¡Solicitud enviada! El equipo del festival la revisará pronto.'
    )
    return redirect('accounts:panel_expositor')


# ============================================================
#  PRODUCTOS DEL EXPOSITOR — LISTA + CREAR
# ============================================================
@expositor_requerido
def expositor_productos(request):
    expositor = request.user.perfil.expositor
    productos = expositor.productos.all().order_by('categoria', 'nombre')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data.copy()
            if hasattr(datos.get('precio'), 'quantize'):
                datos['precio'] = str(datos['precio'])
            _guardar_operacion(expositor, {
                'tipo': 'producto_crear',
                'datos': datos,
            })
            messages.success(
                request,
                f'Producto "{datos["nombre"]}" enviado para aprobación.'
            )
            return redirect('accounts:expositor_productos')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'accounts/expositor_productos.html', {
        'expositor': expositor,
        'productos': productos,
        'form': form,
        'puede_editar': True,
    })


# ============================================================
#  PRODUCTOS DEL EXPOSITOR — EDITAR
# ============================================================
@expositor_requerido
def expositor_producto_edit(request, prod_pk):
    expositor = request.user.perfil.expositor
    producto = get_object_or_404(Producto, pk=prod_pk, expositor=expositor)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            datos = form.cleaned_data.copy()
            if hasattr(datos.get('precio'), 'quantize'):
                datos['precio'] = str(datos['precio'])
            _guardar_operacion(expositor, {
                'tipo': 'producto_editar',
                'producto_id': producto.pk,
                'datos': datos,
            })
            messages.success(
                request,
                f'Cambios del producto "{producto.nombre}" enviados para aprobación.'
            )
            return redirect('accounts:expositor_productos')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'accounts/expositor_producto_form.html', {
        'expositor': expositor,
        'producto': producto,
        'form': form,
        'modo': 'editar',
    })


# ============================================================
#  PRODUCTOS DEL EXPOSITOR — ELIMINAR
# ============================================================
@expositor_requerido
def expositor_producto_delete(request, prod_pk):
    expositor = request.user.perfil.expositor
    producto = get_object_or_404(Producto, pk=prod_pk, expositor=expositor)
    nombre = producto.nombre

    _guardar_operacion(expositor, {
        'tipo': 'producto_eliminar',
        'producto_id': producto.pk,
    })

    messages.success(
        request,
        f'Eliminación del producto "{nombre}" enviada para aprobación.'
    )
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
            # Guardamos la imagen físicamente pero NO la asociamos al Expositor
            # hasta que el admin apruebe. Solo registramos la operación.
            foto_temp = FotoProducto.objects.create(
                expositor=expositor,
                imagen=f,
                descripcion=descripcion,
            )
            _guardar_operacion(expositor, {
                'tipo': 'foto_agregar',
                'foto_id': foto_temp.pk,
                'datos': {'descripcion': descripcion},
            })
            subidas += 1

        if subidas:
            messages.success(
                request,
                f'{subidas} foto(s) enviadas para aprobación.'
            )
        else:
            messages.warning(request, 'No se subió ninguna foto.')
        return redirect('accounts:expositor_fotos')

    return render(request, 'accounts/expositor_fotos.html', {
        'expositor': expositor,
        'fotos': fotos,
        'puede_editar': True,
    })


@expositor_requerido
def expositor_foto_delete(request, foto_pk):
    expositor = request.user.perfil.expositor
    foto = get_object_or_404(FotoProducto, pk=foto_pk, expositor=expositor)

    _guardar_operacion(expositor, {
        'tipo': 'foto_eliminar',
        'foto_id': foto.pk,
    })

    messages.success(request, 'Eliminación de foto enviada para aprobación.')
    return redirect('accounts:expositor_fotos')


# ============================================================
#  LOGO DEL EXPOSITOR
# ============================================================
@expositor_requerido
def expositor_logo_delete(request):
    expositor = request.user.perfil.expositor

    if expositor.logo:
        _guardar_campo_cambio(expositor, 'logo', '')
        messages.success(request, 'Eliminación del logo enviada para aprobación.')
    return redirect('accounts:expositor_registro_completo')