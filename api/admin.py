from django.contrib import admin

from api import models

@admin.register(models.ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_filter = ('active',)
    list_display = ('key', 'active')

@admin.register(models.AuthToken)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created')

