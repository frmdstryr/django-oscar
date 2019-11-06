from django.urls import path
from django.contrib.auth.decorators import login_required

from oscar.core.application import Application
from oscar.core.loading import get_class


class ProductReviewsApplication(Application):
    name = None
    hidable_feature_name = "reviews"

    detail_view = get_class('catalogue.reviews.views', 'ProductReviewDetail')
    create_view = get_class('catalogue.reviews.views', 'CreateProductReview')
    preview_view = get_class('catalogue.reviews.views', 'UploadImagePreview')
    remove_view = get_class('catalogue.reviews.views', 'UploadImageDelete')
    upload_view = get_class('catalogue.reviews.views', 'UploadImageView')
    vote_view = get_class('catalogue.reviews.views', 'AddVoteView')
    list_view = get_class('catalogue.reviews.views', 'ProductReviewList')

    def get_urls(self):
        urls = [
            path(r'<int:pk>/', self.detail_view.as_view(),
                name='reviews-detail'),
            path(r'add/', self.create_view.as_view(),
                name='reviews-add'),
            path(r'add/image/', self.upload_view.as_view(),
                name='reviews-add-image'),
            path(r'add/image/<uuid:collection>/<int:image_id>/preview/',
                 self.preview_view.as_view(),
                 name='reviews-preview-image'),
            path(r'add/image/<uuid:collection>/<int:image_id>/remove/',
                 self.remove_view.as_view(),
                 name='reviews-delete-image'),
            path(r'/<int:pk>/vote/',
                login_required(self.vote_view.as_view()),
                name='reviews-vote'),
            path('/', self.list_view.as_view(), name='reviews-list'),
        ]
        return self.post_process_urls(urls)


application = ProductReviewsApplication()
