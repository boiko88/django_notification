import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notifications.settings")

app = Celery("notifications")

# Configure from Django settings using CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


