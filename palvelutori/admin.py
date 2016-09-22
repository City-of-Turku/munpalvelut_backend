from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin
from django.utils.translation import ugettext_lazy as _

from palvelutori.models import User, VerificationLink, UserSite
from palvelutori.user_forms import UserCreationForm, UserChangeForm

@admin.register(User)
class UserAdmin(OriginalUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'vetuma', 'company', 'company_role')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

@admin.register(VerificationLink)
class VerificationLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'used')

@admin.register(UserSite)
class UserSiteAdmin(admin.ModelAdmin):
    pass
