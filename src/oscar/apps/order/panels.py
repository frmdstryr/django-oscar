from oscar.core.edit_handlers import HelpPanel, InlinePanel
from oscar.core.loading import get_class
from wagtailmodelchooser.edit_handlers import ModelChooserPanel


class OrderAddressPanel(ModelChooserPanel):
    auto_register = True

    def get_queryset(self, request):
        order = self.instance
        return order.user.addresses.all()


class OrderLinesPanel(InlinePanel):
    pass


class OrderInfoPanel(HelpPanel):
    template = 'oscar/dashboard/orders/order_info.html'

    def __init__(self):
        super().__init__(template=self.template)
