#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin
from . import models

@admin.register(models.CalendarEntry)
class CalendarEntryAdmin(admin.ModelAdmin):
    list_filter = ('company__name','busy')
    search_fields = ('company__name',)
