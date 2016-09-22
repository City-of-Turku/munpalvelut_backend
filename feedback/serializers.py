from rest_framework import serializers

class FeedbackFormSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField()
