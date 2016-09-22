#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from unittest import skip
from rest_framework import status
from rest_framework.test import APITestCase
from palvelutori.test_mixins import (
                    BasicCRUDApiTestCaseSetupMixin, BasicCRUDApiTestCaseMixin,
                    STR_401_MESSAGE, STR_403_MESSAGE)
from . import models

STR_RATING_MESSAGE = 'Hienoa työtä!'
STATIC_RATING = 4

@skip("CompanyRating endpoint is not used anymore")
class CompanyRatingApiTestCase(BasicCRUDApiTestCaseSetupMixin, APITestCase):
    object_class = models.CompanyRating

    list_url = 'api:companyratings-list'
    detail_url = 'api:companyratings-detail'
    create_url = 'api:companyratings-list'
    update_url = 'api:companyratings-detail'
    delete_url = 'api:companyratings-detail'

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
        'message': STR_RATING_MESSAGE,
        'rating': STATIC_RATING
    }
    update_object = {
        'rating': STATIC_RATING + 1
    }

    @classmethod
    def setUpTestData(cls):
        # Set company in template object
        cls.template_object.update({'company': cls.template_companies[0]['id']})

        # Generate companies
        cls.companies = [models.Company.objects.create(**c) for c in cls.template_companies]

        super(CompanyRatingApiTestCase, cls).setUpTestData()

    @classmethod
    def get_object_templates(cls):
        user = cls.user_class.objects.get(id=cls.template_users['normal_user2']['id'])
        company = models.Company.objects.get(id=cls.template_object['company'])

        d = cls.template_object.copy()
        d.update({
            'user': user, # Generate all ratings for this user
            'company': company
        })
        return [d.copy() for _ in range(4)]

    # Company views
    def test_company_rating_list(self):
        """
        Ratings should be listed in company detail view.
        Ratings should not include id or user information.
        """
        url = reverse('api:company-detail', args=(self.template_object['company'],))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ratings', response.data)
        self.assertEqual(len(response.data['ratings']), len(self.objects))
        [self.assertNotIn('user', r) for r in response.data['ratings']]
        [self.assertNotIn('id', r) for r in response.data['ratings']]

    # Validation

    def test_rating_range(self):
        """
        Only ratings between 1 to 5 are allowed.
        """
        url = reverse(self.create_url)
        payload = self.template_object.copy()

        payload.update({'rating': None})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], None)

        payload.update({'rating': 0})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        payload.update({'rating': 1})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 1)

        payload.update({'rating': 5})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)

        payload.update({'rating': 6})
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # List and detail

    def test_can_view_only_own_detail(self):
        """
        Anonymous user can not view any rating.
        Logged in user can view details of only their own ratings.
        Staff user has no special privileges.
        """
        obj = self.objects[0]
        url = reverse(self.detail_url, args=(obj.id,))

        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Logged in user with no ratings
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Logged in user with ratings
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], user['id'])

        # Staff user (has no ratings)
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_can_list_only_own(self):
        """
        Anonymous user can not list any rating.
        Logged in user can list only their own ratings.
        Staff user has no special privielegs.
        """
        url = reverse(self.list_url)

        # Anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

        # Logged in user with no ratings
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

        # Logged in user with ratings
        user = self.template_users['normal_user2']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(filter(lambda o: o.user_id == user['id'], self.objects)))

        # Staff user (has no ratings)
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    # Anonymous create, update and delete

    def test_anonymous_can_create(self):
        payload = self.template_object.copy()

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], STR_RATING_MESSAGE)
        self.assertEqual(response.data['rating'], STATIC_RATING)
        self.assertEqual(response.data['user'], None)

    def test_anonymous_can_not_create_for_another_user(self):
        payload = self.template_object.copy()
        payload.update({
            'user': self.template_users['normal_user1']['id'], # This should be ignored
            'user_id': self.template_users['normal_user1']['id'], # This should be ignored
        })

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], None)

    def test_anonymous_can_not_update_or_delete(self):
        obj = self.objects[0]

        update = self.update_object.copy()
        [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

        payload = self.template_object.copy()
        payload.update(update)

        # Update
        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Delete
        url = reverse(self.delete_url, args=(obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Logged in create, update and delete

    def test_logged_in_can_create_update_and_delete_own(self):
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])

        # Create
        payload = self.template_object.copy()

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], STR_RATING_MESSAGE)
        self.assertEqual(response.data['rating'], STATIC_RATING)
        self.assertEqual(response.data['user'], user['id'])

        # Update
        obj = response.data

        update = self.update_object.copy()
        [self.assertNotEqual(obj[k], v) for k,v in update.items()]

        payload = self.template_object.copy()
        payload.update(update)

        url = reverse(self.update_url, args=(obj['id'],))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], obj['id'])
        [self.assertEqual(response.data[k], v) for k,v in update.items()]
        [self.assertNotEqual(response.data[k], obj[k]) for k,v in update.items()]

        # Delete
        url = reverse(self.delete_url, args=(obj['id'],))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logged_in_can_not_create_update_or_delete_for_another_user(self):
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])

        # Create
        payload = self.template_object.copy()
        payload.update({
            'user': self.template_users['normal_user2']['id'], # This should be ignored
            'user_id': self.template_users['normal_user2']['id'], # This should be ignored
        })

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], user['id'])

        # Update
        obj = self.objects[0]

        update = self.update_object.copy()
        [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

        payload = self.template_object.copy()
        payload.update(update)

        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Delete
        url = reverse(self.delete_url, args=(obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
