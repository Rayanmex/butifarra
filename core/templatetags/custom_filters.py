from django import template

register = template.Library()


@register.filter
def split(value, arg):
    """Divide una cadena por un separador. Uso: {{ "a,b,c"|split:"," }}"""
    return value.split(arg)