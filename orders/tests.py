#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from palvelutori import test_mixins
from palvelutori.models import User
from organisation.models import Company
from services.models import ServicePackage
from .models import Order

from copy import deepcopy

class OrderTest(test_mixins.BasicCRUDApiTestCaseSetupMixin, APITestCase):

    object_class = Order

    list_url_user = "api:user-orders-list"
    list_url_company = "api:company-orders-list"
    detail_url_user = "api:user-orders-detail"
    detail_url_company = "api:company-orders-detail"
    create_url_user = list_url_user
    create_url_company = list_url_company
    update_url_user = detail_url_user
    update_url_company = detail_url_company
    delete_url_user = detail_url_user
    delete_url_company = detail_url_company

    company = {
        "id": 1,
        "name": "Image Test",
        "businessid": "123456-7",
        "service_areas": ["20100", "20200"],
        "price_per_hour": 10,
        "price_per_hour_continuing": 9,
    }

    service_package = {
        "id": 1,
        "shortname": "palvelu-paketti",
        "pricing_formula": "???",
        "website": "example.com"
    }

    template_object = {
        "user_first_name": "Test",
        "user_last_name": "User",
        "user_email": "test@example.com",
        "user_phone": "+12345678",

        "site_address_street": "Ääkköskatu 3",
        "site_address_street2": "",
        "site_address_postalcode": "12345",
        "site_address_city": "Helsinki",
        "site_room_count": 4,
        "site_sanitary_count": 1,
        "site_floor_count": 1,
        "site_floor_area": 80.4,

        "duration": 4,
        "price": 400,
        "timeslot_start": "2016-10-10T07:00:00Z",
        "timeslot_end": "2016-10-10T11:00:00Z",
        "extra_info": "",

        "company_id": company['id'],
        "service_package_id": service_package['id'],
        "service_package_shortname": "palvelu-paketti"
    }

    @classmethod
    def setUpTestData(cls):
        template_users = deepcopy(cls.template_users)
        template_users['normal_user2'].update({'company_id': cls.company['id']})
        cls.template_users = template_users

        template_object = deepcopy(cls.template_object)
        template_object.update({'user_id': cls.template_users['normal_user1']['id']})
        cls.template_object = template_object

        Company.objects.create(**cls.company)
        ServicePackage.objects.create(**cls.service_package)

        super().setUpTestData()

    # List

    def test_list_anonymous(self):
        """
        Anonymous user should NOT be able to list
        """
        # User orders
        url = reverse(self.list_url_user, kwargs={'user_pk': self.template_users['normal_user1']['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Company orders
        url = reverse(self.list_url_company, kwargs={'company_pk': self.company['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_normal_user(self):
        """
        User should be able to list own orders
        """
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(self.list_url_user, kwargs={'user_pk': user['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

        # Company orders
        url = reverse(self.list_url_company, kwargs={'company_pk': self.company['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_company_user(self):
        """
        Company user should be able to list own companys orders
        """
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(self.list_url_user, kwargs={'user_pk': self.template_users['normal_user1']['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Company orders
        url = reverse(self.list_url_company, kwargs={'company_pk': self.company['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

    def test_list_staff_user(self):
        """
        Staff user should be able to list all orders
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(self.list_url_user, kwargs={'user_pk': self.template_users['normal_user1']['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

        # Company orders
        url = reverse(self.list_url_company, kwargs={'company_pk': self.company['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

    # Retrieve

    def test_detail_anonymous(self):
        """
        Anonymous user should NOT be able to retrieve
        """
        obj = self.objects[0]

        # User orders
        url = reverse(
            self.detail_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Company orders
        url = reverse(
            self.detail_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_normal_user(self):
        """
        User should be able to retrieve own orders
        """
        obj = self.objects[0]
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(
            self.detail_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Company orders
        url = reverse(
            self.detail_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_company_user(self):
        """
        Company user should be able to retrieve own companys orders
        """
        obj = self.objects[0]
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(
            self.detail_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Company orders
        url = reverse(
            self.detail_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_staff_user(self):
        """
        Staff user should be able to retrieve all orders
        """
        obj = self.objects[0]
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        # User orders
        url = reverse(
            self.detail_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Company orders
        url = reverse(
            self.detail_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Create

    def test_create_user_order(self):
        """
        Anonymous users should not be able to create.
        User should be able to create orders for him/herself.
        Staff users should be able to create for other users.
        """
        TEST_STR = 'Luonti testi'

        payload = self.template_object.copy()
        payload.pop('company_id', None)
        payload.pop('service_package_id', None)
        payload.update({
            'company': self.company['id'],
            'service_package': self.service_package['id'],
            'extra_info': TEST_STR
        })

        url = reverse(
            self.create_url_user,
            kwargs={ 'user_pk': self.template_users['normal_user1']['id'] }
        )

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['extra_info'], TEST_STR)

        # Other user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        payload['extra_info'] = ''
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['extra_info'], '')

        # Two messages should have been sent
        self.assertEqual(len(mail.outbox), 2)

    def test_create_company_order(self):
        """
        Company orders can not be created.
        """
        TEST_STR = 'Luonti testi'

        payload = self.template_object.copy()
        payload.pop('company_id', None)
        payload.pop('service_package_id', None)
        payload.update({
            'user': self.template_users['normal_user1']['id'],
            'service_package': self.service_package['id'],
            'extra_info': TEST_STR
        })

        url = reverse(
            self.create_url_company,
            kwargs={ 'company_pk': self.company['id'] }
        )

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Other user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Update

    def test_update_user_orders(self):
        """
        No one should be able to update user orders
        """
        obj = self.objects[0]

        url = reverse(
            self.update_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )

        # Anonymous user
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Other user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_company_orders(self):
        """
        No one should be able to update company orders
        """
        obj = self.objects[0]

        url = reverse(
            self.update_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )
        # Anonymous user
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Other user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Delete

    def test_delete_user_orders(self):
        """
        No one should be able to delete orders
        """
        obj = self.objects[0]

        url = reverse(
            self.delete_url_user,
            kwargs={
                'pk': obj.id,
                'user_pk': obj.user_id
            }
        )

        # Anonymous user
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Other user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    def test_delete_company_orders(self):
        """
        No one should be able to delete orders
        """
        obj = self.objects[0]

        url = reverse(
            self.delete_url_company,
            kwargs={
                'pk': obj.id,
                'company_pk': obj.company_id
            }
        )

        # Anonymous user
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Owner user
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Other user
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Staff user
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
