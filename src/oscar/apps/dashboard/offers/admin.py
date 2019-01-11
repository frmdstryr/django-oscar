from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model


Range = get_model('offer', 'Range')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


class OffersAdmin(DashboardAdmin):
    model = ConditionalOffer
    menu_label = _('Offers')
    menu_icon = 'tag'
    list_display = ('name', 'active', 'offer_type', 'status',
                    'start_datetime', 'end_datetime', 'exclusive', )
    list_filter = ('status', 'offer_type',
                   'start_datetime', 'end_datetime', 'exclusive')
    search_fields = ('name')

    def active(self, obj):
        active = obj.is_available()
        return format_html('<span class="label label-{}">{}</span>',
                           'success' if active else 'danger',
                           'Yes' if active else 'No')


class RangesAdmin(DashboardAdmin):
    model = Range
    menu_label = _('Product ranges')
    menu_icon = 'list-ol'
    list_display = ('name', 'num_products', 'is_public', 'date_created')
    list_filter = ('is_public', 'date_created')
    search_fields = ('name')
