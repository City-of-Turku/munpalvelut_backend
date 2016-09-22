from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models


class AddressAdmin(admin.StackedInline):
    model = models.Address
    extra = 0


class DescriptionAdmin(admin.TabularInline):
    model = models.CompanyDescription
    extra = 0


class LinkAdmin(admin.TabularInline):
    model = models.CompanyLink
    extra = 0


class CompanyRatingAdmin(admin.TabularInline):
    model = models.CompanyRating
    extra = 0


class YTRCompanyFilter(admin.SimpleListFilter):
    parameter_name = 'ytr'
    title = _('YTR link?')

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No'))
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(ytr__isnull=False)
        if self.value() == 'no':
            return queryset.filter(ytr__isnull=True)
        return queryset


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'businessid', 'has_ytr')
    inlines = (DescriptionAdmin, AddressAdmin, LinkAdmin, CompanyRatingAdmin)
    list_filter = (YTRCompanyFilter,)

    def has_ytr(self, obj):
        if obj.has_ytr():
            return obj.ytr
        return ''
    has_ytr.short_description = _('YTR code')
