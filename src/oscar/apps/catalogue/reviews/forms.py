from uuid import uuid4
from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model

from wagtail.images.fields import WagtailImageField


Vote = get_model('reviews', 'Vote')
ProductReview = get_model('reviews', 'ProductReview')
OscarImage = get_model('images', 'OscarImage')


class ProductReviewForm(forms.ModelForm):
    name = forms.CharField(label=_('Name'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)

    uuid = forms.UUIDField(widget=forms.HiddenInput(), required=True)

    def __init__(self, product, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.product = product
        if user and user.is_authenticated:
            self.instance.user = user
            del self.fields['name']
            del self.fields['email']
        self.fields['uuid'].initial = self.instance.uuid

    class Meta:
        model = ProductReview
        fields = ('title', 'score', 'body', 'name', 'email', 'uuid')


class ReviewImageForm(forms.ModelForm):
    #: Must match the UUID from the product review
    uuid = forms.CharField(widget=forms.HiddenInput(), required=True)
    file = WagtailImageField(required=True)

    class Meta:
        model = OscarImage
        fields = ('file',)



class VoteForm(forms.ModelForm):

    class Meta:
        model = Vote
        fields = ('delta',)

    def __init__(self, review, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.review = review
        self.instance.user = user

    @property
    def is_up_vote(self):
        return self.cleaned_data['delta'] == Vote.UP

    @property
    def is_down_vote(self):
        return self.cleaned_data['delta'] == Vote.DOWN


class SortReviewsForm(forms.Form):
    SORT_BY_SCORE_HIGHEST = '-score'
    SORT_BY_SCORE_LOWEST = 'score'
    SORT_BY_MOST_RECENT = '-date_created'
    SORT_BY_MOST_HELPFUL = '-delta_votes'
    SORT_BY_MOST_VOTES = '-total_votes'

    SORT_REVIEWS_BY_CHOICES = (
        (SORT_BY_SCORE_HIGHEST, _('Score (highest first)')),
        (SORT_BY_SCORE_LOWEST, _('Score (lowest first)')),
        (SORT_BY_MOST_RECENT, _('Most recent')),
        (SORT_BY_MOST_HELPFUL, _('Most helpful')),
        (SORT_BY_MOST_VOTES, _('Most votes')),
    )

    sort_by = forms.ChoiceField(
        choices=SORT_REVIEWS_BY_CHOICES,
        label=_('Sort by'),
        initial=SORT_BY_SCORE_HIGHEST,
        required=False
    )
