from django.contrib import admin

from oscar.core.loading import get_model

from .models import is_custom_invoice_model

LegalEntity = get_model('invoices', 'LegalEntity')
LegalEntityAddress = get_model('invoices', 'LegalEntityAddress')

admin.site.register(LegalEntity)
admin.site.register(LegalEntityAddress)

if not is_custom_invoice_model:
    Invoice = get_model('invoices', 'Invoice')
    admin.site.register(Invoice)
