from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext as _

from rest_framework import serializers

from palvelutori.models import User, VerificationLink, UserSite
from mailer.mail import send_template_mail

class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer for displaying a public subset of user information."""
    class Meta:
        model = User
        read_only_fields = ('id', 'email', 'first_name', 'last_name')
        fields = read_only_fields


class UserSerializer(serializers.ModelSerializer):
    """User serializer for list and edit views"""
    class Meta:
        model = User
        read_only_fields = (
            'date_joined',
            'last_login',
            'is_superuser',
            'is_staff',
            'is_active',
            'is_verified',
            'email',
            'company',
            'company_role',
            )
        fields = ('id', 'first_name', 'last_name', 'phone', 'orders') + read_only_fields

    orders = serializers.HyperlinkedIdentityField(
        view_name='api:user-orders-list',
        lookup_url_kwarg='user_pk'
    )

class RegisterUserSerializer(serializers.Serializer):
    """Serializer for new user registration"""

    email = serializers.EmailField()
    password = serializers.CharField(max_length=512)
    first_name = serializers.CharField(max_length=100, allow_blank=True)
    last_name = serializers.CharField(max_length=100, allow_blank=True)
    phone = serializers.CharField(max_length=50, allow_blank=True)
    vetuma = serializers.CharField(max_length=128, allow_blank=True, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use")
        return value

    def create(self, data):
        # TODO allow requests authenticated with an API key
        # to create pre_verified users. Otherwise, the verification message
        # must be sent.
        pre_verified = True

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_verified=pre_verified,
            vetuma=data.get('vetuma', ''),
        )

        if not pre_verified:
            vl = VerificationLink.create_for(user)
            vl.send_mail()

        return user


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=256, required=False)
    new_password = serializers.CharField(max_length=512)

    def validate(self, data):
        u = self.context['view'].get_object()
        ru = self.context['request'].user

        try:
            validate_password(data['new_password'], u.password)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.error_list)

        # Administrators can change passwords without knowing the old password,
        # except for their own.
        if 'old_password' not in data or not check_password(data['old_password'], u.password):
            if not ru.has_perm('auth.change_user') or ru.id == u.id:
                raise serializers.ValidationError(_('Incorrect password'))

        return data

class VerificationSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=512)

    def validate_key(self, value):
        try:
            self.verificationlink = VerificationLink.objects.get(key=value, used__isnull=True)
        except VerificationLink.DoesNotExist:
            raise serializers.ValidationError("Incorrect verification key")

        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=256)
    password = serializers.CharField(max_length=512)

    def validate(self, data):
        self._user = authenticate(
                email=data['email'],
                password=data['password']
                )

        if not self._user:
            raise serializers.ValidationError("Invalid username or password")

        if not self._user.is_active:
            raise serializers.ValidationError("User account is not active")

        if not self._user.is_verified:
            raise serializers.ValidationError("Email address not yet verified")

        return data

class UserSiteSerializer(serializers.ModelSerializer):
    """UserSite serializer for list and edit views"""

    floor_area = serializers.DecimalField(max_digits=8, decimal_places=2, coerce_to_string=False, required=False)

    class Meta:
        model = UserSite
        read_only_fields = ('id', 'user')


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=256)

    def send_token(self):
        try:
            user = User.objects.get(email=self.validated_data['email'])
        except User.DoesNotExist:
            # Missing user is not a validation error to avoid
            # leaking information about the existence of user accounts
            return False

        ctx = {
            'url': 'http://localhost:8000/password-reset/',
            'user': user,
            'token': token_generator.make_token(user),
        }

        return send_template_mail(user.email, 'password_reset', ctx)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=256)
    token = serializers.CharField(max_length=256, required=False)
    vetuma = serializers.CharField(max_length=256, required=False)
    new_password = serializers.CharField(max_length=256)

    def validate(self, data):
        if not (('token' in data) ^ ('vetuma' in data)):
            raise serializers.ValidationError(_("Either 'token' or 'vetuma' field (but not both) must be set'"))

        try:
            self._user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            self._user = None

        if 'token' in data:
            # Validate using a reset token sent by email
            if self._user is None or not token_generator.check_token(self._user, data['token']):
                raise serializers.ValidationError(_("Invalid email address or token"))

        else:
            # Validate using vetuma token
            if self._user is None or self._user.vetuma != data['vetuma']:
                raise serializers.ValidationError(_("Invalid email address or vetuma token"))

        try:
            validate_password(data['new_password'], self._user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.error_list)

        return data

    def reset_password(self):
        self._user.set_password(self.validated_data['new_password'])
        self._user.save()
