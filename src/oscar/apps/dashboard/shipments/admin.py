from django.conf.urls import url
from django.urls import reverse
from django.utils.text import camel_case_to_spaces
from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model

from wagtail.admin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class
)

OrderAndItemCharges = get_model('shipping', 'OrderAndItemCharges')
WeightBased = get_model('shipping', 'WeightBased')
ShippingMethod = get_model('shipping', 'Method')


class ShippingMethodsAdmin(DashboardAdmin):
    model = ShippingMethod
    menu_label = _('Shipping Methods')
    add_label = _('Add a new Shipping Method')
    menu_icon = 'truck'

    dashboard_url = 'shipping-methods'
    list_display = ('name', 'code', 'is_enabled', 'calculation_method')
    list_filter = ('is_enabled', )
    search_fields = ('name', 'code')

    # =========================================================================
    # Display fields
    # =========================================================================
    def calculation_method(self, method):
        return camel_case_to_spaces(method.__class__.__name__).title()

    # =========================================================================
    # Admin customizations
    # =========================================================================

    # Since creating shipping methods requires a shipment method class
    # the create url was changed to require the shipping method and a dropdown
    # add_button is used to select which one.
    index_template_name = 'oscar/dashboard/shipments/index.html'
    add_button_class = get_class(
        'dashboard.shipments.widgets', 'AddShippingMethodDropdownButton')
    create_view_class = get_class(
        'dashboard.shipments.views', 'ShippingMethodCreateView')
    edit_view_class = get_class(
        'dashboard.shipments.views', 'ShippingMethodEditView')

    def get_shipping_method_classes(self):
        """ Called to get all the available shipping method subclasses

        """
        return (OrderAndItemCharges, WeightBased)

    def get_shipping_method(self, shipping_method_name):
        """ Invoked by the create view to lookup the shipping method using
        the class name

        """
        name = shipping_method_name.replace("-", "")
        for cls in self.get_shipping_method_classes():
            if cls.__name__.lower() == name:
                return cls

    def add_button(self):
        """ This button is used to choose which shipping method class to create
        on the index view.

        """
        DropDownButton = self.add_button_class
        return DropDownButton(label=self.add_label, model_admin=self).render()

    def get_admin_urls_for_registration(self):
        """ Add a Product type chooser into the create process
        """
        urls = super().get_admin_urls_for_registration()
        url_helper = self.url_helper
        create_url = r'^%s/%s/create/(?P<shipping_method>[-\w]+)/$' % (
            url_helper.opts.app_label, url_helper.opts.model_name)

        # Replace create view with new url
        create_name = url_helper.get_action_url_name('create')
        urls = [u for u in urls if u.name != create_name]
        urls += [url(create_url, self.create_view, name=create_name)]
        return tuple(urls)

    def create_view(self, request, shipping_method):
        """ The product create view requires the product class.

        """
        kwargs = {'model_admin': self, 'shipping_method': shipping_method}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def get_edit_handler(self, instance, request, model=None):
        """
        Overridden to accept a model parameters
        """
        model = model or type(instance)
        if hasattr(self, 'edit_handler'):
            edit_handler = self.edit_handler
        elif hasattr(self, 'panels'):
            panels = self.panels
            edit_handler = ObjectList(panels)
        elif hasattr(self.model, 'edit_handler'):
            edit_handler = model.edit_handler
        elif hasattr(model, 'panels'):
            panels = model.panels
            edit_handler = ObjectList(panels)
        else:
            fields_to_exclude = self.get_form_fields_exclude(request=request)
            panels = extract_panel_definitions_from_model_class(
                model, exclude=fields_to_exclude)
            edit_handler = ObjectList(panels)
        return edit_handler
