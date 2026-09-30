from django.contrib import admin
from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'expositor', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'activo')
    search_fields = ('user__username', 'user__email', 'expositor__nombre_empresa')
    autocomplete_fields = ['expositor']
    list_editable = ('rol', 'activo')