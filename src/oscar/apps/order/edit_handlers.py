from django.utils.translation import gettext_lazy as _
from oscar.core.edit_handlers import (
    HelpPanel, AddOnlyInlineTablePanel, AddressChooserPanel, ModelChooserPanel
)
from oscar.core.loading import get_class
from oscar.vendor.modelchooser.widgets import AdminModelChooser


class OrderAddressPanel(AddressChooserPanel):
    auto_register = True

    def get_queryset(self, request):
        order = self.instance
        if order and order.user:
            return order.user.addresses.all()
        return super().get_queryset(request)


class OrderLineChooserPanel(ModelChooserPanel):
    auto_register = True
    #choice_template = "oscar/dashboard/orders/order_line_choice.html"


class OrderLinesPanel(AddOnlyInlineTablePanel):
   can_edit_existing = False


class OrderInfoPanel(HelpPanel):
    template = 'oscar/dashboard/orders/order_info.html'

    def __init__(self):
        super().__init__(template=self.template)
