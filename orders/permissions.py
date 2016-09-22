#!/usr/bin/env python
# coding=utf-8

from rest_framework import permissions

# Owner

class IsOwner(permissions.BasePermission):

    def has_permission(self, request, view):
        try:
            return request.user and \
                str(request.user.pk) == str(request.parser_context['kwargs']['user_pk'])
        except (AttributeError, KeyError):
            return False

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user

class IsOwnerOrStaff(IsOwner):

    def has_permission(self, request, view):
        return request.user.is_staff or \
                super(IsOwnerOrStaff, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or \
                super(IsOwnerOrStaff, self).has_object_permission(request, view, obj)

# Company User

class IsCompanyUser(permissions.BasePermission):

    def has_permission(self, request, view):
        try:
            return request.user.company and \
                str(request.user.company.pk) == str(request.parser_context['kwargs']['company_pk'])
        except (AttributeError, KeyError):
            return False

    def has_object_permission(self, request, view, obj):
        return request.user.company == obj.company

class IsCompanyUserOrStaff(IsCompanyUser):

    def has_permission(self, request, view):
        return request.user.is_staff or \
                super(IsCompanyUserOrStaff, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or \
                super(IsCompanyUserOrStaff, self).has_object_permission(request, view, obj)

# Rating

class CanRate(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.can_be_rated()
