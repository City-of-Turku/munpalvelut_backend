# Based on this article:
# https://www.caktusgroup.com/blog/2013/06/26/media-root-and-django-tests/

import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner

class TempMediaMixin(object):
    "Mixin to create MEDIA_ROOT in temp and tear down when complete."

    def setup_test_environment(self):
        "Create temp directory and update MEDIA_ROOT and default storage."
        super(TempMediaMixin, self).setup_test_environment()
        
        self.__original_media_root = settings.MEDIA_ROOT
        self.__original_file_storage = settings.DEFAULT_FILE_STORAGE
        self.__temp_media = tempfile.mkdtemp()
        
        print ("Using temporary media root '{}'...".format(self.__temp_media))

        settings.MEDIA_ROOT = self.__temp_media
        settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    def teardown_test_environment(self):
        "Delete temp storage."
        super(TempMediaMixin, self).teardown_test_environment()
        
        if not self.keepdb:
            print ("Destroying temporary media root '{}'...".format(self.__temp_media))
            shutil.rmtree(self.__temp_media, ignore_errors=True)

        settings.MEDIA_ROOT = self.__original_media_root
        settings.DEFAULT_FILE_STORAGE = self.__original_file_storage


class MediaTestRunner(TempMediaMixin, DiscoverRunner):
    pass
