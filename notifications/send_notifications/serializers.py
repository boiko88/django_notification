from rest_framework import serializers


class SendEmailSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    message = serializers.CharField(max_length=5000)
