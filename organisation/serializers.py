from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from organisation.models import Company, CompanyDescription, Address, CompanyLink, Picture, CompanyRating
from media.models import Image, ImageError

from io import BytesIO
from itertools import chain
import base64

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'name', 'addressType',
            'streetAddress', 'streetAddress2', 'streetAddress3',
            'postbox', 'postalcode', 'city', 'subregion', 'country',
            )


class DescriptionField(serializers.DictField):
    child = serializers.CharField(allow_blank=True)


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyLink
        fields = ('linktype', 'description', 'url')

    description = serializers.CharField(required=False)
    url = serializers.URLField(allow_blank=True)

class CompanyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRating
        read_only_fields = ('id', 'user', 'created')

class AnonymousCompanyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRating
        read_only_fields = ('created',)
        fields = ('message', 'rating') + read_only_fields

class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = ('id', 'url', 'width', 'height', 'title', 'num')

    url = serializers.URLField(source='image.image.url', read_only=True)
    width = serializers.IntegerField(source='image.width', read_only=True)
    height = serializers.IntegerField(source='image.height', read_only=True)


class PictureUploadSerializer(serializers.Serializer):
    image = serializers.CharField()
    title = serializers.CharField(required=False, default='')
    num = serializers.IntegerField(required=False, default=0)

    def validate_image(self, value):
        imgdata = BytesIO(base64.b64decode(value))
        try:
            img = Image.save_or_get(imgdata)
        except ImageError as ex:
            raise serializers.ValidationError(ex.message)
        return img

    def create(self, validated_data):
        return Picture.objects.create(
            company_id=self.context['view'].kwargs['company_pk'],
            **validated_data
        )


class CompanySerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = Company
        read_only_fields = (
            'businessid',
            'ratings',
            'profile_picture',
            )
        fields = ('id', 'name', 'service_areas', 'addresses', 'shortdescription', 'description',
                  'service_hours',
                  'links', 'price_per_hour', 'price_per_hour_continuing',
                  'offered_services', 'orders', 'pictures', 'rating', 'psop',
                  'phone', 'email') + read_only_fields

    addresses = AddressSerializer(many=True, required=False)
    shortdescription = DescriptionField()
    description = DescriptionField()
    service_hours = DescriptionField()
    links = LinkSerializer(many=True, required=False)
    ratings = AnonymousCompanyRatingSerializer(many=True, required=False, read_only=True)
    profile_picture = PictureSerializer(read_only=True)

    orders = serializers.HyperlinkedIdentityField(
        view_name='api:company-orders-list',
        lookup_url_kwarg='company_pk'
    )

    pictures = serializers.HyperlinkedIdentityField(
        view_name='api:company-pictures-list',
        lookup_url_kwarg='company_pk'
    )

    rating = serializers.FloatField(read_only=True)

    def update(self, instance, validated_data):
        addresses = validated_data.pop('addresses', None)
        description = validated_data.pop('description', {})
        shortdesc = validated_data.pop('shortdescription', {})
        service_hours = validated_data.pop('service_hours', {})
        links = validated_data.pop('links', None)

        with transaction.atomic():
            instance = super(CompanySerializer, self).update(instance, validated_data)

            if addresses is not None:
                instance.addresses.all().delete()
                Address.objects.bulk_create([
                    Address(company=instance, **address) for address in addresses
                ])

            instance.companydescription_set.all().delete()
            CompanyDescription.objects.bulk_create([
                CompanyDescription(
                        company=instance,
                        lang=lang,
                        shorttext=shortdesc.get(lang, ''),
                        text=description.get(lang, ''),
                        service_hours=service_hours.get(lang, '')
                    ) for lang in set(chain(description.keys(),service_hours.keys(),shortdesc.keys()))
                ])

            if links is not None:
                instance.links.all().delete()
                CompanyLink.objects.bulk_create([
                    CompanyLink(
                        company=instance,
                        linktype=link['linktype'],
                        other_description=link.get('description','') if link['linktype'] == 'other' else '',
                        url=link['url'],
                    ) for link in links if link['url']
                ])

            return instance
