from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class InvoicesConfig(AppConfig):
    label = 'invoices'
    name = 'oscar_invoices'
    verbose_name = _('Invoices')
