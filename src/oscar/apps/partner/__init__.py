from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PartnerConfig(AppConfig):
    label = 'partner'
    name = 'oscar.apps.partner'
    verbose_name = _('Partner')

    def ready(self):
        from . import receivers  # noqa


default_app_config = 'oscar.apps.partner.PartnerConfig'
