from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Notification, NotificationStatus, ChannelChoices, DeliveryAttempt, AttemptStatus
import os
import requests

from .serializers import SendEmailSerializer, SendTelegramSerializer


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

        try:
            send_mail(
                'Notification',
                message,
                'no-reply@example.com',
                [user_email],
                fail_silently=False,
            )
            DeliveryAttempt.objects.create(
                notification=notification,
                channel=ChannelChoices.EMAIL,
                status=AttemptStatus.SUCCESS,
            )
            notification.status = NotificationStatus.SENT
            notification.sent_at = notification.updated_at
            notification.attempts = notification.attempts + 1
            notification.save(update_fields=['status', 'sent_at', 'attempts'])
            return Response({'detail': 'Email sent successfully', 'notification_id': notification.id}, status=status.HTTP_200_OK)
        except Exception as exc:
            DeliveryAttempt.objects.create(
                notification=notification,
                channel=ChannelChoices.EMAIL,
                status=AttemptStatus.FAILURE,
                error=str(exc),
            )
            notification.status = NotificationStatus.FAILED
            notification.error = str(exc)
            notification.attempts = notification.attempts + 1
            notification.save(update_fields=['status', 'error', 'attempts'])
            return Response({'detail': 'Email sending failed', 'error': str(exc), 'notification_id': notification.id}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": telegram_id, "text": message}

        try:
            resp = requests.post(send_url, json=payload, timeout=10)
            data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
            if resp.status_code == 200 and data.get('ok'):
                DeliveryAttempt.objects.create(
                    notification=notification,
                    channel=ChannelChoices.TELEGRAM,
                    status=AttemptStatus.SUCCESS,
                )
                notification.status = NotificationStatus.SENT
                notification.sent_at = notification.updated_at
                notification.attempts = notification.attempts + 1
                notification.save(update_fields=['status', 'sent_at', 'attempts'])
                return Response({'detail': 'Telegram sent', 'notification_id': notification.id}, status=status.HTTP_200_OK)
            else:
                error_text = data.get('description') if isinstance(data, dict) else resp.text
                raise RuntimeError(error_text or f"HTTP {resp.status_code}")
        except Exception as exc:
            DeliveryAttempt.objects.create(
                notification=notification,
                channel=ChannelChoices.TELEGRAM,
                status=AttemptStatus.FAILURE,
                error=str(exc),
            )
            notification.status = NotificationStatus.FAILED
            notification.error = str(exc)
            notification.attempts = notification.attempts + 1
            notification.save(update_fields=['status', 'error', 'attempts'])
            return Response({'detail': 'Telegram sending failed', 'error': str(exc), 'notification_id': notification.id}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
