from django.contrib.auth import get_user_model
from django.http import Http404

from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import status

from api import user_serializers
from palvelutori.models import VerificationLink, UserSite

class UserViewSet(viewsets.ModelViewSet):
    """
    Normal users can only see themselves, but admin users can modify all users.
    Unauthenticated users are allowed to register accounts.

    An account is registered with a POST request. An email with a verification
    code will be sent to the specified address. The account can be verifified
    at /api/verify-user/.
    """
    permission_classes = [AllowAny]

    def get_queryset(self):
        q = get_user_model().objects.filter(is_active=True)

        if not self.request.user.is_authenticated():
            q = get_user_model().objects.none()

        elif not self.request.user.is_staff:
            q = q.filter(id=self.request.user.id)

        return q

    def get_serializer_class(self):
        if self.action == 'create':
            return user_serializers.RegisterUserSerializer
        elif self.action =='change_password':
            return user_serializers.PasswordSerializer
        else:
            return user_serializers.UserSerializer

    def check_object_permissions(self, request, obj):
        # View access is determined in get_queryset
        if request.method == 'GET':
            return True

        # Users can always modify themselves
        if request.method == 'PUT' and obj.id == request.user.id:
            return True

        # Otherwise, check django permissions
        if request.method == 'PUT' and request.user.has_perm('auth.change_user'):
            return True

        if request.method == 'DELETE' and request.user.has_perm('auth.delete_user'):
            if request.user.id == obj.id:
                raise PermissionDenied("Cannot delete self")
            return True

        raise PermissionDenied()

    def perform_destroy(self, instance):
        """Don't hard-delete users: just unset the is_active flag."""

        instance.is_active = False
        instance.save(update_fields=('is_active',))

    @list_route(methods=['get'])
    def me(self, request, pk=None):
        """
        Get info about the currently logged in user
        """

        user = request.user
        if not user.is_authenticated():
            raise PermissionDenied()

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def change_password(self, request, pk=None):
        """
        Change the given users password. Non-admin users can change
        their own passwords.
        ---
        type:
            status:
                required: true
                type: string
        """

        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data['new_password'])
            user.save(update_fields=('password',))
            return Response({
                'status': 'password set'
                })

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class UserSiteViewSet(viewsets.ModelViewSet):
    """
    Normal users can only see their own sites, but admin users can modify every users sites.
    Unauthenticated users are not able to see anything.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = user_serializers.UserSiteSerializer

    def get_queryset(self):
        q = UserSite.objects.all()

        if not self.request.user.is_staff:
            q = q.filter(user=self.request.user.id)

        return q

    def perform_create(self, serializer):
        override_user = self.request.data.get('user')
        if not self.request.user.is_staff or not override_user:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user_id=override_user)
