from django import template

register = template.Library()


@register.simple_tag
def shipping_charge(method, basket):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.calculate(basket)


@register.simple_tag
def shipping_charge_discount(method, basket):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.discount(basket)


@register.simple_tag
def shipping_charge_excl_discount(method, basket):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return method.calculate_excl_discount(basket)


@register.simple_tag
def shipping_distance(method, address):
    """
    Template tag for getting options nearby the provided address.
    """
    return method.distance(address)


@register.simple_tag
def shipping_miles(distance):
    """
    Convert km to miles and round it
    """
    if not isinstance(distance, float):
        print(distance)
        return ''
    d = distance * 0.6213712
    if d < 5:
        return "less than 5"
    if d > 100:
        return 10 * round(d/10)
    return 5 * round(d/5)
