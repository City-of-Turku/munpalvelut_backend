from django.test import TestCase
from django.core.files.uploadhandler import MemoryFileUploadHandler, StopFutureHandlers
from django.conf import settings

from media.models import Image

import os

def _getfile(name):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'test_images',
        name
    )
    return open(path, 'rb')

class ImageTestCase(TestCase):
    def test_image_saving(self):
        img = Image.save_or_get(_getfile('test1.png'))
        self.assertIsNotNone(img.id)

        self.assertEquals(img.width, 32)
        self.assertEquals(img.height, 48)
        
        img2 = Image.save_or_get(_getfile('test2.png'))
        self.assertIsNotNone(img2.id)
        self.assertNotEqual(img2.id, img.id)
        self.assertEquals(img2.width, 32)
        self.assertEquals(img2.height, 32)

        # Identical images should be deduplicated
        img1_2 = Image.save_or_get(_getfile('test1.png'))
        self.assertEqual(img1_2.id, img.id)
        
        # Test JPEG and GIF formats
        img3 = Image.save_or_get(_getfile('test3.jpeg'))
        self.assertIsNotNone(img3.id)
        
        img4 = Image.save_or_get(_getfile('test4.gif'))
        self.assertIsNotNone(img4.id)
    
    def test_size_limiting(self):
        img = Image.save_or_get(_getfile('test-big.png'))
        self.assertIsNotNone(img.id)
        
        self.assertTrue(img.width <= settings.MAX_IMAGE_SIZE[0])
        self.assertTrue(img.height <= settings.MAX_IMAGE_SIZE[1])
        self.assertTrue(
            img.width == settings.MAX_IMAGE_SIZE[0] or
            img.height == settings.MAX_IMAGE_SIZE[1]
        )
