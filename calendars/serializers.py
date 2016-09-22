#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from rest_framework import serializers
from . import models

class CalendarEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CalendarEntry

    def validate(self, data):
        """
        Check that the start is before the end.
        """
        if data['start'] > data['end']:
            raise serializers.ValidationError("End must occur after start")
        return data
