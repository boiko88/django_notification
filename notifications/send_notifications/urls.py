from django.urls import path
from . import views

urlpatterns = [
    path('send_notification/', views.SendNotificationView.as_view(), name='send_notification'),
]
