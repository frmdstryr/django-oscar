from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/chooser/(?P<signed_data>[a-zA-Z0-9.:_-]+)/$',
        views.chooser,
        name='model_chooser'),
]
