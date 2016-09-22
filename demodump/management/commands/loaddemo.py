"""
A management command for loading a database+media file dump
generated with dumpdemo.

See also dumpdemo.py"
"""

from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.files.storage import default_storage, FileSystemStorage
from django.conf import settings

import zipfile
from tempfile import NamedTemporaryFile
import shutil
import datetime
import os

class Command(BaseCommand):
    help = """Load a database+media file dump generated with dumpdemo""
"""
    output_transaction = True

    SETTINGS_KEY="PILOT_DUMP"

    def add_arguments(self, parser):
        parser.add_argument('--no-db', action='store_false', dest='load_db', help="Don't load database dump")
        parser.add_argument('--no-files', action='store_false', dest='load_files', help="Don't unpack media files")
        parser.add_argument('--no-delete', action='store_false', dest='delete', help="Don't delete local media files before unpacking")
        parser.add_argument('--no-input', action='store_false', dest='interactive', help="Don't prompt for confirmation")
        parser.add_argument('--override', action='store_true', dest='override', help="Load even if allow_load is not set to True")
        parser.add_argument('input', type=str, help='Input filename')

    def handle(self, *args, **options):
        if getattr(settings, self.SETTINGS_KEY, {}).get('allow_load', False) != True and options['override'] != True:
            raise CommandError("Loading of demo dumps not enabled ('allow_load' not set to True)")

        self.verbosity = int(options.get('verbosity'))
        load_db = options.get('load_db', True)
        load_files = options.get('load_files', True)
        self.deletefiles = options.get('delete', True)

        with zipfile.ZipFile(options['input'], 'r') as archive:
            if options.get('interactive', True):
                confirm = input("""Loaddemo will erase current database content and media files
and replace them with the ones loaded from file.
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """)
                if confirm != 'yes':
                    print ("Canncelled.")
                    return

            if load_db:
                self.load_database(archive)

            if load_files:
                self.load_media_files(archive)


    def load_database(self, archive):
        with NamedTemporaryFile(suffix=".json") as dbfile:
            # Unpack the database dump fixture
            with archive.open("database.json") as infile:
                shutil.copyfileobj(infile, dbfile)
            dbfile.flush()

            # Clear out the old database
            call_command('flush', '--no-input')

            # Load dump fixture
            call_command('loaddata', dbfile.name)


    def load_media_files(self, archive):
        if isinstance(default_storage, FileSystemStorage):
            self.load_media_files_filesystem(archive)
        else:
            raise CommandError("Cannot load media files: Support for storage backends other than FileSystemStorage not implemented!")


    def load_media_files_filesystem(self, archive):
        # Clear out any existing files
        if self.deletefiles:
            if self.verbosity > 1:
                print ("Deleting existing media files...")
            shutil.rmtree(settings.MEDIA_ROOT)

        # Unpack media
        prefix = getattr(settings, self.SETTINGS_KEY, {}).get('media_prefix', 'media') + '/'
        count = 0
        for name in archive.namelist():
            if name.startswith(prefix):
                target_dir = os.path.join(settings.MEDIA_ROOT, os.path.dirname(name[len(prefix):]))
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                if self.verbosity > 1:
                    print ("Extracting", name)

                with open(os.path.join(settings.MEDIA_ROOT, name[len(prefix):]), 'wb') as dest:
                    with archive.open(name) as src:
                        shutil.copyfileobj(src, dest)
                        count += 1

        print ("Unpacked %d media files" % count)
