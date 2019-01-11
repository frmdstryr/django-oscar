from django import template

from oscar.core.loading import get_class


register = template.Library()


@register.simple_tag
def dashboard_navigation(user):
    get_nodes = get_class('dashboard.menu', 'get_nodes')
    return get_nodes(user)
