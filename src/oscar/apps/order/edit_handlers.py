from oscar.core.edit_handlers import (
    HelpPanel, AddOnlyInlineTablePanel, AddressChooserPanel
)
from oscar.core.loading import get_class


class OrderAddressPanel(AddressChooserPanel):
    auto_register = True

    def get_queryset(self, request):
        order = self.instance
        if order and order.user:
            return order.user.addresses.all()
        return super().get_queryset(request)


class OrderLinesPanel(AddOnlyInlineTablePanel):
    pass


class OrderInfoPanel(HelpPanel):
    template = 'oscar/dashboard/orders/order_info.html'

    def __init__(self):
        super().__init__(template=self.template)
