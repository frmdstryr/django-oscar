from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, View

from wagtail.core.models import Collection
from wagtail.images.models import Filter

from oscar.apps.catalogue.reviews.signals import review_added
from oscar.core.loading import get_classes, get_model
from oscar.core.utils import redirect_to_referrer

ProductReviewForm, VoteForm, SortReviewsForm, ReviewImageForm = get_classes(
    'catalogue.reviews.forms',
    ['ProductReviewForm', 'VoteForm', 'SortReviewsForm', 'ReviewImageForm'])


Vote = get_model('reviews', 'vote')
ProductReview = get_model('reviews', 'ProductReview')
ProductReviewImage = get_model('reviews', 'ProductReviewImage')
OscarImage = get_model('images', 'OscarImage')
Product = get_model('catalogue', 'product')


class CreateProductReview(CreateView):
    template_name = "catalogue/reviews/review_form.html"
    model = ProductReview
    product_model = Product
    form_class = ProductReviewForm
    view_signal = review_added
    max_images = 3

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            self.product_model, pk=kwargs['product_pk'])
        # check permission to leave review
        if not self.product.is_review_permitted(request.user):
            if self.product.has_review_by(request.user):
                message = _("You have already reviewed this product!")
            else:
                message = _("You can't leave a review for this product.")
            messages.warning(self.request, message)
            return redirect(self.product.get_absolute_url())

        return super().dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['max_images'] = range(self.max_images)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product'] = self.product
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        # Associate any images uploaded with this uuid to the review
        review = form.instance
        root, created = Collection.objects.get_or_create(name="Reviews")
        try:
            collection = root.get_children().get(name=review.uuid)
            for image in OscarImage.objects.filter(
                    collection=collection)[:self.max_images]:
                ProductReviewImage.objects.create(review=review, image=image)
        except Collection.DoesNotExist:
            pass

        self.send_signal(self.request, response, self.object)
        msg = "Thank you for reviewing this product!"
        if settings.OSCAR_MODERATE_REVIEWS:
            msg += " Your review will be available after approval."
        messages.success(self.request, _(msg))
        return response

    def get_success_url(self):
        return self.product.get_absolute_url()

    def send_signal(self, request, response, review):
        self.view_signal.send(sender=self, review=review, user=request.user,
                              request=request, response=response)


class UploadImagePreview(View):
    """ Preview a review image

    """
    def get(self, request, product_slug, product_pk, collection, image_id):
        image = get_object_or_404(
            OscarImage, id=image_id, collection__name=collection)

        if image.collection.get_parent().name != 'Reviews':
            raise HttpResponseNotFound()  # Not allowed to access this

        response = HttpResponse()
        image = Filter(spec='fill-320x320').run(image, response)
        response['Content-Type'] = 'image/' + image.format_name
        return response


class UploadImageDelete(View):
    """ Remove the image

    """
    def post(self, request, product_slug, product_pk, collection, image_id):
        image = get_object_or_404(
            OscarImage, id=image_id, collection__name=collection)
        if image.collection.get_parent().name != 'Reviews':
            raise HttpResponseNotFound()  # Not allowed to access this
        if ProductReview.objects.filter(uuid=collection).exists():
            raise HttpResponseNotFound()  # Can't delete anymore
        image.delete()
        return JsonResponse({'status': 'OK'})


class UploadImageView(View):
    """
    API to upload an image. This is done before the review is saved so
    """
    def post(self, request, product_slug, product_pk, *args, **kwargs):
        image = OscarImage(uploaded_by_user=request.user)
        form = ReviewImageForm(request.POST, request.FILES, instance=image)
        if not form.is_valid():
            return JsonResponse({
                'status': 'Invalid Request',
                'errors': form.errors,
            })

        # Cannot upload to existing reviews
        review_uuid = form.cleaned_data['uuid']
        if ProductReview.objects.filter(uuid=review_uuid).exists():
            return JsonResponse({
                'status': 'Invalid Request',
            })

        # Add it to a collection for this review
        root, created = Collection.objects.get_or_create(name="Reviews")
        try:
            collection = root.get_children().get(name=review_uuid)
        except Collection.DoesNotExist:
            collection = root.add_child(name=review_uuid)
        image.collection = collection

         # Set image file size
        image.file_size = image.file.size

        # Set image file hash
        image.file.seek(0)
        image._set_file_hash(image.file.read())
        image.file.seek(0)
        form.save()
        thumbnail_url = reverse('catalogue:reviews-preview-image',
                      args=(product_slug, product_pk, review_uuid, image.id))
        delete_url = reverse('catalogue:reviews-delete-image',
                      args=(product_slug, product_pk, review_uuid, image.id))
        return JsonResponse({
            'status': 'OK',
            'thumbnail_url': thumbnail_url,
            'delete_url': delete_url
        })


class ProductReviewDetail(DetailView):
    template_name = "catalogue/reviews/review_detail.html"
    context_object_name = 'review'
    model = ProductReview

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            Product, pk=self.kwargs['product_pk'])
        return context


class AddVoteView(View):
    """
    Simple view for voting on a review.

    We use the URL path to determine the product and review and use a 'delta'
    POST variable to indicate it the vote is up or down.
    """

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['product_pk'])
        review = get_object_or_404(ProductReview, pk=self.kwargs['pk'])

        form = VoteForm(review, request.user, request.POST)
        if form.is_valid():
            if form.is_up_vote:
                review.vote_up(request.user)
            elif form.is_down_vote:
                review.vote_down(request.user)
            review.update_totals()
            messages.success(request, _("Thanks for voting!"))
        else:
            for error_list in form.errors.values():
                for msg in error_list:
                    messages.error(request, msg)
        return redirect_to_referrer(request, product.get_absolute_url())


class ProductReviewList(ListView):
    """
    Browse reviews for a product
    """
    template_name = 'catalogue/reviews/review_list.html'
    context_object_name = "reviews"
    model = ProductReview
    product_model = Product
    paginate_by = settings.OSCAR_REVIEWS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.approved().filter(
            product=self.kwargs['product_pk'])
        self.form = SortReviewsForm(self.request.GET)
        sort_by = SortReviewsForm.SORT_BY_SCORE_HIGHEST
        if self.request.GET and self.form.is_valid():
            sort_by = self.form.cleaned_data['sort_by']
        return qs.order_by(sort_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(
            self.product_model, pk=self.kwargs['product_pk'])
        context['form'] = self.form
        return context
