from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_model
from wagtail.admin import messages, widgets


CreateView = get_class('dashboard.views', 'CreateView')
EditView = get_class('dashboard.views', 'EditView')
Benefit = get_model('offer', 'Benefit')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Voucher = get_model('voucher', 'Voucher')


class VoucherCreateView(CreateView):

    def form_valid(self, form):
        condition = Condition.objects.create(
            range=form.cleaned_data['benefit_range'],
            type=Condition.COUNT,
            value=1
        )
        benefit = Benefit.objects.create(
            range=form.cleaned_data['benefit_range'],
            type=form.cleaned_data['benefit_type'],
            value=form.cleaned_data['benefit_value']
        )
        name = form.cleaned_data['name']
        offer = ConditionalOffer.objects.create(
            name=_("Offer for voucher '%s'") % name,
            offer_type=ConditionalOffer.VOUCHER,
            benefit=benefit,
            condition=condition,
            exclusive=form.cleaned_data['exclusive'],
        )
        voucher = Voucher.objects.create(
            name=name,
            code=form.cleaned_data['code'],
            usage=form.cleaned_data['usage'],
            start_datetime=form.cleaned_data['start_datetime'],
            end_datetime=form.cleaned_data['end_datetime'],
        )
        voucher.offers.add(offer)
        messages.success(
            self.request, self.get_success_message(voucher),
            buttons=self.get_success_message_buttons(voucher)
        )
        return redirect(self.get_success_url())


class VoucherEditView(EditView):

    def get_initial(self):
        voucher = self.get_instance()
        offer = voucher.offers.first()
        benefit = offer.benefit
        return {
            'benefit_type': benefit.type,
            'benefit_range': benefit.range,
            'benefit_value': benefit.value,
            'exclusive': offer.exclusive,
        }

    def form_valid(self, form):
        voucher = self.get_instance()
        voucher.name = form.cleaned_data['name']
        voucher.code = form.cleaned_data['code']
        voucher.usage = form.cleaned_data['usage']
        voucher.start_datetime = form.cleaned_data['start_datetime']
        voucher.end_datetime = form.cleaned_data['end_datetime']
        voucher.save()

        offer = voucher.offers.first()
        offer.condition.range = form.cleaned_data['benefit_range']
        offer.condition.save()

        offer.exclusive = form.cleaned_data['exclusive']
        offer.save()

        benefit = voucher.benefit
        benefit.range = form.cleaned_data['benefit_range']
        benefit.type = form.cleaned_data['benefit_type']
        benefit.value = form.cleaned_data['benefit_value']
        benefit.save()

        messages.success(
            self.request, self.get_success_message(voucher),
            buttons=self.get_success_message_buttons(voucher)
        )
        return redirect(self.get_success_url())
