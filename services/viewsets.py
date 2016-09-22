from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import status

from services.models import ServicePackage
from services.serializers import ServicePackageSerializer
 
class ServicePackageViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    List of service packages.
    """
    serializer_class = ServicePackageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ServicePackage.objects.all()
    
