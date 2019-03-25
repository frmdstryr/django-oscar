from oscar.apps.images.abstract_models import (
    AbstractOscarImage, AbstractOscarRendition,
)
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('images', 'OscarImage'):
    class OscarImage(AbstractOscarImage):
        pass

    __all__.append('OscarImage')


if not is_model_registered('images', 'OscarRendition'):
    class OscarRendition(AbstractOscarRendition):
        class Meta:
            unique_together = ('image', 'filter_spec', 'focal_point_key')

    __all__.append('OscarRendition')
