from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Notification, NotificationStatus, ChannelChoices, DeliveryAttempt, AttemptStatus
from .serializers import SendEmailSerializer


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
