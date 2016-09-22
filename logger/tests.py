from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from palvelutori.test_mixins import BasicCRUDApiTestCaseSetupMixin
from logger.models import LogEntry

class LoggerTestCase(BasicCRUDApiTestCaseSetupMixin, APITestCase):
    object_class = LogEntry
    template_object = {
        'message': 'test0',
        'severity': 0,
        'category': 'testcase',
        'ip': '127.0.0.1',
        'user_id': lambda x : x+1,
    }
    object_count = 3

    def test_anonymous(self):
        """Anonymous users are allowed to write, but not view, log entries."""
        url = reverse('api:log-list')

        # Test log entry creation
        data = {
            'message': 'Anon test',
            'severity': 0,
            'category': 'test',
            }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry = LogEntry.objects.filter(user__isnull=True)[0]
        self.assertEqual(entry.message, data['message'])
        self.assertEqual(entry.severity, data['severity'])
        self.assertEqual(entry.category, data['category'])

        # No log entries should be visible through the API, though
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Deletion should not be possible
        response = self.client.post(reverse('api:log-erase'), {
            'before': str(timezone.now()),
            'max_severity': LogEntry.ERROR,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user(self):
        """Regular users can write and view their own log entries."""
        url = reverse('api:log-list')

        # Test creation
        user = self.template_users['normal_user1']
        self.client.login(email=user['email'], password=user['password'])

        response = self.client.post(url, {
            'message': 'Anon test',
            'severity': 0,
            'category': 'test',
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # We should see two entries: the pre-built test entry and the
        # one we just created
        response = self.client.get(url)
        self.assertEqual(response.data['count'], 2)

        # Deletion should not be possible
        response = self.client.post(reverse('api:log-erase'), {
            'before': str(timezone.now()),
            'max_severity': LogEntry.ERROR,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user(self):
        """Users with extra permissions may view and delete log entries created
        by other users."""
        user = self.template_users['staff_user']
        self.client.login(email=user['email'], password=user['password'])

        # Admins can see everything
        response = self.client.get(reverse('api:log-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.object_count)

        # Deletion should be possible
        response = self.client.post(reverse('api:log-erase'), {
            'before': str(timezone.now()),
            'max_severity': LogEntry.ERROR,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted'], self.object_count)
        self.assertEqual(LogEntry.objects.count(), 0)
