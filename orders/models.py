#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

from palvelutori.models import User
from mailer.mail import send_template_mail

from datetime import timedelta

class Order(models.Model):

    created = models.DateTimeField(auto_now_add=True)

    # User info

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True, null=True,
        on_delete=models.SET_NULL)
    user_first_name = models.CharField( max_length=30)
    user_last_name = models.CharField(max_length=30)
    user_email = models.EmailField(max_length=255)
    user_phone = models.CharField(max_length=50)

    # Usersite info

    site_address_street = models.CharField(max_length=255)
    site_address_street2 = models.CharField(max_length=255, blank=True)
    site_address_postalcode = models.CharField(max_length=32)
    site_address_city = models.CharField(max_length=255)
    site_address_country = models.CharField(max_length=3, default="FIN", editable=False)
    site_room_count = models.PositiveSmallIntegerField(blank=True, null=True)
    site_sanitary_count = models.PositiveSmallIntegerField(blank=True, null=True)
    site_floor_count = models.PositiveSmallIntegerField(blank=True, null=True)
    site_floor_area = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    # Company info

    company = models.ForeignKey(
        'organisation.Company',
        on_delete=models.CASCADE,
        help_text='company id'
    )

    # Service info

    service_package = models.ForeignKey(
        'services.ServicePackage',
        blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text='service package id'
    )
    service_package_shortname = models.SlugField()

    # Order info

    duration = models.DecimalField(max_digits=4, decimal_places=1, help_text='Duration of the service (decimal with one decimal place, max value 999.9)')
    price = models.DecimalField(max_digits=7, decimal_places=2, help_text='Price of the service (decimal with two decimal places, max value 99999.99)')
    timeslot_start = models.DateTimeField(help_text='datetime in ISO 8601 format')
    timeslot_end = models.DateTimeField(help_text='datetime in ISO 8601 format')

    extra_info = models.TextField(blank=True)

    # Rating

    rating = models.PositiveSmallIntegerField(
        help_text='A rating between 1 and 5',
        blank=True, null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ])

    rated = models.DateTimeField(blank=True, null=True, editable=False)

    def can_be_rated(self):
        """
        An order can be rated only after the timeslot has ended.
        The rating can be changed for 24 hours after it was originally made.
        """
        now = timezone.now()
        return \
            self.timeslot_end < now \
            and (not self.rated or (now - self.rated < timedelta(days=1)))

    def send_notification(self):
        """
        Send a notification mail to the company.
        """

        send_template_mail(
            [u.email for u in self.company.user_set.filter(is_active=True)],
            'new-order-notification',
            {
                'order': self,
            })
