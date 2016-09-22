from rest_framework import serializers

class YtrFetchSerializer(serializers.Serializer):
    businessid = serializers.CharField(max_length=9)


class YtrCompanySerializer(serializers.Serializer):
    businessid = serializers.CharField(max_length=9)
    name = serializers.CharField(max_length=200)