#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

import datetime
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from palvelutori import test_mixins
from palvelutori.models import User
from organisation.models import Company
from .models import Order


class OrderRatingTest(test_mixins.BasicCRUDApiTestCaseSetupMixin, APITestCase):

        object_class = Order
        object_count = 10

        rate_url = "api:user-orders-rate-detail"
        company_list_url = "api:company-list"
        order_list_url = "api:user-orders-list"

        company1 = {
            "id": 1,
            "name": "Rating Test",
            "businessid": "123456-7",
            "service_areas": ["20100", "20200"],
            "price_per_hour": 10,
            "price_per_hour_continuing": 9,
        }

        company2 = {
            "id": 2,
            "name": "Rating Test 2",
            "businessid": "654321-7",
            "service_areas": ["20100", "20200"],
            "price_per_hour": 10,
            "price_per_hour_continuing": 9,
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
            "timeslot_start": lambda x : timezone.now() - datetime.timedelta(hours=2),
            "timeslot_end": lambda x : timezone.now() + datetime.timedelta(hours=2),
            "extra_info": "",

            "company_id": company1['id'],
            "service_package_shortname": "palvelu-paketti"
        }

        @classmethod
        def setUpTestData(cls):
            cls.template_object.update({'user_id': cls.template_users['normal_user1']['id']})

            Company.objects.create(**cls.company1) # This will have 'object_count' orders
            Company.objects.create(**cls.company2) # This will have 0 orders

            super(OrderRatingTest, cls).setUpTestData()

            # 3 users:
            # - staff users
            # - normal_user1: 10 orders
            # - normal_user2: 0 orders

            # 2 companies:
            # - 1: 10 orders
            # - 2: 0 orders

        def test_when_no_ratings(self):
            """
            Rating should be None
            """

            company_ratings = {
                1: None,
                2: None
            }

            url = reverse(self.company_list_url)
            response = self.client.get(url)

            [self.assertTrue('rating' in c and company_ratings[c['id']] == c['rating']) for c in response.data['results']]

        def test_when_too_few_ratings(self):
            """
            Rating should be None.

            The system requires companies to have atleast 2 ratings before
            the rating is visible.
            """
            o = Order.objects.all()[0]
            o.rating = 5
            o.save()

            company_ratings = {
                1: None,
                2: None
            }

            url = reverse(self.company_list_url)
            response = self.client.get(url)

            [self.assertTrue('rating' in c and company_ratings[c['id']] == c['rating']) for c in response.data['results']]

        def test_when_enough_ratings(self):
            """
            Rating should be the mean of all ratings.

            Give atleast 2 ratings for a comapny.
            """
            rating_sum = 0
            rating_count = 2
            give_rating = 5
            for o in Order.objects.all()[:rating_count]:
                o.rating = give_rating
                o.save()
                rating_sum += give_rating

            rating_should_be = float(rating_sum) / float(rating_count)

            company_ratings = {
                1: rating_should_be,
                2: None
            }

            url = reverse(self.company_list_url)
            response = self.client.get(url)

            [self.assertTrue('rating' in c and company_ratings[c['id']] == c['rating']) for c in response.data['results']]

        def test_can_rate(self):
            """
            Ratings can be made and changed 24 hours after timeslot_end has passed.
            """

            user = self.template_users['normal_user1']
            self.client.login(email=user['email'], password=user['password'])
            url = reverse(self.order_list_url, kwargs={'user_pk': user['id']})

            # No order should be allowed to be rated
            # Every order's timeslot_end is in the future

            response = self.client.get(url)

            can_be_rated = sum(1 for res in response.data['results'] if res['can_be_rated'])
            can_not_be_rated = sum(1 for res in response.data['results'] if not res['can_be_rated'])

            self.assertEqual(can_be_rated, 0)
            self.assertEqual(can_not_be_rated, self.object_count)

            # 5 orders should be allowed to be rated
            # Set 5 order's timeslot_end to past

            allow_rating_count = 5
            for o in Order.objects.all()[:allow_rating_count]:
                o.timeslot_end = timezone.now() - datetime.timedelta(hours=1)
                o.save()

            response = self.client.get(url)

            can_be_rated = sum(1 for res in response.data['results'] if res['can_be_rated'])
            can_not_be_rated = sum(1 for res in response.data['results'] if not res['can_be_rated'])

            self.assertEqual(can_be_rated, allow_rating_count)
            self.assertEqual(can_not_be_rated, self.object_count - allow_rating_count)

            # 3 orders should be allowed to be rated
            # Set 2 of the previous 5 to have already been rated

            disallow_rating_count = 2
            Order.objects.all().update(rating=3, rated=timezone.now())
            for o in Order.objects.filter(timeslot_end__lte=timezone.now())[:disallow_rating_count]:
                o.rated = timezone.now() - datetime.timedelta(days=1, seconds=1)
                o.save()

            response = self.client.get(url)

            can_be_rated = sum(1 for res in response.data['results'] if res['can_be_rated'])
            can_not_be_rated = sum(1 for res in response.data['results'] if not res['can_be_rated'])

            self.assertEqual(can_be_rated, allow_rating_count - disallow_rating_count)
            self.assertEqual(can_not_be_rated, self.object_count - allow_rating_count + disallow_rating_count)

        def test_user_rating(self):
            """
            Only owner of the order can rate the order.
            """
            RATING = 3

            order = Order.objects.all()[0]

            owner_user = self.template_users['normal_user1']
            other_user = self.template_users['normal_user2']

            url = reverse(self.rate_url, kwargs={
                'pk': order.pk,
                'user_pk': owner_user['id'],
            })

            self.assertEqual(order.rating, None)
            self.assertEqual(order.rated, None)

            # Should not be allowed since timeslot_end is in the future
            self.client.login(email=owner_user['email'], password=owner_user['password'])
            response = self.client.put(url, data={'rating': RATING})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            # Set the timeslot_end to past
            order.timeslot_end = timezone.now() - datetime.timedelta(hours=1)
            order.save()

            # Other user should not be allowed
            self.client.login(email=other_user['email'], password=other_user['password'])
            response = self.client.put(url, data={'rating': RATING})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            # Owner user should not be allowed
            self.client.login(email=owner_user['email'], password=owner_user['password'])
            response = self.client.put(url, data={'rating': RATING})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            originally_rated = Order.objects.get(pk=order.pk).rated
            self.assertNotEqual(originally_rated, None)

            # The rating can be changed for 24 hour after the first rating
            response = self.client.put(url, data={'rating': RATING})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # 'rated' field should be set and the rating should be equal to RATING
            updated_order = Order.objects.get(pk=order.pk)
            self.assertEqual(updated_order.rating, RATING)
            self.assertEqual(updated_order.rated, originally_rated)

        def test_rating_min_max(self):
            """
            Rating should be between 1 and 5
            """
            Order.objects.all().update(timeslot_end=timezone.now() - datetime.timedelta(hours=1))

            owner_user = self.template_users['normal_user1']
            self.client.login(email=owner_user['email'], password=owner_user['password'])

            urls = (reverse(self.rate_url, kwargs={
                'pk': o.pk,
                'user_pk': o.user_id,
            }) for o in Order.objects.all())

            # Not ok
            response = self.client.put(next(urls), data={'rating': ''})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Not ok
            response = self.client.put(next(urls), data={'rating': 0})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # Ok
            response = self.client.put(next(urls), data={'rating': 1})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Ok
            response = self.client.put(next(urls), data={'rating': 3})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Ok
            response = self.client.put(next(urls), data={'rating': 5})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Not ok
            response = self.client.put(next(urls), data={'rating': 6})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

