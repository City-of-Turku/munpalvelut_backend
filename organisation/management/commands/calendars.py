from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc

from calendars.models import CalendarEntry
from organisation.models import Company

import datetime

class Command(BaseCommand):
    help = "Create calendar entries"
    output_transaction = True

    def add_arguments(self, parser):
        parser.add_argument('companies', nargs='?',
                            help='Add calendar entries for these companies (default is all)')
        parser.add_argument('--weeks', action='store', default='1',
                            help='How many weeks to add (starting from this one)')
        parser.add_argument('--dry-run', action='store_true', dest='dryrun')

    def handle(self, *args, **options):
        companies = options.get('companies', '')
        weeks = int(options.get('weeks'))
        self.verbosity = int(options.get('verbosity'))
        self.dryrun = options.get('dryrun', False)

        if self.dryrun:
            self.verbosity = 3

        if companies:
            companies = [int(c) for c in companies.split(',')]

        self.add_weeks(companies, weeks)

    def add_weeks(self, companies, weeks):
        entries = []

        day0 = get_previous_monday(datetime.date.today())

        companyset = Company.objects.all()
        if companies:
            companyset = companyset.filter(id__in=companies)

        for week in range(weeks):
            for company in companyset:
                for day in range(5):
                    date = day0 + datetime.timedelta(days=week*7 + day)

                    if CalendarEntry.objects.filter(company=company, start__date=date).exists():
                        continue

                    time_start = datetime.datetime(date.year, date.month, date.day, 8, 0, tzinfo=utc)
                    time_end = datetime.datetime(date.year, date.month, date.day, 16, 0, tzinfo=utc)
                    entries.append(CalendarEntry(
                        start=time_start,
                        end=time_end,
                        busy=False,
                        company=company
                        ))
                    if self.verbosity > 2:
                        print("Adding entry {}: {} -- {} for company {} (#{})".format(
                            date,
                            time_start,
                            time_end,
                            company.name,
                            company.id
                            ))

        if self.verbosity > 1:
            print ("Adding", len(entries), "calendar entries...")

        if not self.dryrun:
            CalendarEntry.objects.bulk_create(entries)


def get_previous_monday(date, tz=None):
    """Get closest monday on or before ``date`` in the given timezone.

    :param date: aware or naive datetime or date
    :param tz: timezone to use when calculating previous monday, needed only if date is an
               aware datetime and you wish to ensure a monday in some specific zone
    :return: aware or naive date

    Source: djangotools repo: common/time.py

    2016-04-11 is a monday
    >>> import pytz
    >>> get_previous_monday(datetime(2016, 4, 10, 23, tzinfo=pytz.timezone('Europe/Helsinki')),
    ...                     pytz.timezone('Europe/Helsinki'))
    date(2016, 4, 4)

    >>> get_previous_monday(datetime(2016, 4, 10, 23, tzinfo=pytz.utc),
    ...                     pytz.timezone('Europe/Helsinki'))
    date(2016, 4, 11)

    >>> get_previous_monday(datetime(2016, 4, 11, 1, tzinfo=pytz.timezone('Europe/Helsinki')),
    ...                     pytz.timezone('Europe/Helsinki'))
    date(2016, 4, 11)

    >>> get_previous_monday(datetime(2016, 4, 11, 1, tzinfo=pytz.timezone('Europe/Helsinki')),
    ...                     pytz.utc)
    date(2016, 4, 4)

    >>> get_previous_monday(datetime(2016, 4, 11, 1))
    date(2016, 4, 11)

    """

    try:
        if date.tzinfo is not None:
            # input is aware datetime
            if tz is not None:
                date = date.astimezone(tz)
        date = date.date()
    except AttributeError:
        # input is a date
        pass

    return date - datetime.timedelta(days=date.weekday())
