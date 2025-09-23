from rest_framework import serializers


class SendEmailSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    message = serializers.CharField(max_length=5000)


class SendTelegramSerializer(serializers.Serializer):
    telegram_id = serializers.CharField(max_length=128)
    message = serializers.CharField(max_length=4096)
