from django.forms.models import inlineformset_factory


from oscar.core.loading import get_model

ProductReview = get_model('reviews', 'ProductReview')
ProductReviewImage = get_model('reviews', 'ProductReviewImage')


ProductReviewImageFormSet = inlineformset_factory(
    ProductReview, ProductReviewImage, fields=('title', 'image'),
    extra=5, max_num=5)
