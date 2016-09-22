#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

import django_filters
from rest_framework import filters
from . import models

class CalendarEntryFilter(filters.FilterSet):
    start__gt = django_filters.IsoDateTimeFilter(name='start', lookup_expr='gt')
    start__gte = django_filters.IsoDateTimeFilter(name='start', lookup_expr='gte')
    start__lt = django_filters.IsoDateTimeFilter(name='start', lookup_expr='lt')
    start__lte = django_filters.IsoDateTimeFilter(name='start', lookup_expr='lte')

    end__gt = django_filters.IsoDateTimeFilter(name='end', lookup_expr='gt')
    end__gte = django_filters.IsoDateTimeFilter(name='end', lookup_expr='gte')
    end__lt = django_filters.IsoDateTimeFilter(name='end', lookup_expr='lt')
    end__lte = django_filters.IsoDateTimeFilter(name='end', lookup_expr='lte')

    class Meta:
        model = models.CalendarEntry
        fields = ['company']
