from organisation.models import Company, Address, YTRCompany

import logging
logger = logging.getLogger(__name__)

def import_company_resultset(node, overwrite=False):
    out = []
    for company in node['haeYrityksetResult']['yritykset']['yritys']:
        out.append(import_company(company, overwrite=overwrite))
    return out


def import_company(node, overwrite=False):
    """Import a company from the given "Yritys" node.
    If the company already exists, AlreadyExist is raised.
    If the parameter overwrite is set to True, the existing
    company's information will be updated from the node.
    """

    businessid = node['yritysTunnus']

    try:
        company = Company.objects.get(businessid=businessid)

        if not overwrite:
            logger.info("Company {} already imported. Skipping.".format(businessid))
            return

    except Company.DoesNotExist:
        company = Company(
            businessid=businessid,
            service_areas=[],
            price_per_hour=None,
            price_per_hour_continuing=None,
            )
        company._new = True

    company.name = node['name']

    # Currently, we only have one email address and phone number
    emails = node.get('sahkoisetYhteystiedot', {}).get('organisaatioSahkoinenYhteystieto', [])
    for email in emails:
        if int(email['yhteystietoTyyppi']['code']) == 1:
            company.email = email['yhteystieto']
            break

    phones = node.get('puhelinnumerot', {}).get('organisaatioPuhelinnumero', [])
    for phone in phones:
        if int(phone['puhelinnumeroTyyppi']['code']) == 5: # TODO what are the different types?
            company.phone = phone['numero']
            break

    company.save()
    if not company.has_ytr() and node.get('code', None):
        YTRCompany.objects.create(company=company, code=node.get('code'))

    # Update addresses
    addresses = [Address(
        company=company,
        addressType=address_type(a['osoitetyyppi']['code']),
        streetAddress=a['katuOsoite'],
        streetAddress2=a['katuOsoite2'] or '',
        streetAddress3=a['katuOsoite3'] or '',
        postalcode=a['postinumeroKoodi'],
        city=a['postitoimipaikkaNimi'],
        country=a['maa']['maatunnusKoodi'],
        ) for a in node['osoitteet']['organisaatioOsoite']]

    company.addresses.all().delete()
    Address.objects.bulk_create(addresses)

    return company


def address_type(code):
    return {
        '3': Address.TYPE_SNAILMAIL
    }.get(code, 'unknown')
