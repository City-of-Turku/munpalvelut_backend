from __future__ import unicode_literals

from django.db import models
from django.conf import settings

import os
import binascii

class ApiKey(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=128, unique=True)
    active = models.BooleanField(default=True)

class AuthToken(models.Model):
    key = models.CharField("Key", max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField("Created", auto_now_add=True)

    @classmethod
    def create_for(cls, user):
        return cls.objects.create(
            key=cls.generate_key(),
            user=user
            )
    
    @staticmethod
    def generate_key():
        return binascii.hexlify(os.urandom(20)).decode()
