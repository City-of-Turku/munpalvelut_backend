"""
A management command for generating a database+media file dump
for use in pilot or development environment.

Generates a file named `anonymized-dump-YYY-MM-DD.json` in the project root.

Database dump can be imported with `./manage.py loaddata filename`

Configuration
--------------

In settings.py:

    PILOT_DUMP={
        "exclude": [
            "cache_app.*",
            "sessions.Session",
            ...
            ],
        'media_prefix': 'media', # default, this sets the media file path prefix in the archive
        'allow_load': true, # Set this to enable the loaddump command
    }

If a model has a method named "anonymize_for_dump(self)", it
will be called before the object is serialized. The changes
are not saved in the database.
"""

from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.core import serializers
from django.apps import apps
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, router

from collections import OrderedDict
import zipfile
from tempfile import NamedTemporaryFile
import datetime
import os

class Command(BaseCommand):
    help = """Create a database and static file dump for use in pilot/dev environment.
"""
    output_transaction = False

    SETTINGS_KEY="PILOT_DUMP"

    def add_arguments(self, parser):
        parser.add_argument('--no-anon', action='store_false', dest='anonymize', help="Don't anonymize data")
        parser.add_argument('--no-db', action='store_false', dest='dump_db', help="Don't make a database dump")
        parser.add_argument('--no-files', action='store_false', dest='dump_files', help="Don't archive media files")
        parser.add_argument('output', nargs='?', type=str, help='Output filename. Default is "anonymized-dump-YYYY-MM-DD.zip"')

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity'))
        self.anonymize = options.get('anonymize', True)
        self.dump_db = options.get('dump_db', True)
        self.dump_files = options.get('dump_files', True)

        if not self.dump_db and not self.dump_files:
            raise CommandError("Nothing to do!")

        if options['output']:
            archivename = options['output']
        else:
            archivename = 'pilot-dump-' + str(datetime.date.today()) + '.zip'
            if self.anonymize:
                archivename = 'anonymized-' + archivename

        if os.path.isfile(archivename):
            raise CommandError("Dump file " + archivename + " already exists!")

        with zipfile.ZipFile(archivename, 'w') as archive:
            if self.dump_db:
                self.dump_database(archive)

            if self.dump_files:
                self.dump_media_files(archive, default_storage)

        print ("Wrote", archivename)


    def dump_database(self, archive):
        """Dump the database.
        This is based on Django's dumpdata command.
        """
        excluded_apps, exclude_models = self.get_exclusions()

        app_list = [
                (app_config, None) for app_config in apps.get_app_configs()
                if app_config.models_module is not None and app_config.label not in excluded_apps
            ]

        def get_objects():
            models = serializers.sort_dependencies(app_list)
            using = DEFAULT_DB_ALIAS

            models = [m for m in models
                      if (m._meta.app_label, m.__name__) not in exclude_models
                          and not m._meta.proxy and router.allow_migrate_model(using, m)
                     ]

            for i, model in enumerate(models):
                if self.verbosity > 1:
                    print ("%2s/%d: Dumping model %s.%s..." % (i+1, len(models), model._meta.app_label, model.__name__), end="")

                objects = model._default_manager

                queryset = objects.using(using).order_by(model._meta.pk.name)
                count = 0
                for obj in queryset.iterator():
                    if self.anonymize and hasattr(obj, 'anonymize_for_dump'):
                        obj.anonymize_for_dump()
                    yield obj
                    count += 1

                if self.verbosity > 1:
                    print (" [%d]" % count)

        with NamedTemporaryFile('w+t') as tmpfile:
            serializers.serialize('json', get_objects(),
                                indent=None,
                                stream=tmpfile,
                                )
            tmpfile.flush()
            archive.write(tmpfile.name, "database.json", zipfile.ZIP_DEFLATED)


    def dump_media_files(self, archive, storage, path=''):
        if self.verbosity > 1:
            print ("Archiving media/" + path + "...", end="")

        dirs, files = storage.listdir(path)

        if len(files) > 0 and self.verbosity >= 3:
            print ("")

        for f in files:
            try:
                filepath = storage.path(os.path.join(path, f))
            except NotImplementedError:
                # TODO download to a temporary file, then call archive_media_file
                raise CommandError("Remote media file store dumping not implemented!")

            else:
                self.archive_media_file(archive, filepath, path, f)

        if self.verbosity > 1:
            print (" [%d]" % len(files))

        for d in dirs:
            self.dump_media_files(archive, storage, path + d)


    def archive_media_file(self, archive, filepath, path, name):
        if self.verbosity >= 3:
            print ("\t%s" % name)

        prefix = getattr(settings, self.SETTINGS_KEY, {}).get('media_prefix', 'media')
        archive.write(filepath, os.path.join(prefix, path, name))


    def get_exclusions(self):
        """Return excluded apps and models.
        Parses the "exclude" setting:

            appname.*     - exclude entire app
            appname.model - exclude specific model

        Returns a list of excluded app names and
        (app name, model name) tuples.
        """
        conf = getattr(settings, self.SETTINGS_KEY, {})

        eapps = set()
        emodels = set()

        for x in conf.get('exclude', []):
            if '.' in x:
                try:
                    app, model = x.split('.')
                except ValueError:
                    raise CommandError("Unparseable app/model exclude: " + x)
                emodels.add((app, model))
            else:
                eapps.add(x)

        return eapps, emodels
