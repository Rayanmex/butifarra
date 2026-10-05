from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from .models import Expositor, Producto, FotoProducto, ComentarioAdmin


# =============================================================
#  EXPOSITOR (panel propio)
# =============================================================

class ExpositorForm(forms.ModelForm):
    """
    Formulario del EXPOSITOR.
    NO incluye 'menu_completo' ni 'es_destacado' ni 'activo'.
    El expositor siempre puede editar — los cambios se guardan como
    CambioPendiente hasta que el admin apruebe.
    """
    class Meta:
        model = Expositor
        fields = [
            'nombre_expositor', 'nombre_empresa', 'logo',
            'email_contacto', 'numero_contacto', 'numero_stand',
            'categoria', 'descripcion', 'especialidades',
            'enlace_red_social_1', 'enlace_red_social_2', 'redes_sociales_texto',
            'acepta_tarjeta', 'acepta_efectivo',
            'link_google_maps', 'direccion_negocio',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'Ej: Butifarras artesanales de la familia Pérez, desde 1985.'
            }),
            'especialidades': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'crema de ajo, mango habanero, BBQ'
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre_expositor': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'numero_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_stand': forms.TextInput(attrs={'class': 'form-control'}),
            'enlace_red_social_1': forms.URLInput(attrs={'class': 'form-control'}),
            'enlace_red_social_2': forms.URLInput(attrs={'class': 'form-control'}),
            'redes_sociales_texto': forms.TextInput(attrs={'class': 'form-control'}),
            'link_google_maps': forms.URLInput(attrs={'class': 'form-control'}),
            'direccion_negocio': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'acepta_tarjeta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'acepta_efectivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================
#  EXPOSITOR (panel admin — edición directa)
# =============================================================

class ExpositorAdminForm(forms.ModelForm):
    """
    Formulario del ADMIN.
    Incluye 'menu_completo', 'es_destacado' y 'activo'.
    """
    class Meta:
        model = Expositor
        fields = [
            'nombre_expositor', 'nombre_empresa', 'logo',
            'email_contacto', 'numero_contacto', 'numero_stand',
            'categoria', 'descripcion', 'especialidades',
            'enlace_red_social_1', 'enlace_red_social_2', 'redes_sociales_texto',
            'menu_completo', 'acepta_tarjeta', 'acepta_efectivo',
            'link_google_maps', 'direccion_negocio',
            'es_destacado', 'activo',
        ]
        widgets = {
            'menu_completo': forms.Textarea(attrs={
                'rows': 10,
                'placeholder': '1 kilo de butifarra tradicional - $350\n'
                               '1 kilo de longaniza casera - $250',
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
            }),
            'especialidades': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre_expositor': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'numero_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_stand': forms.TextInput(attrs={'class': 'form-control'}),
            'enlace_red_social_1': forms.URLInput(attrs={'class': 'form-control'}),
            'enlace_red_social_2': forms.URLInput(attrs={'class': 'form-control'}),
            'redes_sociales_texto': forms.TextInput(attrs={'class': 'form-control'}),
            'link_google_maps': forms.URLInput(attrs={'class': 'form-control'}),
            'direccion_negocio': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'acepta_tarjeta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'acepta_efectivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================
#  PRODUCTO / FOTO
# =============================================================

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'unidad', 'precio', 'descripcion', 'disponible']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1 kilo de butifarra tradicional'
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '350.00',
                'step': '0.01',
                'min': '0'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opcional'
            }),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del producto',
            'categoria': 'Categoría',
            'unidad': 'Unidad de venta',
            'precio': 'Precio ($)',
            'descripcion': 'Descripción',
            'disponible': 'Disponible en el festival',
        }


class FotoProductoForm(forms.ModelForm):
    class Meta:
        model = FotoProducto
        fields = ['imagen', 'descripcion']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Butifarra tradicional en exhibición'
            }),
        }


# =============================================================
#  REVISIÓN DE SOLICITUD (admin)
# =============================================================

class RevisionSolicitudForm(forms.Form):
    ACCIONES = [
        ('aprobar', 'Aprobar y publicar'),
        ('observar', 'Hacer observaciones'),
        ('rechazar', 'Rechazar'),
    ]

    accion = forms.ChoiceField(
        choices=ACCIONES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Decisión'
    )
    comentario = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explica brevemente tu decisión. El expositor verá este texto.'
        }),
        label='Comentario / Observaciones'
    )

    def clean(self):
        cleaned = super().clean()
        accion = cleaned.get('accion')
        comentario = (cleaned.get('comentario') or '').strip()

        if accion in ('observar', 'rechazar') and not comentario:
            raise forms.ValidationError(
                'Debes escribir un comentario si vas a observar o rechazar la solicitud.'
            )
        return cleaned


# =============================================================
#  GESTIÓN DE USUARIOS (admin)
# =============================================================

class CrearUsuarioExpositorForm(forms.Form):
    """
    Formulario del ADMIN para crear un nuevo usuario expositor.
    Crea User + Expositor + PerfilUsuario en una transacción atómica.
    """

    # === Datos del User ===
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre (opcional)'
        })
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la contraseña'
        })
    )

    # === Datos básicos del Expositor ===
    nombre_empresa = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Butifarras "El Buen Sabor"'
        })
    )
    nombre_expositor = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez'
        })
    )
    numero_contacto = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '914 123 4567'
        })
    )

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ese correo ya está registrado.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def save(self):
        """Crea User + Expositor + PerfilUsuario."""
        # Import aquí adentro para evitar import circular
        from accounts.models import PerfilUsuario

        data = self.cleaned_data

        with transaction.atomic():
            # 1) User
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password1'],
                first_name=data.get('first_name') or '',
                is_active=True,
            )

            # 2) Expositor (estado inicial = borrador)
            expositor = Expositor.objects.create(
                nombre_empresa=data.get('nombre_empresa') or 'Por definir',
                nombre_expositor=data.get('nombre_expositor') or None,
                email_contacto=data['email'],
                numero_contacto=data.get('numero_contacto') or None,
                categoria='tradicional',
                activo=True,
                estado_solicitud='borrador',
            )

            # 3) Perfil
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rol = 'expositor'
            perfil.expositor = expositor
            perfil.telefono = data.get('numero_contacto') or ''
            perfil.save()

        return user


class ResetPasswordForm(forms.Form):
    """Formulario del ADMIN para resetear la contraseña de un usuario."""
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la contraseña'
        })
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned


class ComentarioAdminForm(forms.ModelForm):
    """Formulario del ADMIN para agregar un comentario al historial."""
    class Meta:
        model = ComentarioAdmin
        fields = ['tipo', 'texto']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe un comentario para el expositor...'
            }),
        }