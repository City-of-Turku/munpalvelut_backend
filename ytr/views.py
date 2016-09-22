from django.http import Http404
from django.core.urlresolvers import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status, mixins, generics

from ytr.serializers import *
from ytr import client as ytr_client
from organisation.models import Company


class YtrFetchView(APIView):
    """
    Update or create a company based on data fetched from YTR.
    """
    permission_classes = [IsAdminUser]
    def get_serializer(self, *args, **kwargs):
        return YtrFetchSerializer(*args, **kwargs)

    def post(self, request, format=None):
        """
        ---
        serializer: ytr.serializers.YtrFetchSerializer
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            businessid = serializer.data['businessid']

            company = ytr_client.fetch_company(businessid)

            return Response({
                'status': 'ok',
                'url': reverse('api:company-detail', args=(company.id,))
            }, status=status.HTTP_201_CREATED if getattr(company, '_new', False) else status.HTTP_200_OK)


class YtrCompanyView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView):
    """
    Export currently existing company into YTR with given values. Creates or replaces YTR data.
    If company did not have YTR link, then link will be created.
    """
    serializer_class = YtrCompanySerializer
    permission_classes = [IsAdminUser]

    def post(self, request, format=None):
        serializer = YtrCompanySerializer(data=request.data)
        if serializer.is_valid():
            try:
                company = Company.objects.get(businessid=request.data['businessid'])
                if request.data.get('name', None):
                    company.name = request.data['name']
            except Company.DoesNotExist:
                raise Http404
            export = ytr_client.export_company(company)
            if export:
                return Response({
                    'status': 'ok',
                }, status=status.HTTP_200_OK)
        return Response({
            'status': 'fail'
        }, status=status.HTTP_400_BAD_REQUEST)

