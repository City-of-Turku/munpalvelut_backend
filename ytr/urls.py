from django.conf.urls import url

from . import views

urlpatterns = [
    url('^fetch/$', views.YtrFetchView.as_view(), name='ytr-fetch'),
    url('^company/$', views.YtrCompanyView.as_view(), name='ytr-company'),
]
