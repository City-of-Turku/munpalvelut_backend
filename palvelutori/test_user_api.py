#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase

from decimal import Decimal

from .test_mixins import BasicCRUDApiTestCaseMixin, BasicCRUDApiTestCaseSetupMixin
from .models import UserSite

class UserTestCase(BasicCRUDApiTestCaseSetupMixin, APITestCase):
    def test_login(self):
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        # Check the /me/ page
        response = self.client.get(reverse('api:user-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_case_insensitive_login(self):
        user = self.template_users['staff_user']
        self.client.login(email=user['email'].upper(), password=user['password'])
        response = self.client.get(reverse('api:user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_password_change(self):
        admin = self.template_users['staff_user']
        user = self.template_users['normal_user1']

        # Unauthenticated user shouldn't be able to change anything
        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': user['id']}),
            data={'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # A regular user can change their own password (but only if the old password is correct)
        self.client.login(email=user['email'], password=self.template_users['normal_user1']['password'])
        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': user['id']}),
            data={'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': user['id']}),
            data={'old_password': user['password'], 'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

        # But not anyone else's
        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': admin['id']}),
            data={'old_password': admin['password'], 'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Admins can change anyone's password (without needing the old password)
        self.client.login(email=admin['email'], password=self.template_users['staff_user']['password'])

        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': user['id']}),
            data={'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

        # Even admins need to submit the old password when changing their own
        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': admin['id']}),
            data={'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(
            reverse('api:user-change-password', kwargs={'pk': admin['id']}),
            data={'old_password': admin['password'], 'new_password': 'abc'}
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

    def test_password_recovery_email(self):
        user = self.template_users['normal_user1']

        # Request password reset
        response = self.client.post(reverse('api:forgotten-password'), {
            'email': user['email']
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        msg = mail.outbox[0].body
        token = msg[msg.index('?token=')+7:msg.index('&email')]

        # Reset with wrong token shouldn't work
        newpasswd = user['password'][::-1]
        reseturl = reverse('api:reset-password')

        response = self.client.post(reseturl, {
            'email': user['email'],
            'token': 'wrong',
            'new_password': newpasswd,
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.client.login(email=user['email'], password=newpasswd))

        # With correct token it should
        response = self.client.post(reseturl, {
            'email': user['email'],
            'token': token,
            'new_password': newpasswd,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(email=user['email'], password=newpasswd))

    def test_password_recovery_vetuma(self):
        user = self.template_users['normal_user1']

        # Reset with wrong token shouldn't work
        newpasswd = user['password'][::-1]
        reseturl = reverse('api:reset-password')

        response = self.client.post(reseturl, {
            'email': user['email'],
            'vetuma': 'wrong',
            'new_password': newpasswd,
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.client.login(email=user['email'], password=newpasswd))

        # With correct token it should
        response = self.client.post(reseturl, {
            'email': user['email'],
            'vetuma': user['vetuma'],
            'new_password': newpasswd,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(email=user['email'], password=newpasswd))

class UserSitesApiTestCase(BasicCRUDApiTestCaseMixin, APITestCase):
    object_class = UserSite

    list_url = 'api:user-site-list'
    detail_url = 'api:user-site-detail'
    create_url = 'api:user-site-list'
    update_url = 'api:user-site-detail'
    delete_url = 'api:user-site-detail'

    template_object = {
        'address_street': 'Testiääkköskatu 1',
        'address_postalcode': '12345',
        'address_city': 'Turku',
        'address_country': 'FIN',
        'floor_area': Decimal('100.00')
    }

    create_object = {
        'address_street': 'Testiääkköskatu 3',
        'address_postalcode': '12345',
        'address_city': 'Turku',
        'address_country': 'FIN',
        'room_count': '4',
        'sanitary_count': '1',
        'floor_count': '1',
        'floor_area': Decimal('84.00')
    }

    update_object = {
        'floor_area': Decimal('150.00')
    }

    @classmethod
    def get_object_templates(cls):
        return [dict(user=u, **cls.template_object.copy()) for u in cls.user_class.objects.all()]

    # List tests

    def test_list_logged_in(self):
        """
        Normal user should be able to list ONLY his/her own user-sites
        """
        user = self.template_users['normal_user1']

        self.client.login(email=user['email'], password=user['password'])

        response = self.client.get(reverse(self.list_url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        for usersite in response.data['results']:
            self.assertEqual(usersite['user'], user['id'])
            self.assertIn('created', usersite)

    # Detail view tests

    def test_detail_logged_in(self):
        """
        Normal user should be able to view ONLY his/her own user-sites
        """
        user = self.template_users['normal_user1']

        usersite = None
        for site in self.objects:
            if site.user.email == user['email']:
                usersite = site
                break

        self.client.login(email=user['email'], password=user['password'])

        url = reverse(self.detail_url, args=(usersite.id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], usersite.id)
        self.assertEqual(response.data['user'], user['id'])
        self.assertIn('created', response.data)

        other_usersite = None
        for site in self.objects:
            if site.user.email != user['email']:
                other_usersite = site
                break

        url = reverse(self.detail_url, args=(other_usersite.id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Create view tests

    def test_create_logged_in(self):
        """
        Normal user should be able to create user-sites ONLY for themselves
        """
        user = self.template_users['normal_user1']
        other_user = self.template_users['normal_user2']

        self.client.login(email=user['email'], password=user['password'])

        # Create site for this user
        payload = self.create_object.copy()

        response = self.client.post(reverse(self.create_url), data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], user['id'])
        self.assertIn('id', response.data)
        self.assertIn('created', response.data)

        # Try to create for another user, should be forced for this user instead
        payload.update({'user': other_user['id']})

        response = self.client.post(reverse(self.create_url), data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], user['id'])
        self.assertIn('id', response.data)
        self.assertIn('created', response.data)

    def test_create_staff_user(self):
        """
        Staff user should be able to create user-sites for EVERYONE
        """
        user = self.template_users['staff_user']
        other_user = self.template_users['normal_user2']

        self.client.login(email=user['email'], password=user['password'])

        # Create site for this user
        payload = self.create_object.copy()

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], user['id'])
        self.assertIn('id', response.data)
        self.assertIn('created', response.data)

        # Try to create for another user, should be able to
        payload.update({'user': other_user['id']})

        response = self.client.post(reverse(self.create_url), data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], other_user['id'])
        self.assertIn('id', response.data)
        self.assertIn('created', response.data)

    # Update view tests

    def test_update_logged_in(self):
        """
        Normal user should be able to update ONLY his/her own user-sites
        """
        user = self.template_users['normal_user1']
        other_user = self.template_users['normal_user2']

        self.client.login(email=user['email'], password=user['password'])

        # Update own
        obj = None
        for o in self.objects:
            if o.user.email == user['email']:
                obj = o
                break

        update = self.update_object.copy()
        [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

        payload = self.template_object.copy()
        payload.update(update)

        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], user['id'])
        self.assertEqual(response.data['id'], obj.id)
        self.assertIn('created', response.data)
        [self.assertEqual(response.data[k], v) for k,v in update.items()]
        [self.assertNotEqual(response.data[k], getattr(obj, k)) for k,v in update.items()]

        # Update other users site
        other_obj = None
        for o in self.objects:
            if o.user.email != user['email']:
                other_obj = o
                break

        [self.assertNotEqual(getattr(other_obj, k), v) for k,v in update.items()]

        url = reverse(self.update_url, args=(other_obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Delete view tests

    def test_delete_logged_in(self):
        """
        Normal user should be able to delete ONLY his/her own user-sites
        """
        user = self.template_users['normal_user1']
        other_user = self.template_users['normal_user2']

        self.client.login(email=user['email'], password=user['password'])

        # Delete own site
        obj = None
        for o in self.objects:
            if o.user.email == user['email']:
                obj = o
                break

        url = reverse(self.delete_url, args=(obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Delete other users site
        other_obj = None
        for o in self.objects:
            if o.user.email != user['email']:
                other_obj = o
                break

        url = reverse(self.delete_url, args=(other_obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
