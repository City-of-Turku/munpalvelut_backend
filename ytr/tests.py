from django.test import TestCase

from ytr import parser
from organisation.models import Company, Address

import os
import json

# Create your tests here.
class ParserTest(TestCase):

    def test_company_import(self):
        parser.import_company_resultset(get_example('yritykset-2467503-7.json'))

        company = Company.objects.all()[0]

        self.assertEqual(company.businessid, '2467503-7')
        self.assertEqual(company.name, 'MKV Siistix')
        self.assertEqual(company.phone, '045-2550222')
        self.assertEqual(company.email, 'varhominna@hotmail.com')

        addr = company.addresses.all()[0]

        self.assertEqual(addr.streetAddress, 'Juvantie 145')
        self.assertEqual(addr.addressType, Address.TYPE_SNAILMAIL)
        self.assertEqual(addr.postalcode, '21450')
        self.assertEqual(addr.city, 'Tarvasjoki')
        self.assertEqual(addr.country, 'FI')

def get_example(name):
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'examples',
        'ytr',
        name
        )

    with open(path, 'r') as f:
        return json.load(f)
