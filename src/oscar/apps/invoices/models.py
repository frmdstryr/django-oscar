from oscar.core.loading import is_model_registered

from oscar.invoices import app_settings
from oscar.invoices.abstract_models import AbstractInvoice, AbstractLegalEntity, AbstractLegalEntityAddress

__all__ = []

is_custom_invoice_model = app_settings.OSCAR_INVOICES_INVOICE_MODEL != 'invoices.Invoice'


if not is_model_registered('invoices', 'Invoice') and not is_custom_invoice_model:
    class Invoice(AbstractInvoice):
        pass

    __all__.append('Invoice')


if not is_model_registered('invoices', 'LegalEntity'):
    class LegalEntity(AbstractLegalEntity):
        pass

    __all__.append('LegalEntity')


if not is_model_registered('invoices', 'LegalEntityAddress'):
    class LegalEntityAddress(AbstractLegalEntityAddress):
        pass

    __all__.append('LegalEntityAddress')
