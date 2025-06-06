from celery import shared_task
from django.utils import timezone
from .models import User

@shared_task
def cleanup_presence():
    """Mark users as offline if they haven't been seen in 5 minutes"""
    threshold = timezone.now() - timezone.timedelta(minutes=5)
    User.objects.filter(
        online=True,
        last_seen__lt=threshold
    ).update(online=False)

