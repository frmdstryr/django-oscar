from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_classes

from .base import DashboardAdminGroup


class CatalogueGroup(DashboardAdminGroup):
    menu_label = _('Catalogue')
    menu_icon = 'sitemap'
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = get_classes('dashboard.catalogue.admin', (
        'ProductAdmin',
        'ProductClassAdmin',
        'ProductAttributeAdmin',
        'AttributeOptionGroupAdmin',
        'ProductOptionAdmin',
        'AddToCartOptionGroupAdmin',
    ))


class FulfillmentGroup(DashboardAdminGroup):
    menu_label = _('Fullfillment')
    menu_icon = 'shopping-cart'
    menu_order = 300
    items = (
        get_class('dashboard.orders.admin', 'OrderAdmin'),
        get_class('dashboard.partners.admin', 'PartnerAdmin'),
        get_class('dashboard.partners.admin', 'StockAlertAdmin'),
    )


class CustomersGroup(DashboardAdminGroup):
    menu_label = _('Customers')
    menu_icon = 'group'
    menu_order = 400
    items = (
        get_class('dashboard.orders.admin', 'CustomerAdmin'),
        get_class('dashboard.catalogue.admin', 'ProductReviewAdmin'),
    )


class OffersGroup(DashboardAdminGroup):
    menu_label = _('Offers')
    menu_icon = 'tags'
    menu_order = 500
    items = (
        get_class('dashboard.offers.admin', 'OffersAdmin'),
        get_class('dashboard.offers.admin', 'RangesAdmin'),
        get_class('dashboard.vouchers.admin', 'VouchersAdmin'),
        get_class('dashboard.vouchers.admin', 'VoucherSetsAdmin'),
    )


class ContentGroup(DashboardAdminGroup):
    menu_label = _('Content')
    menu_icon = 'folder'
    menu_order = 600
    items = ()


class ReportsGroup(DashboardAdminGroup):
    menu_label = _('Reports')
    menu_icon = 'bar-chart'
    menu_order = 700
    items = (
        get_class('dashboard.reports.admin', 'AbandonedCartsAdmin'),
    )


class DashboardSite:
    """ This simple class serves as a basic hook for wagtail that can
    be overridden with class loading.

    See wagtail_hooks
    """
    panels = [
        get_class('dashboard.panels', 'RecentOrdersChart'),
        get_class('dashboard.panels', 'LastOrdersList'),
        get_class('dashboard.panels', 'LastSearchTermsList'),
        get_class('dashboard.panels', 'TopSearchTermsList'),
    ]

    summary_items = [
        get_class('dashboard.panels', 'OrdersSummaryItem'),
        get_class('dashboard.panels', 'CustomersSummaryItem'),
        get_class('dashboard.panels', 'ProductsSummaryItem'),
    ]

    def construct_main_menu(self, request, menu_items):
        # Remove images and documents
        excluded = ('documents',)
        menu_items[:] = [
            item for item in menu_items if item.name not in excluded
        ]

    def construct_panels(self, request, panels):
        for Panel in self.panels:
            panels.append(Panel(request))

    def construct_summary_items(self, request, summary_items):
        # Just ignore the default ones
        summary_items[:] = [
            SummaryItem(request) for SummaryItem in self.summary_items
        ]

    def register_modeladmins(self):
        for Group in get_classes('dashboard.admin', (
                    'CatalogueGroup',
                    'FulfillmentGroup',
                    'CustomersGroup',
                    'OffersGroup',
                    'ContentGroup',
                    'ReportsGroup',
                )):
            if Group.items:
                Group().register_with_wagtail()

