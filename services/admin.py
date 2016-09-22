from django.contrib import admin

from . import models

class DescriptionAdmin(admin.StackedInline):
    model = models.ServicePackageDescription
    extra = 0


@admin.register(models.ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('shortname',)
    inlines = (DescriptionAdmin,)
