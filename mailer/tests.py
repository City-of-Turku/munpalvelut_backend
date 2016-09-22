from __future__ import unicode_literals

from unittest import skipIf
from django.test import TestCase
from django.core import mail
from django.utils import translation
from django.conf import settings

from mailer.mail import send_template_mail, send_template_admin_mail, send_template_manager_mail

class MailerTest(TestCase):
    def test_mail(self):
        with translation.override('en'):
            send_template_mail('test@example.com', 'test', {'var': 'hello'})
            send_template_mail('test@example.com', 'test', {'var': 'world'}, subject="Test2")

        with translation.override('fi'):
            send_template_mail('test@example.com', 'test', {'var': 'moi'})

        self.assertEqual(len(mail.outbox), 3)

        self.assertEqual(mail.outbox[0].subject, 'Mailer test subject: "hello"')
        self.assertEqual(mail.outbox[0].body.strip(), "Mailer test: 'hello'")
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], 'test@example.com')

        self.assertEqual(mail.outbox[1].subject, 'Test2')
        self.assertEqual(mail.outbox[1].body.strip(), "Mailer test: 'world'")

        self.assertEqual(mail.outbox[2].subject, 'Mailer test subject: "moi"')
        self.assertEqual(mail.outbox[2].body.strip(), "Postitesti: 'moi'")

    @skipIf(not settings.ADMINS, "no admins configured")
    def test_admin_mail(self):
        send_template_admin_mail('admin test', 'test', {})

        self.assertEqual(len(mail.outbox), 1)

    @skipIf(not settings.MANAGERS, "no managers configured")
    def test_manager_mail(self):
        send_template_manager_mail('manager test', 'test', {})

        self.assertEqual(len(mail.outbox), 1)
