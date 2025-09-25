import os
from typing import List

import requests
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    Notification,
    NotificationStatus,
    ChannelChoices,
    DeliveryAttempt,
    AttemptStatus,
)


def _get_channel_order(user_preferred: List[str]) -> List[str]:
    default_order = [ChannelChoices.EMAIL, ChannelChoices.SMS, ChannelChoices.TELEGRAM]
    if not user_preferred:
        return default_order
    normalized = [c for c in user_preferred if c in dict(ChannelChoices.choices)]
    # Append any missing defaults to ensure full fallback coverage
    for channel in default_order:
        if channel not in normalized:
            normalized.append(channel)
    return normalized


def _send_via_email(notification: Notification) -> None:
    send_mail(
        "Notification",
        notification.message,
        os.getenv("DEFAULT_FROM_EMAIL") or "no-reply@example.com",
        [notification.user.email],
        fail_silently=False,
    )


def _send_via_sms(notification: Notification) -> None:
    # Placeholder: integrate real SMS provider (Twilio) here
    if not notification.user.phone_number:
        raise RuntimeError("Phone number not set for user")
    # Simulate success path without external call
    return None


def _send_via_telegram(notification: Notification) -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("Bot token not configured")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": notification.user.telegram_id, "text": notification.message}
    resp = requests.post(send_url, json=payload, timeout=10)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    if not (resp.status_code == 200 and isinstance(data, dict) and data.get("ok")):
        error_text = data.get("description") if isinstance(data, dict) else resp.text
        raise RuntimeError(error_text or f"HTTP {resp.status_code}")


CHANNEL_SENDER = {
    ChannelChoices.EMAIL: _send_via_email,
    ChannelChoices.SMS: _send_via_sms,
    ChannelChoices.TELEGRAM: _send_via_telegram,
}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3})
def send_notification_task(self, notification_id: int) -> str:
    notification = Notification.objects.select_related("user").get(pk=notification_id)
    if notification.status == NotificationStatus.SENT:
        return "already_sent"

    channel_order = _get_channel_order(notification.user.preferred_channels or [])
    last_error = ""

    # Mark as in progress
    Notification.objects.filter(pk=notification.pk).update(
        status=NotificationStatus.IN_PROGRESS,
        updated_at=timezone.now(),
    )

    for channel in channel_order:
        Notification.objects.filter(pk=notification.pk).update(last_channel=channel)
        try:
            CHANNEL_SENDER[channel](notification)
            DeliveryAttempt.objects.create(
                notification=notification,
                channel=channel,
                status=AttemptStatus.SUCCESS,
            )
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
            notification.attempts = notification.attempts + 1
            notification.error = ""
            notification.last_channel = channel
            notification.save(update_fields=["status", "sent_at", "attempts", "error", "last_channel", "updated_at"])
            return "sent"
        except Exception as exc:  # noqa: BLE001 – we log as failure attempt
            last_error = str(exc)
            DeliveryAttempt.objects.create(
                notification=notification,
                channel=channel,
                status=AttemptStatus.FAILURE,
                error=last_error,
            )
            notification.attempts = notification.attempts + 1
            notification.error = last_error
            notification.last_channel = channel
            notification.save(update_fields=["attempts", "error", "last_channel", "updated_at"])

    # If all channels failed
    Notification.objects.filter(pk=notification.pk).update(
        status=NotificationStatus.FAILED,
        error=last_error,
        updated_at=timezone.now(),
    )
    raise RuntimeError(last_error or "All channels failed")
