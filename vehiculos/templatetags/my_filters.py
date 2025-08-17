from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary[key]
    except (KeyError, TypeError):
        return None

@register.filter
def dict_get_item(d, key):
    try:
        return d[key]
    except (KeyError, TypeError):
        return None


@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def percentage(value, total):
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0