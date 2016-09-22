#!/usr/bin/env python
# coding=utf-8

from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.http import Http404
from django.db.models import Q

from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAdminUser, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from organisation.models import Company, Address, CompanyRating, Picture
from organisation.serializers import CompanySerializer, CompanyRatingSerializer, PictureSerializer, PictureUploadSerializer
from api.user_serializers import PublicUserSerializer
from palvelutori.models import User

class CompanyViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """
    Company listings.

    """
    serializer_class = CompanySerializer

    def get_queryset(self):
        q = Company.objects.filter(active=True)

        search = self.request.query_params.get('search', '')

        if search:
            # TODO use the new fulltext search functionality in
            # Django 1.10
            q = q.filter(
                Q(email=search) |
                Q(name__icontains=search) |
                Q(companydescription__text__icontains=search) |
                Q(addresses__streetAddress__icontains=search) |
                Q(addresses__postalcode=search)
                ).distinct()

        return q

    def get_object(self):
        obj = super(CompanyViewSet, self).get_object()

        if self.request.method not in SAFE_METHODS:
            if self.request.user.company_id != obj.id and not self.request.user.is_superuser:
                self.permission_denied(
                    self.request,
                    message='Not a member of this company'
                )

        return obj


class CompanyRatingViewSet(viewsets.ModelViewSet):
    """
    Company rating views.

    Everyone can create ratings.
    Anonymous users can not list, view, update or delete.
    Logged in users can list, view, update and delete only their own ratings.

    Staff users have no special privileges.
    """
    queryset = CompanyRating.objects.filter(company__active=True)
    serializer_class = CompanyRatingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        q = super(CompanyRatingViewSet, self).get_queryset()

        if self.request.user.is_authenticated():
            q = q.filter(user=self.request.user.id)
        else:
            q = q.none()

        return q

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            return serializer.save(user=self.request.user)

        return super(CompanyRatingViewSet, self).perform_create(serializer)

class CompanyPictureViewSet(viewsets.ModelViewSet):
    serializer_class = PictureSerializer
    create_serializer_class = PictureUploadSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return self.create_serializer_class
        return self.serializer_class

    def get_queryset(self):
        return Picture.objects.filter(company_id=self.kwargs['company_pk'], company__active=True)
    
    def get_object(self):
        obj = super(CompanyPictureViewSet, self).get_object()
        
        if self.request.method not in SAFE_METHODS:
            if self.request.user.company_id != obj.company_id:
                self.permission_denied(
                    self.request,
                    message='Not a member of this company'
                )

        return obj

    def create(self, request, company_pk=None):
        if self.request.user.company_id != int(company_pk):
            self.permission_denied(
                self.request,
                message='Not a member of this company'
            )

        return super(CompanyPictureViewSet, self).create(request, company_pk=company_pk)


class CompanyUserViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """Users associated with a company.

    This is a public read-only list of users associated with a specific company."""
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return User.objects.filter(company_id=self.kwargs['company_pk'], company__active=True)
