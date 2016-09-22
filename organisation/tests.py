#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from palvelutori import test_mixins
from .models import Company

from copy import deepcopy
from ytr import client

class CompanyTest(test_mixins.BasicUpdateApiTestCaseRunMixin,
                  test_mixins.BasicCRUDApiTestCaseSetupMixin,
                  APITestCase):
    object_class = Company

    list_url = 'api:company-list'
    detail_url = 'api:company-detail'
    update_url = 'api:company-detail'

    template_object = {
        'name': 'Test company',
        'businessid': lambda x : '1234567-' + str(x),
        'service_areas': ['20100', '20200', '20300'],
        'price_per_hour': '10.0',
        'price_per_hour_continuing': '9.5',
    }

    update_object = {
        'name': 'Testifirma',
        'description': {
            'fi': 'Yritys (täysi kuvaus)',
            'en': 'Company (full description)',
        },
        'shortdescription': {
            'fi': 'Yritys',
            'en': 'Company',
        },
        'service_hours': {
            'fi': 'avoinna joka päivä',
            'en': 'open every day',
        },
        'price_per_hour': '11.00',
        'price_per_hour_continuing': '8.00',
        'service_areas': ['20000', '20500'],
        'email': 'test@example.com',
        'phone': '+358 124 45678',
        'addresses': [
            {
                "name": "test",
                "addressType": "snailmail",
                "streetAddress": "Testikatu 1",
                "streetAddress2": "",
                "streetAddress3": "",
                "subregion": "",
                "postalcode": "20100",
                "city": "Turku",
                "country": "FI",
                'postbox': '',
            }
        ],
        'links': [
            {
                'linktype': 'other',
                'description': 'Test',
                'url': 'http://example.org'
            },
            {
                'linktype': 'youtube',
                'description': 'Youtube',
                'url': 'http://youtube.com/'
            },
        ],
    }

    def test_user_attachment(self):
        usr = self.users[0]
        usr.company = self.objects[0]
        usr.save()

        # User should now be attached to company 0
        url = reverse('api:company-users-list', kwargs={'company_pk': self.objects[0].id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], usr.id)

        # No users have been added to company 1
        url = reverse('api:company-users-list', kwargs={'company_pk': self.objects[1].id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_hiding(self):
        self.objects[0].active = False
        self.objects[0].save()

        url = reverse('api:company-list')
        response = self.client.get(url)

        for company in response.data['results']:
            self.assertNotEqual(company['id'], self.objects[0])

    def test_blank_descriptions(self):
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        update = deepcopy(self.update_object)
        update['shortdescription']['se'] = ''
        update['links'].append({
            'linktype': 'web',
            'url': ''
        })

        obj = self.objects[0]
        payload = self.get_object_template(self.template_object, 0)
        payload.update(update)

        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search(self):
        self.objects[0].active = False
        self.objects[0].save()

        url = reverse('api:company-list')
        response = self.client.get(url, data={'search': 'Test'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects)-1)
