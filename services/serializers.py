from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from services.models import ServicePackage, ServicePackageDescription

class ServicePackageSerializer(serializers.ModelSerializer):
    ""
    ""
    class Meta:
        model = ServicePackage
        
        fields = ('id', 'shortname', 'title', 'pricing_formula', 'website', 'description')
    
    title = serializers.DictField(child=serializers.CharField())
    description = serializers.DictField(child=serializers.CharField())
