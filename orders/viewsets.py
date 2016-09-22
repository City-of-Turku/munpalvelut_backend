#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.filters import OrderingFilter, DjangoFilterBackend

from palvelutori.models import User
from . import models, serializers, permissions, filtersets

class BaseOrderMixin(object):
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_class = filtersets.OrderFilter
    ordering_fields = ('created', 'timeslot_start', 'timeslot_end')
    ordering = ('-created',)


class UserOrderViewSet( BaseOrderMixin,
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    Orders made by a user.

    Normal users can view, create and list their own orders.
    Staff users can view, create and list anyone's orders.
    Unauthenticated users are not able to do anything.

    Uses ISO 8601 formatted strings for datetime fields.

    Ordering can be changed by the 'ordering' query parameter.
    Possible entries are 'created', 'timeslot_start' and 'timeslot_end'.
    For example: ?ordering=-created, will put the newest first
    Default ordering is '-created'.
    """
    serializer_class = serializers.UserOrderSerializer
    permission_classes = [IsAuthenticated, permissions.IsOwnerOrStaff]

    def get_queryset(self):
        return models.Order.objects.filter(user_id=self.kwargs['user_pk'])

    def perform_create(self, serializer):
        obj = serializer.save(
            user=get_object_or_404(User, pk=self.kwargs['user_pk'])
        )

        # Send notification mail to the company
        obj.send_notification()

        return obj

class CompanyOrderViewSet(  BaseOrderMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    Orders received by a company.

    Normal users can view and list their company's orders.
    Staff users can view and list every company's orders.
    Unauthenticated users are not able to do anything.

    Uses ISO 8601 formatted strings for datetime fields.

    Ordering can be changed by the 'ordering' query parameter.
    Possible entries are 'created', 'timeslot_start' and 'timeslot_end'.
    For example: ?ordering=-created, will put the newest first
    Default ordering is '-created'.
    """
    serializer_class = serializers.CompanyOrderSerializer
    permission_classes = [IsAuthenticated, permissions.IsCompanyUserOrStaff]

    def get_queryset(self):
        return models.Order.objects.filter(company_id=self.kwargs['company_pk'], company__active=True)


class RateOrderViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Allow a user to rate an order.
    """
    serializer_class = serializers.RateOrderSerializer
    permission_classes = [IsAuthenticated, permissions.IsOwnerOrStaff, permissions.CanRate]

    def perform_update(self, serializer):
        kw = {}
        if not serializer.instance.rated:
            # The rated timestamp is only set when the initial rating is given
            kw['rated'] = timezone.now()

        return serializer.save(**kw)

    def get_queryset(self):
        return models.Order.objects.filter(user_id=self.kwargs['user_pk'])
