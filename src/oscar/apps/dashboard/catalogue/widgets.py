from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from wagtail.admin.widgets import BaseDropdownMenuButton


class ProductAddDropdownButton(BaseDropdownMenuButton):
    # A dropdown to select which product type to add
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
                self.model_admin.get_product_classes()]

    def add_button(self, product_class):
        url_name = self.model_admin.url_helper.get_action_url_name('create')
        kwargs = {'product_class': product_class.slug}
        return {
            'url': reverse_lazy(url_name, kwargs=kwargs),
            'label': _('%s') % product_class.name,
            'classname': '',
            'title': _('Add a new %s product') % product_class.name,
        }
