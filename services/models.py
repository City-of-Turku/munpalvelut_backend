from __future__ import unicode_literals

from django.db import models

class ServicePackage(models.Model):
    shortname = models.SlugField(unique=True)
    pricing_formula = models.CharField(max_length=255)
    website = models.URLField(blank=True)

    @property
    def title(self):
        return {d.lang: d.title for d in self.__get_description()}
    
    @property
    def description(self):
        return {d.lang: d.description for d in self.__get_description()}

    def __str__(self):
        return self.shortname

    def __get_description(self):
        if not hasattr(self, '_descriptions'):
            self._descriptions = list(self.servicepackagedescription_set.all())

        return self._descriptions


class ServicePackageDescription(models.Model):
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE)
    lang = models.CharField(max_length=3)
    
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        unique_together = ("package", "lang")
