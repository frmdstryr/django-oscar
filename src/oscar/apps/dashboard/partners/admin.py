from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model


Partner = get_model('partner', 'Partner')


class PartnerAdmin(DashboardAdmin):
    model = Partner
    menu_label = _('Partners')
    dashboard_url = 'partners'
    list_display = ('name', )
    search_fields = ('name', )
