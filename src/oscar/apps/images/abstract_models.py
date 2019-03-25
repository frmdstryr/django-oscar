from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.images.models import AbstractImage, AbstractRendition


class AbstractOscarImage(AbstractImage):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'tags',
        'focal_point_x',
        'focal_point_y',
        'focal_point_width',
        'focal_point_height',
    )

    class Meta:
        abstract = True
        verbose_name = _('image')
        verbose_name_plural = _('images')


class AbstractOscarRendition(AbstractRendition):
    image = models.ForeignKey(
        'images.OscarImage',
        on_delete=models.CASCADE,
        related_name='renditions')

    class Meta:
        abstract = True
