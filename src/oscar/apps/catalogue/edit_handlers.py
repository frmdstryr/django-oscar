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

    def get_attribute_form_fields(self, attribute):
        field_name = 'value_%s' % attribute.type
        return ('id', ORDERING_FIELD_NAME, field_name, self.rel_name)

    def on_form_bound(self):
        ProductAttribute = get_model('catalogue', 'ProductAttribute')
        ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')

        instance = self.instance
        related_model = self.db_field.related_model
        product_class = instance.product_class
        if product_class is None:
            raise ValueError("Product class is missing")
        self.children = []

        # Enforce min and max to match attribute count
        attributes = product_class.attributes.all()
        formset = self.formset = self.form.formsets[self.relation_name]
        formset.min_num = len(attributes)
        formset.max_num = formset.min_num

        # Get the saved values and list of attributes that need added
        saved_values = formset.get_queryset()
        saved_attributes = [v.attribute for v in saved_values]
        unsaved_attributes = [a for a in attributes if a not in saved_attributes]

        # A populated form should be created for each attribute that was
        # already saved and the min_num creates empty forms for the unsaved
        # attributes
        for subform in formset.forms:
            if formset.is_bound:
                subform.is_valid()  # Load the instance

            try:
                attribute = subform.instance.attribute
                if attribute in unsaved_attributes:
                    unsaved_attributes.remove(attribute)
            except ProductAttribute.DoesNotExist:
                # otherwise set it to one of the unsaved attributes
                attribute = unsaved_attributes.pop()
                subform.instance = ProductAttributeValue(
                    product=instance, attribute=attribute)

            # Remove unused fields from form
            attribute_fields = self.get_attribute_form_fields(attribute)
            subform.fields = {
                name: field for name, field in subform.fields.items()
                if name in attribute_fields}

            # Hide the the attribute field and set initial value
            attr_field = subform.fields[self.rel_name]
            attr_field.widget = forms.HiddenInput()
            attr_field.initial = attribute

            # ditto for the ORDER field, if present
            if formset.can_order:
                subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            # Make sure the field matches the attribute spec
            field_name = 'value_%s' % attribute.type
            value_field = subform.fields[field_name]
            value_field.required = attribute.required
            value_field.label = attribute.name

            # Restrict options to only selected option group
            if attribute.is_option or attribute.is_multi_option:
                value_field.queryset = attribute.option_group.options.all()

            # Create the edit handler, only the attribute field type is used
            child_edit_handler = MultiFieldPanel(
                [FieldPanel(field_name)], heading=attribute.name)
            self.children.append(
                child_edit_handler.bind_to(model=related_model).bind_to(
                    instance=subform.instance, form=subform,
                    request=self.request))

            # Clear any validation errors as we just changed the form
            # so it's validation state may be invalid
            if formset.is_bound:
                subform._errors = None

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if formset.can_order and formset.is_valid():
            self.children.sort(
                key=lambda child: child.form.cleaned_data.get(
                    ORDERING_FIELD_NAME, 1) or 1)

        empty_form = formset.empty_form
        if formset.can_delete:
            empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        if formset.can_order:
            empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

        self.empty_child = self.get_child_edit_handler()
        self.empty_child = self.empty_child.bind_to_instance(
            instance=empty_form.instance, form=empty_form, request=self.request)
