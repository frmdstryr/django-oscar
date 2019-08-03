from django import forms
from wagtail.admin.edit_handlers import (
    InlinePanel, MultiFieldPanel, FieldPanel,
    DELETION_FIELD_NAME, ORDERING_FIELD_NAME
)

from oscar.core.loading import get_model


class ProductAttributesPanel(InlinePanel):
    # Wagtail handles the FK relation from AttributeValue to Product
    # this is the name that links the AttributeValue to the Attribute
    rel_name = 'attribute'

    def on_form_bound(self):
        ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')

        instance = self.instance
        related_model = self.db_field.related_model
        product_class = instance.product_class
        if product_class is None:
            raise ValueError("Product class is missing")

        # Enforce min and max to match attribute count
        self.min_value = product_class.attributes.count()
        self.max_value = self.min_value
        self.formset = self.form.formsets[self.relation_name]
        self.children = []

        # Forms that have an attribute set
        populated_forms = {f.instance.attribute: f for f in self.formset.forms
                           if f.instance.attribute}
        # And those that don't?
        unpopulated_forms = [f for f in self.formset.forms
                             if f not in populated_forms.values()]

        # Create a form for each attribute
        for attribute in product_class.attributes.all():
            try:
                value = instance.attribute_values.get(attribute=attribute)
            except ProductAttributeValue.DoesNotExist:
                value = ProductAttributeValue(
                    product=instance, attribute=attribute)

            # Get the populated form for this attribute
            if attribute in populated_forms:
                subform = populated_forms.pop(attribute)
            elif unpopulated_forms:
                subform = unpopulated_forms.pop()
                subform.instance = value
            else:
                subform = self.formset.empty_form
                subform.instance = value

            field_name = 'value_%s' % attribute.type

            # Remove unused fields from form
            attribute_fields = (
                'id', ORDERING_FIELD_NAME, field_name, self.rel_name)
            subform.fields = {
                name: field for name, field in subform.fields.items()
                if name in attribute_fields}

            # Hide the the attribute field
            subform.fields[self.rel_name].widget = forms.HiddenInput()
            # ditto for the ORDER field, if present
            if self.formset.can_order:
                subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            # Make sure the field matches the attribute spec
            field = subform.fields[field_name]
            field.required = attribute.required
            field.label = attribute.name

            # Create the edit handler, only the attribute field type is used
            child_edit_handler = MultiFieldPanel(
                [FieldPanel(field_name)], heading=attribute.name)
            self.children.append(
                child_edit_handler.bind_to(model=related_model).bind_to(
                    instance=subform.instance, form=subform,
                    request=self.request))

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if self.formset.can_order and self.formset.is_valid():
            self.children.sort(
                key=lambda child: child.form.cleaned_data[ORDERING_FIELD_NAME]
                                  if child.form.is_bound else 1)

        empty_form = self.formset.empty_form
        empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

        self.empty_child = self.get_child_edit_handler()
        self.empty_child = self.empty_child.bind_to_instance(
            instance=empty_form.instance, form=empty_form, request=self.request)
