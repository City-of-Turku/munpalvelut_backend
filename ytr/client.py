from django.conf import settings
from django.db import transaction

from organisation.models import YTRCompany
from ytr import parser

import requests, json

import logging
logger = logging.getLogger(__name__)

class YtrError(Exception):
    pass

def _get(path):
    assert(path[0] == '/')

    path = settings.YTR_API_ROOT + path
    logger.info("Fetching " + path)
    r = requests.get(path)

    if r.status_code != 200:
        logger.error("Error fetching %s: error code %d" % (path, r.status_code))
        raise YtrError("Error fetching %s: error code %d" % (path, r.status_code))

    return r.json()

def _post(path, data = None, **kwargs):
    assert (path[0] == '/')
    if data is None:
        data = {}

    path = settings.YTR_API_ROOT + path
    logger.info('POST '+path)

    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Allow": "POST,PUT,PATCH,HEAD"
    })
    payload = json.dumps(data)
    r = s.post(path, data=payload, **kwargs)
    if r.status_code != 200:
        error = "POST Error on %s: error code %d" % (path, r.status_code)
        logger.error(error)
        raise YtrError(error)
    return r

def fetch_company(company):
    """Import a company.

    The parameter "company" can be either a Company instance (which will
    be updated) or a business ID string.
    """

    if not isinstance(company, str):
        company = company.businessid

    data = _get('/cxf/toimijat/yritykset?ytunnus=%s&tarkatTiedot=true' % company)

    with transaction.atomic():
        companies = parser.import_company_resultset(data, overwrite=True)

    return companies[0] if len(companies) > 0 else None


def find_company(company):
    """
    Look for company in YTR, return data if found else None
    """
    url = '/cxf/toimijat/yritykset/?ytunnus=' + company.businessid
    data = _get(url)
    companies = data['haeYrityksetResult']['yritykset']['yritys']
    # company exists in YTR?
    return companies[0] if len(companies) > 0 else None


def export_company(company):
    """
    IF company has YTR relation then do update otherwise add as new
    """
    if company.has_ytr() and company.ytr.code:
        url = '/cxf/yleiset/update'
        r = _post(url, YTRCompany.map(company))
        return True

    # On insert check first is there a record on given business ID
    ytr = find_company(company)

    if ytr is None:
        # Create new record
        url = '/cxf/yleiset/put'
        r = _post(url, YTRCompany.map(company))
        # Fetch again so we get YTR code (post does not return object)
        ytr = find_company(company)
        # Create record for our side
        try:
            company = YTRCompany.objects.create(company=company, code=ytr['code'])
            # update data to YTR
            url = '/cxf/yleiset/update'
            r = _post(url, YTRCompany.map(company))
            return True
        except ValueError:
            # after second find... something went wrong
            pass
    logger.error("Cannot update company ([}) into YTR".format(company.businessid))
    return False
