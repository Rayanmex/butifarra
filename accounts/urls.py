from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),

    # Panel del expositor
    path('panel/', views.panel_expositor, name='panel_expositor'),
    path('panel/registro/', views.expositor_registro_completo, name='expositor_registro_completo'),
    path('panel/enviar-solicitud/', views.expositor_enviar_solicitud, name='expositor_enviar_solicitud'),
    path('panel/productos/', views.expositor_productos, name='expositor_productos'),
    path('panel/productos/<int:prod_pk>/eliminar/', views.expositor_producto_delete, name='expositor_producto_delete'),
    path('panel/fotos/', views.expositor_fotos, name='expositor_fotos'),
    path('panel/fotos/<int:foto_pk>/eliminar/', views.expositor_foto_delete, name='expositor_foto_delete'),
    path('panel/logo/eliminar/', views.expositor_logo_delete, name='expositor_logo_delete'),
]