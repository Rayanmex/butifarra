from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('expositor', 'Expositor'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default='expositor',
        verbose_name='Rol'
    )
    # Enlace al expositor cuando el rol es 'expositor'
    expositor = models.OneToOneField(
        'core.Expositor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_usuario',
        verbose_name='Expositor vinculado'
    )
    telefono = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f"{self.user.username} · {self.get_rol_display()}"

    # Helpers
    def es_admin(self):
        return self.rol == 'admin'

    def es_expositor(self):
        return self.rol == 'expositor'


@receiver(post_save, sender=User)
def crear_perfil_automatico(sender, instance, created, **kwargs):
    """Crea automáticamente un PerfilUsuario al crear un User."""
    if created:
        PerfilUsuario.objects.get_or_create(user=instance)