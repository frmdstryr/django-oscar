from django.conf.urls import url
from django.contrib import messages
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import (
    DashboardAdmin, DashboardURLHelper, DashboardButtonHelper
)
from oscar.core.loading import get_class, get_model
from oscar.templatetags.currency_filters import currency
from wagtail.contrib.modeladmin.mixins import ThumbnailMixin
from wagtail.admin import messages


ProductClass = get_model('catalogue', 'ProductClass')
Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')
Option = get_model('catalogue', 'Option')
AddToCartOptionGroup = get_model('catalogue', 'AddToCartOptionGroup')
ProductReview = get_model('reviews', 'ProductReview')


class AttributeOptionGroupAdmin(DashboardAdmin):
    model = AttributeOptionGroup
    dashboard_url = 'product-attribute-option-groups'
    menu_label = _('Attribute option groups')
    menu_icon = 'tags'
    list_display = ('name', 'option_summary')

    def delete_view(self, request, instance_pk):
        instance = self.model.objects.get(pk=instance_pk)
        count = instance.product_attributes.count()
        if count:
            messages.error(request, _(
                "Unable to delete '%s', there are still %s attributes using "
                "this option group" % (instance, count)))
            return redirect(self.get_action_url('index'))
        return super().delete_view(request, instance_pk)


class AttributeOptionAdmin(DashboardAdmin):
    model = AttributeOption
    dashboard_url = 'product-attribute-options'
    menu_label = _('Attribute Option')
    menu_icon = 'tag'

    def delete_view(self, request, instance_pk):
        instance = self.model.objects.get(pk=instance_pk)
        what = None
        product_count = instance.product_set.count()
        type_count = instance.productclass_set.count()
        if product_count:
            what = _("products")
        elif type_count:
            what = _("product types")
        if what:
            count = product_count or type_count
            messages.error(request, _(
                "Unable to delete '%s', there are still %s %s using "
                "this option" % (instance, count, what)))
            return redirect(self.get_action_url('index'))
        return super().delete_view(request, instance_pk)


class ProductAttributeAdmin(DashboardAdmin):
    model = ProductAttribute
    menu_label = _('Attributes')
    menu_icon = 'tag'
    dashboard_url = 'product-attributes'
    list_display = ('name', 'type', 'required', 'display')
    list_filter = ('type', 'required', 'display')
    search_fields = ('name', 'code')


class ProductClassAdmin(DashboardAdmin):
    model = ProductClass
    menu_label = _('Product types')
    dashboard_url = 'product-types'
    menu_icon = 'cube'
    list_display = ('name', 'requires_shipping', 'track_stock')
    list_filter = ('name', 'requires_shipping', 'track_stock')
    search_fields = ('name', )

    def delete_view(self, request, instance_pk):
        instance = self.model.objects.get(pk=instance_pk)
        count = instance.products.count()
        if count:
            messages.error(request, _(
                "Could not delete the %s type, there are still %s products "
                "using this type" % (instance, count)))
            return redirect(self.get_action_url('index'))
        return super().delete_view(request, instance_pk)


