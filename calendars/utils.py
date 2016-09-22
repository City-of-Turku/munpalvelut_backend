#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.utils import timezone

DATETIME_FORMAT_SHORT = '%Y-%m-%d %H:%M'

def datetime_formatted_localized(dt, format=DATETIME_FORMAT_SHORT):
    return timezone.localtime(dt).strftime(format)
