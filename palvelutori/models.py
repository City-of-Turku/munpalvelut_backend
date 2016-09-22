from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

import random, string

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)


@python_2_unicode_compatible
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), max_length=255, unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)

    phone = models.CharField(_('phone number'), max_length=50, blank=True)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_("Has this user's email address been verified?")
    )

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    vetuma = models.CharField(max_length=128, help_text="Vetuma identification code", blank=True)

    company = models.ForeignKey('organisation.Company', on_delete=models.SET_NULL, blank=True, null=True)
    company_role = models.CharField(max_length=128, help_text="User's role in the company", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def anonymize_for_dump(self):
        self.email = self.email + ".example.org"
        self.vetuma = ""

    def __str__(self):
        return self.email


@python_2_unicode_compatible
class VerificationLink(models.Model):
    KEY_LENGTH = 32

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True
    )
    created = models.DateTimeField(auto_now_add=True)
    used = models.DateTimeField(blank=True, null=True, default=None)
    key = models.CharField(max_length=128, unique=True)

    def __str__(self):
         return self.key

    @classmethod
    def create_for(cls, user):
        return cls.objects.create(
            user=user,
            key=''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(cls.KEY_LENGTH))
            )

    def send_mail(self):
        self.user.email_user("Activate account",
                             "Your activation key: " + self.key
                             )

    @transaction.atomic
    def verify(self):
        self.user.is_verified = True
        self.user.save(update_fields=('is_verified',))

        self.used = timezone.now()
        self.save(update_fields=('used',))

class UserSite(models.Model):
    """

    address_country uses ISO 3166-1 alpha-3 specification:
        https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    address_street = models.CharField(max_length=255)
    address_street2 = models.CharField(max_length=255, blank=True)
    address_postalcode = models.CharField(max_length=32)
    address_city = models.CharField(max_length=255)
    address_country = models.CharField(max_length=3, default="FIN", editable=False)

    room_count = models.PositiveSmallIntegerField(blank=True, null=True)
    sanitary_count = models.PositiveSmallIntegerField(blank=True, null=True)
    floor_count = models.PositiveSmallIntegerField(blank=True, null=True)
    floor_area = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
