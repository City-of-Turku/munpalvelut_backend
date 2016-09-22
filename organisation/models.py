#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.db import models, transaction
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator

@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=255)
    businessid = models.CharField(max_length=32, unique=True)

    offered_services = models.ManyToManyField('services.ServicePackage', blank=True)

    service_areas = ArrayField(
        models.CharField(max_length=5),
        blank=True,
        help_text="Postal codes of the areas in which this company provides service"
        )

    price_per_hour = models.DecimalField(max_digits=32, decimal_places=2, blank=True, null=True, help_text="Hourly rate in EUR")
    price_per_hour_continuing = models.DecimalField(max_digits=32, decimal_places=2, blank=True, null=True, help_text="Hourly rate in EUR for continuing service")

    psop = models.BooleanField(default=False, help_text='Palveluseteli ja ostopalvelutuottaja')

    phone = models.CharField(max_length=128, blank=True, help_text="Customer facing phone number")
    email = models.EmailField(blank=True, help_text="Customer facing email address")

    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name

    @property
    def shortdescription(self):
        return {d.lang: d.shorttext for d in self.get_descriptions() if d.text}

    @property
    def description(self):
        return {d.lang: d.text for d in self.get_descriptions() if d.text}

    @property
    def service_hours(self):
        return {d.lang: d.service_hours for d in self.get_descriptions() if d.service_hours}

    def get_descriptions(self):
        if not hasattr(self, '_description_set'):
            self._description_set = list(self.companydescription_set.all())
        return self._description_set

    @property
    def profile_picture(self):
        """Return the first picture or None if this company has
        no pictures.
        TODO: optimize
        """
        try:
            return self.picture_set.all().select_related('image')[0]
        except IndexError:
            return None

    @property
    def rating(self):
        ratings = self.get_ratings()
        rating_count = len(ratings)

        # Rating count has to be greater than or equal to 2 before
        # ratings can be visible.
        if rating_count >= 2:
            return float(sum(map(lambda x: x['rating'], ratings))) / float(rating_count)
            
        return None

    def has_ytr(self):
        """
        Company does it have YdinTietoRekisteri-company extension
        Returns: YTRCompany-object if found else False
        """
        if hasattr(self, 'ytr') and type(self.ytr) == type(YTRCompany()):
            return self.ytr
        return False

    def get_ratings(self):
        if not hasattr(self, '_rating_set'):
            self._rating_set = list(self.order_set.filter(rating__isnull=False).values('id', 'rating', 'rated', 'user', 'company'))
        return self._rating_set

class CompanyDescription(models.Model):
    """Language variants for company description"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    lang = models.CharField(max_length=3)
    shorttext = models.TextField(blank=True, help_text="Short, (a sentence or two) description of the company.")
    text = models.TextField(blank=True, help_text="Full description")
    service_hours = models.CharField(max_length=255, blank=True, help_text="Freeform service description of service hours.")

    class Meta:
        unique_together = ('company', 'lang')

@python_2_unicode_compatible
class CompanyLink(models.Model):
    """Links to web, social media and other sites.
    """

    TYPE_CHOICES = (
        ('web', 'Homepage'),
        ('youtube', 'Youtube'),
        ('facebook', 'Facebook'),
        ('other', 'Other'),
    )
    TYPE_DICT = dict(TYPE_CHOICES)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="links")

    linktype = models.CharField(max_length=32, choices=TYPE_CHOICES)
    other_description = models.CharField(max_length=128, blank=True, help_text="Link description when type is 'other'")
    url = models.URLField(max_length=512)

    class Meta:
        ordering = ('linktype', 'id')

    def __str__(self):
        return self.linktype + ": " + self.url

    @property
    def description(self):
        if self.linktype == 'other':
            return self.other_description
        return self.TYPE_DICT.get(self.linktype, self.linktype)


@python_2_unicode_compatible
class Address(models.Model):
    TYPE_SNAILMAIL = "snailmail"

    ADDRESS_TYPES = (
        (TYPE_SNAILMAIL, "Snail mail"),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="addresses")

    name = models.CharField(max_length=255)
    addressType = models.CharField(max_length=16, choices=ADDRESS_TYPES)
    streetAddress = models.CharField(max_length=255)
    streetAddress2 = models.CharField(max_length=255, blank=True)
    streetAddress3 = models.CharField(max_length=255, blank=True)
    postbox = models.CharField(max_length=255, blank=True)
    postalcode = models.CharField(max_length=32, blank=True)
    city = models.CharField(max_length=255)
    subregion = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class CompanyRating(models.Model):
    """
    User ratings for companies.

    Users can rate the performance of a company and give textual feedback.
    """
    created = models.DateTimeField(auto_now_add=True)

    company = models.ForeignKey(
        Company,
        help_text='The company who receives the rating',
        on_delete=models.CASCADE,
        related_name='ratings')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='User who makes the rating. Optional',
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='company_ratings')

    message = models.TextField(help_text='Freeform message', blank=True)
    rating = models.PositiveSmallIntegerField(
        help_text='A rating between 1 and 5',
        blank=True, null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ])


class Picture(models.Model):
    """Company pictures."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    image = models.ForeignKey('media.Image', on_delete=models.PROTECT)
    title = models.CharField(max_length=200, blank=True)
    num = models.IntegerField(default=0, help_text="Order number")

    class Meta:
        ordering = ('num', 'id')


class YTRCompany(models.Model):
    """
    Extends company information with YTR data
    """
    company = models.OneToOneField(Company, related_name='ytr', null=True, blank=True)
    # code is designated by YTR, do not allow to change it
    code = models.CharField(editable=False, max_length=20, default='', null=True, blank=True, verbose_name='YTR code')

    def __str__(self):
        return self.code if self.code else _('(No YTR code)')

    @classmethod
    def map(cls, company):
        # map our data to match YTR fields
        code = "" if not company.has_ytr() else company.ytr.code
        data = {
            "entities": [
                {
                    "code": code,
                    "name": company.name,
                    "type": "Yritys",
                    "attributes": {
                        "ytunnus": {
                            "value": company.businessid
                        }
                    }
                    # ,
                    # "connections": {
                    #     "organisaationmuoto": {
                    #         "code": "1"
                    #     },
                    #     "kotimaa": {
                    #         "code": "246"
                    #     },
                    #     "asiointikieli": {
                    #         "code": "fi"
                    #     },
                    #     "kotikunta": {
                    #         "code": "2"
                    #     }
                    # }
                }
            ]
        }
        return data

