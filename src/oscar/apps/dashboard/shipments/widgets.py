from django.urls import reverse_lazy
from django.utils.text import camel_case_to_spaces
from django.utils.translation import gettext_lazy as _
from wagtail.admin.widgets import BaseDropdownMenuButton


class AddShippingMethodDropdownButton(BaseDropdownMenuButton):
    # A dropdown to select which shipping method type to add
    template_name = 'oscar/dashboard/widgets/button_with_dropdown.html'

    def __init__(self, label, model_admin, **kwargs):
        super().__init__(label, **kwargs)
        self.model_admin = model_admin
        self.is_parent = True  # Required in render

    @property
    def show(self):
        return bool(self.dropdown_buttons)

    @property
    def dropdown_buttons(self):
        return [self.add_button(cls) for cls in
                self.model_admin.get_shipping_method_classes()]

    def add_button(self, shipping_method_class):
        url_name = self.model_admin.url_helper.get_action_url_name('create')
        name = camel_case_to_spaces(shipping_method_class.__name__)
        kwargs = {'shipping_method': name.replace(' ', '-')}
        return {
            'url': reverse_lazy(url_name, kwargs=kwargs),
            'label': _('%s') % name.title(),
            'classname': '',
            'title': _('Add a new %s shipping method') % name,
        }
