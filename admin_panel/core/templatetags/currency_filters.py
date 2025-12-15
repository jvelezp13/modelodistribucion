"""
Filtros de template para formato de moneda colombiana
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def peso_colombiano(value):
    """
    Formatea un número como peso colombiano: $1.234.567
    Usa puntos como separador de miles (formato colombiano)
    """
    if value is None:
        return "-"

    try:
        # Convertir a número
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        num = float(value)

        # Redondear a entero
        num = round(num)

        # Formatear con puntos como separador de miles
        formatted = f"{num:,.0f}".replace(",", ".")

        return f"${formatted}"
    except (ValueError, TypeError):
        return "-"


@register.filter
def numero_miles(value):
    """
    Formatea un número con separador de miles (puntos): 1.234.567
    Sin símbolo de moneda
    """
    if value is None:
        return "-"

    try:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        num = float(value)
        num = round(num)
        return f"{num:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"
