from django.db import models


class ChannelChoices(models.TextChoices):
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    TELEGRAM = 'telegram', 'Telegram'


class NotificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In progress'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'


class AttemptStatus(models.TextChoices):
    SUCCESS = 'success', 'Success'
    FAILURE = 'failure', 'Failure'


class User(models.Model):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    telegram_id = models.CharField(max_length=100)
    preferred_channels = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text='List of preferred channels in priority order'
    )

    def __str__(self):
        return self.email


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    last_channel = models.CharField(
        max_length=20,
        choices=ChannelChoices.choices,
        null=True,
        blank=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification #{self.pk} to {self.user.email} ({self.status})"


class DeliveryAttempt(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='attempts_log')
    channel = models.CharField(max_length=20, choices=ChannelChoices.choices)
    status = models.CharField(max_length=20, choices=AttemptStatus.choices)
    error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attempt {self.channel} for Notification #{self.notification_id}: {self.status}"
