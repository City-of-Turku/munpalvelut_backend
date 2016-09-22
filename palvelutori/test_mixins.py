#!/usr/bin/env python
# coding=utf-8

from django.core.urlresolvers import reverse
from rest_framework import status
from .models import User

from collections import OrderedDict

STR_401_MESSAGE = 'Authentication credentials were not provided.'
STR_403_MESSAGE = 'You do not have permission to perform this action.'

class BasicCRUDApiTestCaseSetupMixin(object):
    user_class = User
    object_class = None
    object_count = 3

    list_url = str()
    detail_url = str()
    create_url = str()
    update_url = str()
    delete_url = str()

    template_users = {
        'staff_user': {
            'id': 1,
            'email': 'staff@example.com',
            'password': '123456',
            'is_staff': True,
            'is_superuser': True,
        },
        'normal_user1': {
            'id': 2,
            'email': 'user1@example.com',
            'password': '1234',
            'vetuma': 'vet321',
        },
        'normal_user2': {
            'id': 3,
            'email': 'user2@example.com',
            'password': '12345'
        }
    }

    template_object = dict()
    update_object = dict()
    create_object = dict()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Generate Users
        cls.users = cls.generate_users(cls.get_user_templates())

        # Generate objects
        cls.objects = cls.generate_objects(cls.get_object_templates())

    @classmethod
    def get_user_templates(cls):
        return cls.template_users.values()

    @classmethod
    def get_object_templates(cls):
        if cls.template_object:
            return [cls.get_object_template(cls.template_object, idx) for idx in range(cls.object_count)]
        else:
            return None

    @classmethod
    def get_object_template(cls, tpl, idx):
        tpl = tpl.copy()
        for key in tpl.keys():
            if hasattr(tpl[key], '__call__'):
                tpl[key] = tpl[key](idx)

        return tpl

    @classmethod
    def generate_users(cls, templates):
        return [cls.user_class.objects.create_user(**t) for t in templates]

    @classmethod
    def generate_objects(cls, templates):
        if templates:
            return [cls.object_class.objects.create(**t) for t in templates]

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_setup(self):
        """
        Setup should have created a list of objects and users to use in tests.
        """
        self.assertTrue(len(self.users) > 0)
        self.assertTrue(self.objects is None or len(self.objects) > 0)


class BasicReadApiTestCaseRunMixin(object):
    # List tests

    def test_list_anonymous(self):
        """
        Anonymous user should NOT be able to list
        """
        url = reverse(self.list_url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('results', response.data)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], STR_401_MESSAGE)

    def test_list_staff_user(self):
        """
        Staff user should be able to list EVERY object
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        url = reverse(self.list_url)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), len(self.objects))

    # Detail view tests

    def test_detail_anonymous(self):
        """
        Anonymous user should NOT be able to view details
        """
        obj = self.objects[0]

        url = reverse(self.detail_url, args=(obj.id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], STR_401_MESSAGE)

    def test_detail_staff_user(self):
        """
        Staff user should be able to view EVERY object
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        for obj in self.objects:
            url = reverse(self.detail_url, args=(obj.id,))
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('id', response.data)


class BasicCreateApiTestCaseRunMixin(object):
    def test_create_anonymous(self):
        """
        Anonymous user should NOT be able to create
        """
        payload = self.create_object.copy()

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], STR_401_MESSAGE)

    def test_create_staff_user(self):
        """
        Staff user should be able to create objects
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        payload = self.create_object.copy()

        url = reverse(self.create_url)
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)


class BasicUpdateApiTestCaseRunMixin(object):
    def test_update_anonymous(self):
        """
        Anonymous user should NOT be able to update
        """
        obj = self.objects[0]

        update = self.update_object.copy()
        [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

        payload = self.get_object_template(self.template_object, 0)
        payload.update(update)

        url = reverse(self.update_url, args=(obj.id,))
        response = self.client.put(url, data=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], STR_401_MESSAGE)

    def test_update_staff_user(self):
        """
        Staff user should be able to update EVERY object
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        update = self.update_object.copy()

        payload = self.get_object_template(self.template_object, 0)
        payload.update(update)

        for obj in self.objects:
            [self.assertNotEqual(getattr(obj, k), v) for k,v in update.items()]

            url = reverse(self.update_url, args=(obj.id,))
            response = self.client.put(url, data=payload)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['id'], obj.id)

            [self.assertEqual(_normalize_response(response.data[k]), v) for k,v in update.items()]
            [self.assertNotEqual(_normalize_response(response.data[k]), getattr(obj, k)) for k,v in update.items()]

def _normalize_response(obj):
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = _normalize_response(v)

    elif isinstance(obj, OrderedDict):
        return _normalize_response(dict(obj))

    elif isinstance(obj, dict):
        obj2 = {}
        for k, v in obj.items():
            obj2[str(k) if isinstance(k, str) else k] = _normalize_response(v)
        obj = obj2

    elif isinstance(obj, str):
        return str(obj)

    return obj

class BasicDeleteApiTestCaseRunMixin(object):
    def test_delete_anonymous(self):
        """
        Anonymous user should NOT be able to delete
        """
        obj = self.objects[0]

        url = reverse(self.delete_url, args=(obj.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], STR_401_MESSAGE)

    def test_delete_staff_user(self):
        """
        Staff user should be able to delete EVERY object
        """
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        for obj in self.objects:
            url = reverse(self.delete_url, args=(obj.id,))
            response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class BasicCRUDApiTestCaseRunMixin(BasicReadApiTestCaseRunMixin,
                                   BasicCreateApiTestCaseRunMixin,
                                   BasicUpdateApiTestCaseRunMixin,
                                   BasicDeleteApiTestCaseRunMixin):
    pass


class BasicCRUDApiTestCaseMixin(BasicCRUDApiTestCaseRunMixin, BasicCRUDApiTestCaseSetupMixin):
    """
    Test basic CRUD retrieve and list actions for anonymous users and staff users.
    Other users actions are usually more complicated so those have to be written
    per case.
    """
