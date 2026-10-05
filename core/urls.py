from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ============ PÁGINAS PÚBLICAS ============
    path('', views.index, name='index'),
    path('contacto/', views.contacto, name='contacto'),
    path('historia/', views.historia, name='historia'),
    path('programa/', views.programa, name='programa'),

    # Productores (redirige al catálogo)
    path('productores/', views.productores, name='productores'),

    # Expositores (público)
    path('expositores/', views.expositores_list, name='expositores_list'),
    path('expositores/<int:pk>/', views.expositor_detail, name='expositor_detail'),

    # ============ PANEL DE CONTROL (requiere login) ============
    # Dashboard
    path('panel/', views.panel_dashboard, name='panel_dashboard'),

    # ===== Solicitudes (revisión por admin) =====
    path(
        'panel/solicitudes/',
        views.panel_solicitudes,
        name='panel_solicitudes'
    ),
    path(
        'panel/solicitudes/<int:pk>/',
        views.panel_solicitud_detalle,
        name='panel_solicitud_detalle'
    ),

    # ===== Gestión de Usuarios (expositores) =====
    path(
        'panel/usuarios/',
        views.panel_usuarios,
        name='panel_usuarios'
    ),
    path(
        'panel/usuarios/nuevo/',
        views.panel_usuario_create,
        name='panel_usuario_create'
    ),
    path(
        'panel/usuarios/<int:pk>/editar/',
        views.panel_usuario_edit,
        name='panel_usuario_edit'
    ),
    path(
        'panel/usuarios/<int:pk>/reset-password/',
        views.panel_usuario_reset_password,
        name='panel_usuario_reset_password'
    ),
    path(
        'panel/usuarios/<int:pk>/toggle-activo/',
        views.panel_usuario_toggle_activo,
        name='panel_usuario_toggle_activo'
    ),

    # ===== Comentarios del admin =====
    path(
        'panel/comentarios/<int:pk>/',
        views.panel_comentarios,
        name='panel_comentarios'
    ),

    # ===== Expositores =====
    path(
        'panel/expositores/',
        views.panel_expositores,
        name='panel_expositores'
    ),
    path(
        'panel/expositores/<int:pk>/',
        views.panel_expositor_detail,
        name='panel_expositor_detail'
    ),
    path(
        'panel/expositores/<int:pk>/editar/',
        views.panel_expositor_edit,
        name='panel_expositor_edit'
    ),
    path(
        'panel/expositores/<int:pk>/toggle-activo/',
        views.panel_toggle_activo,
        name='panel_toggle_activo'
    ),
    path(
        'panel/expositores/<int:pk>/toggle-destacado/',
        views.panel_toggle_destacado,
        name='panel_toggle_destacado'
    ),

    # ===== Logo =====
    path(
        'panel/expositores/<int:pk>/logo/eliminar/',
        views.panel_logo_delete,
        name='panel_logo_delete'
    ),

    # ===== Fotos de productos =====
    path(
        'panel/expositores/<int:pk>/fotos/subir/',
        views.panel_foto_upload,
        name='panel_foto_upload'
    ),
    path(
        'panel/fotos/<int:foto_pk>/eliminar/',
        views.panel_foto_delete,
        name='panel_foto_delete'
    ),

    # ===== Productos del menú =====
    path(
        'panel/expositores/<int:pk>/productos/nuevo/',
        views.panel_producto_create,
        name='panel_producto_create'
    ),
    path(
        'panel/expositores/<int:pk>/importar-menu/',
        views.panel_importar_menu,
        name='panel_importar_menu'
    ),
    path(
        'panel/productos/<int:prod_pk>/editar/',
        views.panel_producto_edit,
        name='panel_producto_edit'
    ),
    path(
        'panel/productos/<int:prod_pk>/eliminar/',
        views.panel_producto_delete,
        name='panel_producto_delete'
    ),

    # ===== Edición masiva de logos =====
    path(
        'panel/logos/',
        views.panel_logos_bulk,
        name='panel_logos_bulk'
    ),
]