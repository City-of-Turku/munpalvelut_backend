from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image as PillowImage
from io import BytesIO, SEEK_END

import hashlib

class ImageError(Exception):
    pass
class Image(models.Model):
    """Common store for uploaded images."""

    sha256 = models.CharField(max_length=64, unique=True)
    image = models.FileField(
        upload_to="images",
        max_length=255
        )
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    added  = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def save_or_get(sourcefile):
        """Save the image and return the model.
        
        The image is downscaled if too large. 

        If the exact same image is found, return it instead.
        """
        
        # First, make sure the uploaded file is an image file of acceptable type
        image = PillowImage.open(sourcefile)

        width, height = image.size
        fmt = image.format.lower()
        
        if fmt not in settings.ACCEPTED_IMAGE_FORMATS:
            raise ImageError("Unsupported image format (" + fmt + ")")

        # If image is too big, downscale it
        if width > settings.MAX_IMAGE_SIZE[0] or height > settings.MAX_IMAGE_SIZE[1]:
            image.thumbnail(settings.MAX_IMAGE_SIZE)
            width, height = image.size

            imgdata = BytesIO()
            image.save(imgdata, image.format)
            datalen = imgdata.tell()
        
        else:
            imgdata = sourcefile
            imgdata.seek(0, SEEK_END)
            datalen = imgdata.tell()

        # Generate hash
        imgdata.seek(0)
        m = hashlib.new('sha256')
        while True:
            chunk = imgdata.read(1024)
            if not chunk:
                break
            m.update(chunk)
        m = m.hexdigest()
        
        # See if this image has already been uploaded
        try:
            return Image.objects.get(sha256=m)
        except Image.DoesNotExist:
            pass
        
        # Save image
        sourcefile.seek(0)
        uploadedfile = InMemoryUploadedFile(
            file=imgdata,
            field_name='image',
            name=m + '.' + fmt,
            content_type='image/' + fmt,
            size=datalen,
            charset=None,
            content_type_extra=None
            )

        return Image.objects.create(
            sha256=m,
            image=uploadedfile,
            width=width,
            height=height,
        )
