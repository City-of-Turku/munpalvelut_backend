#!/usr/bin/env python
# coding=utf-8

from unittest import skipUnless
import os
import subprocess
import json
import filecmp
import datetime

from django.test import LiveServerTestCase
from django.conf import settings
from django.utils import timezone

from api.models import AuthToken
from palvelutori.models import User
from organisation.models import Company, Picture as CompanyPicture
from calendars.models import CalendarEntry
from services.models import ServicePackage
from orders.models import Order

class CurlError(Exception):
    pass

@skipUnless(settings.TEST_EXAMPLES, "Curl example tests disabled")
class CurlExampleTest(LiveServerTestCase):
    """Make sure the curl API examples work."""

    def test_login(self):
        reply = self.__curl('user-login.sh')

        self.assertIn('token', reply)

    def test_logout(self):
        reply = self.__curl('user-logout.sh')
        self.assertIn('status', reply)

    def test_password_change(self):
        reply = self.__curl('user-change-password.sh', USER_ID=str(self.__user.id))
        self.assertIn('status', reply)

    def test_password_reset_vetuma(self):
        reply = self.__curl('user-reset-password-vetuma.sh', USER_ID=str(self.__user.id))
        self.assertIn('status', reply)

    def test_calendarentry_create(self):
        reply = self.__curl('calendarentry-create.sh', COMPANY_ID=str(self.__company.id))
        self.assertIn('id', reply)

    def test_calendarentry_delete(self):
        cal = CalendarEntry.objects.create(
            start=timezone.now(),
            end=timezone.now(),
            company=self.__company
        )

        reply = self.__curl('calendarentry-delete.sh', expect_json=False, ID=str(cal.id))
        self.assertEquals(len(reply), 0)

    def test_company_picture_upload(self):
        reply = self.__curl('company-picture-upload.sh', COMPANY_ID=str(self.__company.id))

        self.assertIn('image', reply)

        # Company should now have the test1 sample image
        pic = CompanyPicture.objects.filter(company=self.__company)[0]

        self.assertTrue(filecmp.cmp(pic.image.image.path, os.path.join(self.__testimageroot, 'test1.png'), shallow=False))

    def test_order_create(self):
        reply = self.__curl('order-create.sh',
            USER_ID=str(self.__user.id),
            COMPANY_ID=str(self.__company.id),
            SERVICE_PACKAGE_ID=str(self.__service_package.id)
        )
        self.assertIn('id', reply)

    def test_order_list_user(self):
        reply = self.__curl('order-list-user.sh',
            USER_ID=str(self.__user.id)
        )
        self.assertIn('results', reply)

    def test_order_list_company(self):
        reply = self.__curl('order-list-company.sh',
            COMPANY_ID=str(self.__company.id)
        )
        self.assertIn('results', reply)

    def test_order_rate(self):
        reply = self.__curl('order-rate.sh',
            USER_ID=str(self.__user.id),
            ORDER_ID=str(self.__order.id)
        )
        self.assertIn('id', reply)

    def test_feedback_send(self):
        reply = self.__curl('feedback-send.sh')
        self.assertEquals(reply['status'], 'ok')

    def setUp(self):
        # Create test objects
        self.__company = Company.objects.create(
            name="Image Test",
            businessid="123456-7",
            service_areas=["20100", "20200"],
            price_per_hour=10,
            price_per_hour_continuing=9,
            )

        self.__user = User.objects.create_user(
            email='test@example.com',
            password='abcd1234',
            first_name='Test',
            last_name='User',
            is_verified=True,
            vetuma='vet321',
            company=self.__company
            )

        self.__service_package = ServicePackage.objects.create(
            shortname='palvelu-paketti',
            pricing_formula='???',
            website='example.com'
        )

        self.__order = Order.objects.create(**{
            "user_id": self.__user.pk,
            "user_first_name": self.__user.first_name,
            "user_last_name": self.__user.last_name,
            "user_email": self.__user.email,
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
            "timeslot_start": timezone.now() - datetime.timedelta(hours=2),
            "timeslot_end": timezone.now() - datetime.timedelta(hours=1),
            "extra_info": "",

            "company_id": self.__company.pk,
            "service_package_id": self.__service_package.pk,
            "service_package_shortname": self.__service_package.shortname
        })

        self.__token = AuthToken.objects.create(key="test", user=self.__user)

        # Location of our example scripts
        self.__scriptroot = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'examples',
            'curl'
            )
        self.__testimageroot = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'media',
            'test_images'
            )

    def __curl(self, scriptname, expect_json=True, **extra_env):
        path = os.path.join(self.__scriptroot, scriptname)
        env = os.environ.copy()
        env['APIROOT'] = self.live_server_url
        env['TOKEN'] = self.__token.key
        env.update(extra_env)

        with open('/dev/null', 'w') as devnull:
            proc = subprocess.Popen([path],
                                    cwd=self.__scriptroot,
                                    env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=devnull
                                    )

            out = proc.communicate()[0]

        if proc.returncode != 0:
            raise CurlError(scriptname + " failed")

        if expect_json:
            return json.loads(out.decode('utf-8'))
        else:
            return out
