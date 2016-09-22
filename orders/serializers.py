#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from rest_framework import serializers
from . import models

class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        read_only_fields = ('id',)
        exclude = ('rating',)

    site_floor_area = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        coerce_to_string=False,
        required=False,
        help_text='decimal with two decimal places, max value 99999.99'
    )
    duration = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        coerce_to_string=False,
        help_text='decimal with one decimal place, max value 999.9'
    )
    price = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
        coerce_to_string=False,
        help_text='decimal with two decimal places, max value 99999.99'
    )

    can_be_rated = serializers.BooleanField(
        read_only=True,
        help_text='can this order be rated or not'
    )

class UserOrderSerializer(OrderSerializer):

    class Meta:
        model = models.Order
        read_only_fields = ('id',)
        exclude = ('user',)

class CompanyOrderSerializer(OrderSerializer):

    class Meta:
        model = models.Order
        read_only_fields = ('id',)
        exclude = ('company', 'rating')

class RateOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        read_only_fields = ('id',)
        fields = ('id', 'rating')
