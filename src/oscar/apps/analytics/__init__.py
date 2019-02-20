from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnalyticsConfig(AppConfig):
    label = 'analytics'
    name = 'oscar.apps.analytics'
    verbose_name = _('Analytics')

    def ready(self):
        from . import receivers  # noqa


default_app_config = 'oscar.apps.analytics.AnalyticsConfig'
