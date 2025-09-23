from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    telegram_id = models.CharField(max_length=100)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
