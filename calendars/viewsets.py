#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS
from . import models, serializers, filtersets

class CalendarEntryViewSet(viewsets.ModelViewSet):
    """
    Calendar entries for companies.
    Uses ISO 8601 formatted strings for datetime fields.
    """
    queryset = models.CalendarEntry.objects.filter(company__active=True)
    serializer_class = serializers.CalendarEntrySerializer
    filter_class = filtersets.CalendarEntryFilter
    permission_classes = [IsAuthenticatedOrReadOnly]

    def check_company(self, request, company_id):
        if request.user.company_id != int(company_id):
            if not request.user.is_staff:
                self.permission_denied(
                    request,
                    message='Not a member of this company'
                )

    def get_object(self):
        obj = super(CalendarEntryViewSet, self).get_object()

        if self.request.method not in SAFE_METHODS:
            self.check_company(self.request, obj.company.id)

        return obj

    def perform_create(self, serializer):
        self.check_company(self.request, self.request.data.get('company'))

        return super(CalendarEntryViewSet, self).perform_create(serializer)
