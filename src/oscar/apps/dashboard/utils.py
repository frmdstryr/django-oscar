"""
Taken from the awesome django-xadmin
"""
from django.db import models


def is_rel_field(name, model):
    if hasattr(name, 'split') and name.find("__") > 0:
        parts = name.split("__")
        if parts[0] in (f.name for f in model._meta.get_fields()):
            return True
    return False


def lookup_field(name, obj, model_admin=None):
    opts = obj._meta
    try:
        f = opts.get_field(name)
    except models.FieldDoesNotExist:
        # For non-field values, the value is either a method, property or
        # returned via a callable.
        if callable(name):
            attr = name
            value = attr(obj)
        elif (
                model_admin is not None
                and hasattr(model_admin, name)
                and name not in ('__str__', '__unicode__')
        ):
            attr = getattr(model_admin, name)
            value = attr(obj)
        else:
            if is_rel_field(name, obj):
                parts = name.split("__")
                rel_name, sub_rel_name = parts[0], "__".join(parts[1:])
                rel_obj = getattr(obj, rel_name)
                if rel_obj is not None:
                    return lookup_field(sub_rel_name, rel_obj, model_admin)
            attr = getattr(obj, name)
            if callable(attr):
                value = attr()
            else:
                value = attr
        f = None
    else:
        attr = None
        value = getattr(obj, name)
    return f, attr, value
