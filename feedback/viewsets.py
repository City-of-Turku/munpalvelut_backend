from django.http import Http404
from django.conf import settings

from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework import status

from mailer.mail import send_template_mail
from feedback.serializers import FeedbackFormSerializer

class FeedbackViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Receive user feedback.
    """
    serializer_class = FeedbackFormSerializer

    def create(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            send_template_mail(
                settings.FEEDBACK_EMAIL,
                'feedback',
                serializer.data
                )

            return Response({'status': 'ok'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
