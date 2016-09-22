#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

import django_filters
from rest_framework import filters
from . import models

class OrderFilter(filters.FilterSet):

    created__gt = django_filters.IsoDateTimeFilter(name='created', lookup_expr='gt')
    created__gte = django_filters.IsoDateTimeFilter(name='created', lookup_expr='gte')
    created__lt = django_filters.IsoDateTimeFilter(name='created', lookup_expr='lt')
    created__lte = django_filters.IsoDateTimeFilter(name='created', lookup_expr='lte')

    timeslot_start__gt = django_filters.IsoDateTimeFilter(name='timeslot_start', lookup_expr='gt')
    timeslot_start__gte = django_filters.IsoDateTimeFilter(name='timeslot_start', lookup_expr='gte')
    timeslot_start__lt = django_filters.IsoDateTimeFilter(name='timeslot_start', lookup_expr='lt')
    timeslot_start__lte = django_filters.IsoDateTimeFilter(name='timeslot_start', lookup_expr='lte')

    timeslot_end__gt = django_filters.IsoDateTimeFilter(name='timeslot_end', lookup_expr='gt')
    timeslot_end__gte = django_filters.IsoDateTimeFilter(name='timeslot_end', lookup_expr='gte')
    timeslot_end__lt = django_filters.IsoDateTimeFilter(name='timeslot_end', lookup_expr='lt')
    timeslot_end__lte = django_filters.IsoDateTimeFilter(name='timeslot_end', lookup_expr='lte')

    class Meta:
        model = models.Order
        fields = [] # Exclude all other fields
