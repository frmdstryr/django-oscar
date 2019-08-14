from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from oscar.core.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel,
    TabbedInterface, ObjectList, AutocompletePanel, ModelChooserPanel
)
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.images.edit_handlers import ImageChooserPanel

class AbstractConfiguration(BaseSetting):
    """ System configuration

    """
    shop_name = models.CharField(max_length=64)
    shop_tagline = models.CharField(max_length=256)
    shop_phone_number = PhoneNumberField(default="1-800-799-9999")
    shop_email = models.EmailField(default="sales@example.com")

    shop_logo = models.ForeignKey(
        'images.OscarImage', null=True, on_delete=models.PROTECT,
        related_name='+', help_text=_("Logo used on light backgrounds"))
    shop_logo_alt = models.ForeignKey(
        'images.OscarImage', null=True, on_delete=models.PROTECT,
        related_name='+', help_text=_("Logo used on dark backgrounds"))
    shop_logo_print = models.ForeignKey(
        'images.OscarImage', null=True, on_delete=models.PROTECT,
        related_name='+', help_text=_("Logo used on print media"))
    shop_banner = models.ForeignKey(
        'images.OscarImage', null=True, on_delete=models.PROTECT,
        related_name='+', help_text=_("Banner imaged used by templates"))

    homepage_url = models.CharField(max_length=256, default='/')

    #: Use css by default
    use_less = models.BooleanField(default=False)

    #: Analytics ID
    google_analytics_id = models.CharField(max_length=256, blank=True,
                                           null=True)

    #: Date formats for dashboard and UI
    shop_date_format = models.CharField(max_length=32, default="yy-mm-dd")
    shop_time_format = models.CharField(max_length=32, default="hh:ii")
    shop_datetime_format = models.CharField(
        max_length=32,
        default="yy-mm-dd hh:ii"
    )

    shop_panels = [
        FieldPanel('shop_name'),
        FieldPanel('shop_tagline'),
        FieldPanel('shop_phone_number'),
        FieldPanel('shop_email'),
        FieldPanel('homepage_url'),
    ]

    theme_panels = [
        ImageChooserPanel('shop_logo'),
        ImageChooserPanel('shop_logo_alt'),
        ImageChooserPanel('shop_logo_print'),
        ImageChooserPanel('shop_banner'),
    ]

    config_panels = [
        FieldPanel('google_analytics_id'),
        FieldRowPanel([
            FieldPanel('shop_date_format'),
            FieldPanel('shop_time_format'),
            FieldPanel('shop_datetime_format'),
        ], heading=_('Dates')),
    ]

    edit_handler = TabbedInterface([
        ObjectList(shop_panels, heading=_('Shop')),
        ObjectList(theme_panels, heading=_('Theme')),
        ObjectList(config_panels, heading=_('Config')),
    ])

    class Meta:
        abstract = True
        app_label = 'system'
        verbose_name = _("Configuration")

