from django.conf.urls import include, url
from rest_framework_nested import routers

from api import viewsets
from api import views

from logger import viewsets as log_viewsets
from organisation import viewsets as org_viewsets
from services import viewsets as services_viewsets
from calendars import viewsets as calendars_viewsets
from orders import viewsets as orders_viewsets
from feedback import viewsets as feedback_viewsets

router = routers.DefaultRouter()
router.register(r'users', viewsets.UserViewSet, 'user')
router.register(r'user-sites', viewsets.UserSiteViewSet, 'user-site')
router.register(r'logs', log_viewsets.LogEntryViewSet, 'log')
router.register(r'companies', org_viewsets.CompanyViewSet, 'company')
router.register(r'calendarentries', calendars_viewsets.CalendarEntryViewSet, 'calendarentries')
router.register(r'services', services_viewsets.ServicePackageViewSet, 'services')
router.register(r'feedback', feedback_viewsets.FeedbackViewSet, 'feedback')

companies_router = routers.NestedSimpleRouter(router, r'companies', lookup='company')
companies_router.register(r'pictures', org_viewsets.CompanyPictureViewSet, 'company-pictures')
companies_router.register(r'orders', orders_viewsets.CompanyOrderViewSet, 'company-orders')
companies_router.register(r'users', org_viewsets.CompanyUserViewSet, 'company-users')

user_router = routers.NestedSimpleRouter(router, r'users', lookup='user')
user_router.register(r'orders', orders_viewsets.UserOrderViewSet, 'user-orders')
user_router.register(r'rate-order', orders_viewsets.RateOrderViewSet, 'user-orders-rate')

urlpatterns = [
    url(r'^verify-user/$', views.VerifyUserView.as_view(), name='user-verify'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^forgotten-password/$', views.PasswordResetRequestView.as_view(), name='forgotten-password'),
    url(r'^reset-password/$', views.PasswordResetView.as_view(), name='reset-password'),
    url(r'^ytr/', include('ytr.urls')),
    url(r'^', include(router.urls)),
    url(r'^', include(companies_router.urls)),
    url(r'^', include(user_router.urls)),
]
