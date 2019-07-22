from oscar.apps.shipping import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered('shipping', 'Method'):
    class Method(abstract_models.AbstractMethod):
        pass

    __all__.append('Method')
else:
    Method = get_model('shipping', 'Method')


if not is_model_registered('shipping', 'OrderAndItemCharges'):
    class OrderAndItemCharges(Method, abstract_models.AbstractOrderAndItemCharges):
        pass

    __all__.append('OrderAndItemCharges')


if not is_model_registered('shipping', 'WeightBased'):
    class WeightBased(Method, abstract_models.AbstractWeightBased):
        pass

    __all__.append('WeightBased')


if not is_model_registered('shipping', 'WeightBand'):
    class WeightBand(abstract_models.AbstractWeightBand):
        pass

    __all__.append('WeightBand')
