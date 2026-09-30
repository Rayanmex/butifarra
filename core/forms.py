from django import forms
from .models import Expositor, Producto, FotoProducto


class ExpositorForm(forms.ModelForm):
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
                               '1 kilo de longaniza casera - $250\n'
                               'Medio kilo de queso de puerco - $180',
                'class': 'form-control'
            }),
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
            'es_destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductoForm(forms.ModelForm):
    """Formulario para crear/editar productos del menú."""
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