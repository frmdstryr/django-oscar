from django import template

register = template.Library()


@register.filter
def split(value, separator=' '):
    return value.split(separator)


@register.filter
def underscore_to_space(value):
    return value.replace("_", " ")
