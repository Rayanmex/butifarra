from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def rol_requerido(*roles_permitidos):
    """
    Uso:
        @rol_requerido('admin')
        @rol_requerido('expositor')
        @rol_requerido('admin', 'expositor')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='accounts:login')
        def _wrapped(request, *args, **kwargs):
            perfil = getattr(request.user, 'perfil', None)

            # Superusuario siempre pasa como admin
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not perfil or not perfil.activo:
                messages.error(request, 'Tu cuenta no tiene un perfil válido.')
                return redirect('accounts:login')

            if perfil.rol not in roles_permitidos:
                messages.error(request, 'No tienes permiso para acceder a esa sección.')
                return redirect('accounts:dashboard_redirect')

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# Atajos
admin_requerido = rol_requerido('admin')
expositor_requerido = rol_requerido('expositor')