from django import template

register = template.Library()


@register.simple_tag
def payment_charge(method, basket, order_total):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.calculate(basket, order_total)

