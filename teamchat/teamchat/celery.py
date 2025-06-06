import os
from celery import Celery
from celery.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teamchat.settings')

app = Celery('teamchat')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Windows-specific settings
if os.name == 'nt':
    app.conf.worker_pool = 'solo'  # Use solo pool instead of prefork
    app.conf.worker_max_tasks_per_child = 1
    app.conf.worker_concurrency = 1
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'cleanup-presence': {
        'task': 'chat.tasks.cleanup_presence',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}


