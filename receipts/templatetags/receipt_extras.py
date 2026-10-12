from django import template

register = template.Library()


@register.filter
def rub(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    formatted = f'{number:,.2f}'.replace(',', ' ').replace('.', ',')
    if formatted.endswith(',00'):
        formatted = formatted[:-3]
    return f'{formatted} ₽'
