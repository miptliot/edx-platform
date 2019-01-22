from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^change_involvement_status/$', views.change_involvement_status, name='change_involvement_status'),
]
