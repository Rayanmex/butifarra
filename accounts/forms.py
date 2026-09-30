from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import PerfilUsuario
from core.models import Expositor


from core.forms import Expositor, ProductoForm, FotoProductoForm  # noqa


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input-custom',
            'placeholder': 'Usuario o correo',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-input-custom',
            'placeholder': 'Contraseña',
        })
    )


class RegistroExpositorForm(forms.Form):
    """Registro para un nuevo expositor."""

    # === Datos del User ===
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )
    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'})
    )

    # === Datos del Expositor ===
    nombre_expositor = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez'})
    )
    nombre_empresa = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Butifarras "El Buen Sabor"'})
    )
    numero_contacto = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '914 123 4567'})
    )
    categoria = forms.ChoiceField(
        choices=Expositor.CATEGORIA_CHOICES,
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
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '1 kilo de butifarra tradicional - $350\n1 kilo de longaniza - $250'
        })
    )

    # === Validaciones ===
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
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
        data = self.cleaned_data

        # 1) User
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password1'],
        )

        # 2) Expositor
        expositor = Expositor.objects.create(
            nombre_expositor=data['nombre_expositor'],
            nombre_empresa=data['nombre_empresa'],
            email_contacto=data['email'],
            numero_contacto=data['numero_contacto'],
            categoria=data['categoria'],
            descripcion=data.get('descripcion', ''),
            menu_completo=data['menu_completo'],
            activo=True,
        )

        # 3) Perfil
        perfil = user.perfil
        perfil.rol = 'expositor'
        perfil.expositor = expositor
        perfil.telefono = data['numero_contacto']
        perfil.save()

        return user