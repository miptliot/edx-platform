from django.conf import settings
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^check/$', views.InvolvementView.as_view(), name='check-involvement'),
    url(r'^get-involvement-token/$', views.get_involvement_token, name='get-involvement-token'),
]
