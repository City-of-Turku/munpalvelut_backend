#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin
from . import models

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    pass
