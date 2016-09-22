#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from . import utils

STR_BUSY = 'busy'
STR_AVAILABLE = 'available'

class CalendarEntry(models.Model):
    class Meta:
        ordering = ('end','start')
        verbose_name = 'calendar entry'
        verbose_name_plural = 'calendar entries'

    created = models.DateTimeField(auto_now_add=True)

    start = models.DateTimeField(help_text='Start of the time period')
    end = models.DateTimeField(help_text='End of the time period')

    busy = models.BooleanField(default=False, help_text='Busy or available, defaults to available (False)')

    company = models.ForeignKey('organisation.Company', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{start} - {end}, {busy}'.format(
            start=utils.datetime_formatted_localized(self.start),
            end=utils.datetime_formatted_localized(self.end),
            busy=STR_BUSY if self.busy else STR_AVAILABLE
        )
