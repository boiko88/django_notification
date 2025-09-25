from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Notification, NotificationStatus, ChannelChoices, DeliveryAttempt, AttemptStatus
import os
import requests

from .serializers import SendEmailSerializer, SendTelegramSerializer
from .tasks import send_notification_task


class SendNotificationView(APIView):
    def post(self, request):
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_email = serializer.validated_data['user_email']
        message = serializer.validated_data['message']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'detail': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        notification = Notification.objects.create(
            user=user,
            message=message,
            status=NotificationStatus.IN_PROGRESS,
            last_channel=ChannelChoices.EMAIL,
        )

        # Enqueue async delivery with fallback across channels
        send_notification_task.delay(notification.id)
        return Response({'detail': 'Notification queued', 'notification_id': notification.id}, status=status.HTTP_202_ACCEPTED)


class SendTelegramView(APIView):
    def post(self, request):
        serializer = SendTelegramSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        telegram_id = serializer.validated_data['telegram_id']
        message = serializer.validated_data['message']

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return Response({'detail': 'Bot token not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check if user exists
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({'detail': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        notification = Notification.objects.create(
            user=user,
            message=message,
            status=NotificationStatus.IN_PROGRESS,
            last_channel=ChannelChoices.TELEGRAM,
        )

        # Enqueue async delivery with fallback across channels
        send_notification_task.delay(notification.id)
        return Response({'detail': 'Notification queued', 'notification_id': notification.id}, status=status.HTTP_202_ACCEPTED)
