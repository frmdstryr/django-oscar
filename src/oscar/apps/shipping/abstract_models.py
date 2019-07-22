# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from oscar.core import loading, prices
from oscar.core.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel,
    TabbedInterface, ObjectList, RowPanel
)

from oscar.models.fields import AutoSlugField, ParentalKey
from modelcluster.models import ClusterableModel
from polymorphic.models import PolymorphicModel

Scale = loading.get_class('shipping.scales', 'Scale')


class AbstractMethod(PolymorphicModel):
    """
    Implements the interface declared by shipping.base.Base
    """
    code = AutoSlugField(_("Slug"), max_length=128, unique=True,
                         populate_from='name', db_index=True)
    name = models.CharField(_("Name"), max_length=128, unique=True,
                            db_index=True)
    description = models.TextField(_("Description"), blank=True)

    # We allow shipping methods to be linked to a specific set of countries
    countries = models.ManyToManyField('address.Country',
                                       blank=True, verbose_name=_("Countries"))

    # Allow selection from the dashboard
    is_enabled = models.BooleanField(_('Is Enabled'), default=True)

    # We need this to mimic the interface of the Base shipping method
    is_discounted = False

    shipping_method_panels = [
        FieldPanel('name'),
        FieldPanel('is_enabled'),
        FieldPanel('description', classname='full'),
        FieldPanel('contries'),
    ]

    class Meta:
        abstract = True
        app_label = 'shipping'
        ordering = ['name']
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __str__(self):
        return self.name

    # calculate, is_applicable, and discount must be overwritten in subclasses


class AbstractOrderAndItemCharges(AbstractMethod):
    """
    Standard shipping method

    This method has two components:
    * a charge per order
    * a charge per item

    Many sites use shipping logic which fits into this system.  However, for
    more complex shipping logic, a custom shipping method object will need to
    be provided that subclasses ShippingMethod.
    """
    price_per_order = models.DecimalField(
        _("Price per order"), decimal_places=2, max_digits=12,
        default=D('0.00'))
    price_per_item = models.DecimalField(
        _("Price per item"), decimal_places=2, max_digits=12,
        default=D('0.00'))

    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(
        _("Free Shipping"), decimal_places=2, max_digits=12, blank=True,
        null=True)

    class Meta(AbstractMethod.Meta):
        abstract = True
        app_label = 'shipping'
        verbose_name = _("Order and Item Charge")
        verbose_name_plural = _("Order and Item Charges")

    def is_applicable(self, basket, shipping_address=None, **kwargs):
        return True

    def calculate(self, basket, shipping_address=None, **kwargs):
        if (self.free_shipping_threshold is not None
                and basket.total_incl_tax >= self.free_shipping_threshold):
            return prices.Price(
                currency=basket.currency, excl_tax=D('0.00'),
                incl_tax=D('0.00'))

        charge = self.price_per_order
        for line in basket.lines.all():
            if line.product.is_shipping_required:
                charge += line.quantity * self.price_per_item

        # Zero tax is assumed...
        return prices.Price(
            currency=basket.currency,
            excl_tax=charge,
            incl_tax=charge)


class AbstractWeightBased(AbstractMethod):
    # The attribute code to use to look up the weight of a product
    weight_attribute = 'weight'

    # The default weight to use (in kg) when a product doesn't have a weight
    # attribute.
    default_weight = models.DecimalField(
        _("Default Weight"), decimal_places=3, max_digits=12,
        default=D('0.000'),
        validators=[MinValueValidator(D('0.00'))],
        help_text=_("Default product weight in kg when no weight attribute "
                    "is defined"))

    edit_handler = TabbedInterface([
        ObjectList(
            AbstractMethod.shipping_method_panels + [
                FieldPanel('default_weight'),
            ],
            heading=_('Details')),
        ObjectList([
                InlinePanel('bands'),
            ], heading=_('Weight Bands'))
    ])

    class Meta(AbstractMethod.Meta):
        abstract = True
        app_label = 'shipping'
        verbose_name = _("Weight-based Shipping Method")
        verbose_name_plural = _("Weight-based Shipping Methods")

    def is_applicable(self, basket, shipping_address=None, **kwargs):
        return True

    def calculate(self, basket, shipping_address=None, **kwargs):
        # Note, when weighing the basket, we don't check whether the item
        # requires shipping or not.  It is assumed that if something has a
        # weight, then it requires shipping.
        scale = Scale(attribute_code=self.weight_attribute,
                      default_weight=self.default_weight)
        weight = scale.weigh_basket(basket)
        charge = self.get_charge(weight)

        # Zero tax is assumed...
        return prices.Price(
            currency=basket.currency, excl_tax=charge, incl_tax=charge)

    def get_charge(self, weight):
        """
        Calculates shipping charges for a given weight.

        If there is one or more matching weight band for a given weight, the
        charge of the closest matching weight band is returned.

        If the weight exceeds the top weight band, the top weight band charge
        is added until a matching weight band is found. This models the concept
        of "sending as many of the large boxes as needed".

        Please note that it is assumed that the closest matching weight band
        is the most cost-effective one, and that the top weight band is more
        cost effective than e.g. sending out two smaller parcels.
        Without that assumption, determining the cheapest shipping solution
        becomes an instance of the bin packing problem. The bin packing problem
        is NP-hard and solving it is left as an exercise to the reader.
        """
        weight = D(weight)  # weight really should be stored as a decimal
        if not self.bands.exists():
            return D('0.00')

        top_band = self.top_band
        if weight <= top_band.upper_limit:
            band = self.get_band_for_weight(weight)
            return band.charge
        else:
            quotient, remaining_weight = divmod(weight, top_band.upper_limit)
            if remaining_weight:
                remainder_band = self.get_band_for_weight(remaining_weight)
                return quotient * top_band.charge + remainder_band.charge
            else:
                return quotient * top_band.charge

    def get_band_for_weight(self, weight):
        """
        Return the closest matching weight band for a given weight.
        """
        try:
            return self.bands.filter(
                upper_limit__gte=weight).order_by('upper_limit')[0]
        except IndexError:
            return None

    @property
    def num_bands(self):
        return self.bands.count()

    @property
    def top_band(self):
        try:
            return self.bands.order_by('-upper_limit')[0]
        except IndexError:
            return None


class AbstractWeightBand(models.Model):
    """
    Represents a weight band which are used by the WeightBasedShipping method.
    """
    method = models.ForeignKey(
        'shipping.WeightBased',
        on_delete=models.CASCADE,
        related_name='bands',
        verbose_name=_("Method"))
    upper_limit = models.DecimalField(
        _("Upper Limit"), decimal_places=3, max_digits=12, db_index=True,
        validators=[MinValueValidator(D('0.00'))],
        help_text=_("Enter upper limit of this weight band in kg. The lower "
                    "limit will be determined by the other weight bands."))
    charge = models.DecimalField(
        _("Charge"), decimal_places=2, max_digits=12,
        validators=[MinValueValidator(D('0.00'))])

    @property
    def weight_from(self):
        lower_bands = self.method.bands.filter(
            upper_limit__lt=self.upper_limit).order_by('-upper_limit')
        if not lower_bands:
            return D('0.000')
        return lower_bands[0].upper_limit

    @property
    def weight_to(self):
        return self.upper_limit

    class Meta:
        abstract = True
        app_label = 'shipping'
        ordering = ['method', 'upper_limit']
        verbose_name = _("Weight Band")
        verbose_name_plural = _("Weight Bands")

    def __str__(self):
        return _('Charge for weights up to %s kg') % (self.upper_limit,)
