from django.core.urlresolvers import reverse
from django.core import mail

from rest_framework.test import APITestCase
from rest_framework import status

from palvelutori.test_mixins import BasicCRUDApiTestCaseSetupMixin

class FeedbackTest(BasicCRUDApiTestCaseSetupMixin, APITestCase):
    def test_feedbackform(self):
        # Unauthenticated users should not be able to send any feedback
        response = self.__send_feedback()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # But authenticated users should
        user = self.template_users['normal_user1']

        self.client.login(email=user['email'], password=user['password'])
        response = self.__send_feedback()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)

        # Check that the content actually ends up in the message
        self.assertIn('Hello World', mail.outbox[0].body)

    def __send_feedback(self):
        url = reverse('api:feedback-list')

        return self.client.post(url, data={
            'subject': 'Test',
            'message': 'Hello World'
            })
