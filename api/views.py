from django.http import Http404
from django.contrib.auth import login

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from api.user_serializers import VerificationSerializer, LoginSerializer, PasswordResetRequestSerializer, PasswordResetSerializer
from api.models import AuthToken


class VerifyUserView(APIView):
    """
    Verify a fresly registered user.
    """
    def get_serializer(self, *args, **kwargs):
        return VerificationSerializer(*args, **kwargs)

    def post(self, request, format=None):
        """
        ---
        type:
            status:
                required: true
                type: string
            user_id:
                required: true
                type: integer
        serializer: api.user_serializers.VerificationSerializer
        omit_serializer: false
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.verificationlink.verify()
            return Response({
                'status': 'verified',
                'user_id': serializer.verificationlink.user_id,
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Log in.
    
    Use a POST request to log in and get the user authentication token.
    """
    permission_classes = [AllowAny]
    
    def get_serializer(self, *args, **kwargs):
        return LoginSerializer(*args, **kwargs)

    def post(self, request, format=None):
        """
        ---
        type:
            token:
                required: true
                type: string
        serializer: api.user_serializers.LoginSerializer
        omit_serializer: false
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            
            return Response({
                'token': AuthToken.create_for(serializer._user).key,
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Log a user out.
    
    Making a POST request here invalidates the authentication token.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        """
        
        if self.request.auth:
            # Invalidate authentication token
            self.request.auth.delete()
        
            return Response({
                'status': 'token invalidated'
            })

        else:
            return Response({
                'status': 'no authentication token'
            })


class PasswordResetRequestView(APIView):
    """
    Request password reset token to be sent to the user's email address.
    """
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        return PasswordResetRequestSerializer(*args, **kwargs)

    def post(self, request):
        """
        ---
        serializer: api.user_serializers.PasswordResetRequestSerializer
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.send_token()
            return Response({
                'status': 'ok'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    """
    Reset user password.

    Resetting can be done by the emailed password reset token
    or by vetuma token.
    """
    permission_classes = [AllowAny]

    def get_serializer(self, *args, **kwargs):
        return PasswordResetSerializer(*args, **kwargs)

    def post(self, request):
        """
        ---
        serializer: api.user_serializers.PasswordResetSerializer
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.reset_password()
            return Response({
                'status': 'ok'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