class ProductAdmin(DashboardAdmin, ThumbnailMixin):
    model = Product
    menu_label = _('Products')
    add_label = _('Add a new Product')
    menu_icon = 'cubes'
    dashboard_url = 'products'
    list_display = (
        'id', 'admin_thumb', 'title', 'product_class', 'inventory',
        'price', 'date_updated', 'is_enabled')
    list_filter = ('stockrecords__partner', 'product_class', 'is_enabled',
                   'date_updated', 'date_created',
                   'stockrecords__num_in_stock')
    search_fields = ('title', 'upc')

    # Enable the inspect view and redirect to the frontent page
    inspect_view_enabled = True
    list_display_add_buttons = 'title'

    # Since creating products requires a product class the create url
    # was changed to require the product class slug and a dropdown add_button
    # is used to select which one.
    index_template_name = 'oscar/dashboard/catalogue/index.html'
    add_button_class = get_class(
        'dashboard.catalogue.widgets', 'ProductAddDropdownButton')
    create_view_class = get_class(
        'dashboard.catalogue.views', 'ProductCreateView')

    # Use wagtails thumbnail mixin
    thumb_col_header_text = _('Product Image')
    thumb_image_field_name = 'thumbnail_image'
    inline_editable = ['title', 'is_enabled']
    bulk_actions = ['set_disabled', 'set_enabled']

    # =========================================================================
    # Bulk actions
    # =========================================================================
    def do_bulk_action_set_disabled(self, request, form):
        queryset = form.cleaned_data['selection']
        result = queryset.filter(is_enabled=True).update(
            is_enabled=False)
        messages.success(request, _('%s products disabled' % result))

    def do_bulk_action_set_enabled(self, request, form):
        queryset = form.cleaned_data['selection']
        result = queryset.filter(is_enabled=False).update(
            is_enabled=True)
        messages.success(request, _('%s products enabled' % result))

    # =========================================================================
    # Display fields
    # =========================================================================
    def inventory(self, product):
        """ Get the in stock status

        """
        stockrecord = product.stockrecords.all().first()
        num_in_stock = _('Not stocked')
        num_allocated = ''
        num_available = ''
        icon = 'no'
        if stockrecord is not None:
            if stockrecord.num_in_stock:
                in_stock = True
                num_in_stock = _(f'{stockrecord.num_in_stock} in stock')
                icon = 'yes'
            else:
                num_in_stock = _('Out of stock')
                icon = 'alert'
            num_allocated = _(f'{stockrecord.num_allocated} allocated')
            num_available = _(f'{stockrecord.net_stock_level} available')
            if stockrecord.is_below_threshold:
                icon = 'alert'
        icon = f'admin/img/icon-{icon}.svg'
        return format_html(
            '<ul><li><img src="{}"/> {}</li><li>{}</li><li>{}</li></ul>',
            static(icon), num_in_stock, num_allocated, num_available)

    def price(self, product):
        """ Get the price of the first stock record (if it  exists)

        """
        stockrecord = product.stockrecords.all().first()
        if not stockrecord:
            return
        return currency(stockrecord.price_excl_tax, stockrecord.price_currency)

    # =========================================================================
    # Admin customizations
    # =========================================================================

    def get_product_classes(self):
        return ProductClass.objects.all()

    def add_button(self):
        """ This button is used to choose which product class to create on
        the index view.

        """
        DropDownButton = self.add_button_class
        return DropDownButton(label=self.add_label, model_admin=self).render()

    def get_admin_urls_for_registration(self):
        """ Add a Product type chooser into the create process
        """
        urls = super().get_admin_urls_for_registration()
        url_helper = self.url_helper
        create_url = r'^%s/%s/create/(?P<product_class>[-\w]+)/$' % (
            url_helper.opts.app_label, url_helper.opts.model_name)

        create_name = url_helper.get_action_url_name('create')

        # Replace create view with new url
        urls = [u for u in urls if u.name != create_name]
        urls += [
            url(create_url, self.create_view, name=create_name),
        ]
        return tuple(urls)

    def get_queryset(self, request):
        """
        Restrict the queryset to products the given user has access to.
        A staff user is allowed to access all Products.
        A non-staff user is only allowed access to a product if they are in at
        least one stock record's partner user list.
        """
        qs = Product.objects.base_queryset()

        # Only show records for user
        user = request.user
        if user.is_staff:
            return qs
        return qs.filter(stockrecords__partner__users__pk=user.pk).distinct()

    def create_view(self, request, product_class):
        """ The product create view requires the product class.

        """
        kwargs = {'model_admin': self, 'product_class': product_class}
        view_class = self.create_view_class
        return view_class.as_view(**kwargs)(request)

    def inspect_view(self, request, instance_pk):
        """ Redirect to the frontend page

        """
        product = get_object_or_404(self.get_queryset(request), pk=instance_pk)
        return redirect(product.get_absolute_url())


class ProductOptionAdmin(DashboardAdmin):
    model = Option
    dashboard_url = 'product-cart-options'
    menu_label = _('Add to cart options')
    menu_icon = 'shopping-basket'
    list_display = ('name', 'type')
    list_filter = ('type',)
    search_fields = ('name', )


class AddToCartOptionGroupAdmin(DashboardAdmin):
    model = AddToCartOptionGroup
    dashboard_url = 'product-cart-option-groups'
    menu_label = _('Add to cart option groups')
    menu_icon = 'shopping-basket'
    list_display = ('name', 'option_summary')


class ProductReviewAdmin(DashboardAdmin):
    model = ProductReview
    dashboard_url = 'reviews'
    menu_label = _('Reviews')
    menu_icon = 'comments'
    list_display = ('product', 'title', 'body', 'score', 'total_votes',
                    'reviewer_name', 'status', 'date_created')
    list_filter = ('score', 'status')
    search_fields = ('title', 'product__title', 'body')
    inspect_view_enabled = True
    restricted_actions = ('create', 'delete', 'edit')
    bulk_actions = ['mark_approved', 'mark_rejected']

    def do_bulk_action_mark_approved(self, request, form):
        queryset = form.cleaned_data['selection']
        result = queryset.filter(status=ProductReview.FOR_MODERATION).update(
            status=ProductReview.APPROVED)
        messages.success(request, _('%s reviews marked as approved' % result))

    def do_bulk_action_mark_rejected(self, request, form):
        queryset = form.cleaned_data['selection']
        result = queryset.filter(status=ProductReview.FOR_MODERATION).update(
            status=ProductReview.REJECTED)
        messages.success(request, _('%s reviews marked as rejected' % result))


