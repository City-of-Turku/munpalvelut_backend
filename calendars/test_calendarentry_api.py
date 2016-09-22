#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

import datetime
from django.utils import timezone
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.fields import DateTimeField
from palvelutori.test_mixins import BasicCRUDApiTestCaseMixin
from organisation.models import Company
from . import models

def format_datetime(value):
    """
    Helps to keep datetime representations in sync
    """
    return DateTimeField().to_representation(value)

class CalendarEntryApiTestCase(BasicCRUDApiTestCaseMixin, APITestCase):
    object_class = models.CalendarEntry

    list_url = 'api:calendarentries-list'
    detail_url = 'api:calendarentries-detail'
    create_url = 'api:calendarentries-list'
    update_url = 'api:calendarentries-detail'
    delete_url = 'api:calendarentries-detail'

    template_companies = [
        {
            'id': 1,
            'name': 'TestiYrkkä 1',
            'businessid': '1234567',
            'service_areas': ['12345'],
            'price_per_hour': '100.50',
            'price_per_hour_continuing': '55',
        },
        {
            'id': 2,
            'name': 'TestiYrkkä 2',
            'businessid': '7654321',
            'service_areas': ['54321'],
            'price_per_hour': '190.13',
            'price_per_hour_continuing': '42',
        }
    ]

    template_object = {
        'start': format_datetime(timezone.now()),
        'end': format_datetime(timezone.now() + datetime.timedelta(hours=1))
    }
    create_object = {
        'company': template_companies[0]['id'],
        'start': format_datetime(timezone.now() + datetime.timedelta(days=1)),
        'end': format_datetime(timezone.now() + datetime.timedelta(days=1, hours=1))
    }
    update_object = {
        'start': format_datetime(timezone.now() + datetime.timedelta(days=2)),
        'end': format_datetime(timezone.now() + datetime.timedelta(days=2, hours=1))
    }

    @classmethod
    def setUpTestData(cls):
        # Generate companies
        cls.companies = [Company.objects.create(**c) for c in cls.template_companies]
        super(CalendarEntryApiTestCase, cls).setUpTestData()

        # Set user companies
        u1 = cls.user_class.objects.get(email=cls.template_users['normal_user1']['email'])
        u1.company = cls.companies[0]
        u1.save()

        u2 = cls.user_class.objects.get(email=cls.template_users['normal_user2']['email'])
        u2.company = cls.companies[1]
        u2.save()

    @classmethod
    def get_object_templates(cls):
        templates = list()

        times = [
            {
                'start': format_datetime(timezone.now() + datetime.timedelta(hours=i)),
                'end': format_datetime(timezone.now() + datetime.timedelta(hours=i+1))
            }
                for i in range(3)
        ]

        for t in times:
            d = cls.template_object.copy()
            d.update(t)
            d.update({'company': cls.companies[0]})
            templates.append(d)

        dates = [
            {
                'start': format_datetime(timezone.now() + datetime.timedelta(days=i, hours=6)),
                'end': format_datetime(timezone.now() + datetime.timedelta(days=i+1, hours=6))
            }
                for i in range(3)
        ]

        for t in dates:
            d = cls.template_object.copy()
            d.update(t)
            d.update({'company': cls.companies[0]})
            templates.append(d)

        other_d = cls.template_object.copy()
        other_d.update({
            'company':  cls.companies[1],
            'start': format_datetime(timezone.now() + datetime.timedelta(hours=4)),
            'end': format_datetime(timezone.now() + datetime.timedelta(hours=4+1))
        })
        templates.append(other_d)

        return templates

    # List tests

    def test_list_anonymous(self):
        """
        Anonymous user should be able to list EVERY object
        """
        url = reverse(self.list_url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

    def test_list_logged_in(self):
        """
        Normal user should be able to list EVERY object
        """
        user = self.template_users['normal_user1']

        self.client.login(email=user['email'], password=user['password'])

        url = reverse(self.list_url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

    # Detail view tests

    def test_detail_anonymous(self):
        """
        Anonymous user should be able to view EVERY object
        """
        for obj in self.objects:
            url = reverse(self.detail_url, args=(obj.id,))
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('id', response.data)

    def test_detail_logged_in(self):
        """
        Normal user should be able to view EVERY object
        """
        user = self.template_users['normal_user1']

        self.client.login(email=user['email'], password=user['password'])

        for obj in self.objects:
            url = reverse(self.detail_url, args=(obj.id,))
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('id', response.data)

    # Create view tests

    def test_create_logged_in(self):
        """
        Normal user should be able to create ONLY for their own company
        """
        user = self.template_users['normal_user1']
        db_user = self.user_class.objects.get(email=user['email'])

        other_user = self.template_users['normal_user2']
        db_other_user = self.user_class.objects.get(email=other_user['email'])

        self.client.login(email=user['email'], password=user['password'])

        # Create for this users company
        payload = self.create_object.copy()
        payload.update({'company': db_user.company_id})

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company'], db_user.company_id)
        self.assertIn('id', response.data)
        self.assertIn('created', response.data)

        # Try to create for another users company, should not be able to
        payload.update({'company': db_other_user.company_id})

        response = self.client.post(reverse(self.create_url), data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_staff_user_invalid_object(self):
        """
        Try to create an invalid calendar entry where end is before start.
        Should return 400 Bad Request and not create an object.
        """
        obj_count1 = self.object_class.objects.all().count()

        user = self.template_users['staff_user']

        self.client.login(email=user['email'], password=user['password'])

        payload = self.create_object.copy()
        payload.update({
            'start': format_datetime(timezone.now()),
            'end': format_datetime(timezone.now() - datetime.timedelta(hours=1))
        })

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        obj_count2 = self.object_class.objects.all().count()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(obj_count1, obj_count2)

    # Update view tests

    def test_update_logged_in(self):
        """
        Normal user should be able to update ONLY for his/her own company
        """
        user = self.template_users['normal_user1']
        db_user = self.user_class.objects.get(email=user['email'])

        other_user = self.template_users['normal_user2']
        db_other_user = self.user_class.objects.get(email=other_user['email'])

        self.client.login(email=user['email'], password=user['password'])

        obj = self.object_class.objects.filter(company=db_user.company)[0]

        update = self.update_object.copy()
        [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

        payload = self.template_object.copy()
        payload.update(update)

        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company'], db_user.company_id)
        self.assertEqual(response.data['id'], obj.id)
        self.assertIn('created', response.data)
        [self.assertEqual(response.data[k], v) for k,v in update.items()]
        [self.assertNotEqual(response.data[k], getattr(obj, k)) for k,v in update.items()]

        # Update for other users company
        other_obj = self.object_class.objects.filter(company=db_other_user.company)[0]

        [self.assertNotEqual(getattr(other_obj, k), v) for k,v in update.items()]

        url = reverse(self.update_url, args=(other_obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Delete view tests

    def test_delete_logged_in(self):
        """
        Normal user should be able to delete ONLY for his/her own company
        """
        user = self.template_users['normal_user1']
        db_user = self.user_class.objects.get(email=user['email'])

        other_user = self.template_users['normal_user2']
        db_other_user = self.user_class.objects.get(email=other_user['email'])

        self.client.login(email=user['email'], password=user['password'])

        # Delete own site
        obj = self.object_class.objects.filter(company=db_user.company)[0]

        url = reverse(self.delete_url, args=(obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Delete for other users company
        other_obj = self.object_class.objects.filter(company=db_other_user.company)[0]

        url = reverse(self.delete_url, args=(other_obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Test querying

    def test_query_anonymous_by_datetime(self):
        """
        Anonymous user should be able to query calendar entries by date
        """

        start = (timezone.now() - datetime.timedelta(hours=1)).isoformat()
        end = (timezone.now() + datetime.timedelta(days=1)).isoformat()

        payload = {
            'start__gte': start,
            'end__lte': end,
        }

        url = reverse(self.list_url)
        response = self.client.get(url, data=payload)

        manual_query = self.object_class.objects.filter(**payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), manual_query.count())

    def test_query_anonymous_by_datetime_for_company(self):
        """
        Anonymous user should be able to query calendar entries by date for a certain company
        """
        company_id = self.companies[1].id
        start = (timezone.now() - datetime.timedelta(hours=1)).isoformat()
        end = (timezone.now() + datetime.timedelta(days=1)).isoformat()

        payload = {
            'company': company_id,
            'start__gte': start,
            'end__lte': end,
        }

        url = reverse(self.list_url)
        response = self.client.get(url, data=payload)

        manual_query = self.object_class.objects.filter(**payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), manual_query.count())
        self.assertEqual(len(response.data['results']), 1)
