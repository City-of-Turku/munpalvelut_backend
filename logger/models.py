from __future__ import unicode_literals

from django.db import models
from django.conf import settings

class LogEntry(models.Model):
    DEBUG = 0
    VERBOSE = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    SEVERITY_CHOICES = (
        (DEBUG, 'Debug'),
        (VERBOSE, 'Verbose'),
        (INFO, 'Info'),
        (WARNING, 'Warning'),
        (ERROR, 'Error'),
        )
    SEVERITY_NAMES = {
        'debug': DEBUG,
        'verbose': VERBOSE,
        'info': INFO,
        'warning': WARNING,
        'warn': WARNING,
        'error': ERROR,
    }

    message = models.TextField(help_text="")
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=255, blank=True)
    exception = models.TextField(blank=True)
    created = models.DateTimeField("Created", auto_now_add=True)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             blank=True, null=True,
                             related_name='+')

    class Meta:
        permissions = (
            ('see_all', "Can see every user's log entries"),
        )
        ordering = ('-created',)
