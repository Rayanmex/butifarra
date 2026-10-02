from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction

from .models import PerfilUsuario
from core.models import Expositor

# Reexports por si otro módulo los importaba desde aquí
from core.forms import ProductoForm, FotoProductoForm  # noqa


class LoginForm(AuthenticationForm):
    """
    Acepta 'usuario' o 'correo electrónico' indistintamente.
    Si el valor contiene '@' y existe un User con ese email,
    lo convertimos a su username antes de autenticar.
    """
    username = forms.CharField(
        label='Usuario o correo',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input-custom',
            'placeholder': 'Usuario o correo',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-input-custom',
            'placeholder': 'Contraseña',
        })
    )

    def clean_username(self):
        valor = (self.cleaned_data.get('username') or '').strip()
        if '@' in valor:
            user = User.objects.filter(email__iexact=valor).first()
            if user:
                return user.username
        return valor


class RegistroExpositorForm(forms.Form):
    """
    Registro para un nuevo expositor.
    Solo pide datos de acceso + los mínimos para crear el Expositor.
    El resto se completa desde el panel (expositor_registro_completo).
    """

    # === Datos del User (OBLIGATORIOS) ===
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

    # === Datos del Expositor (OPCIONALES) ===
    nombre_expositor = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez'
        })
    )
    nombre_empresa = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Butifarras "El Buen Sabor"'
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
    categoria = forms.ChoiceField(
        choices=Expositor.CATEGORIA_CHOICES,
        required=False,
        initial='tradicional',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Cuéntanos sobre tu negocio (opcional)'
        })
    )
    menu_completo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '1 kilo de butifarra tradicional - $350\n1 kilo de longaniza - $250'
        })
    )

    # === Validaciones ===
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

    @transaction.atomic
    def save(self):
        """
        Crea User + Expositor + PerfilUsuario de forma atómica.
        Los campos opcionales del Expositor se llenan con defaults
        si vienen vacíos, para que el modelo no reviente.
        """
        data = self.cleaned_data

        # 1) User
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password1'],
        )

        # 2) Expositor (estado inicial = borrador)
        expositor = Expositor.objects.create(
            nombre_expositor=data.get('nombre_expositor') or None,
            nombre_empresa=data.get('nombre_empresa') or 'Por definir',
            email_contacto=data['email'],
            numero_contacto=data.get('numero_contacto') or None,
            categoria=data.get('categoria') or 'tradicional',
            descripcion=data.get('descripcion') or '',
            menu_completo=data.get('menu_completo') or '',
            activo=True,
            estado_solicitud='borrador',
        )

        # 3) Perfil (el signal pudo crearlo ya)
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.rol = 'expositor'
        perfil.expositor = expositor
        perfil.telefono = data.get('numero_contacto') or ''
        perfil.save()

        return user