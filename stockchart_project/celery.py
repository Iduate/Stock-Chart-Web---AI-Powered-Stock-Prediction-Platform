import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockchart_project.settings')

app = Celery('stockchart_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'update-market-data': {
        'task': 'charts.tasks.update_market_data',
        'schedule': 300.0,  # Every 5 minutes during market hours
    },
    'check-prediction-accuracy': {
        'task': 'charts.tasks.check_prediction_accuracy',
        'schedule': 3600.0,  # Every hour
    },
    'send-notification-emails': {
        'task': 'notifications.tasks.send_pending_notifications',
        'schedule': 600.0,  # Every 10 minutes
    },
    'process-referral-payouts': {
        'task': 'users.tasks.process_referral_payouts',
        'schedule': 86400.0,  # Daily
    },
    'cleanup-expired-coupons': {
        'task': 'users.tasks.cleanup_expired_coupons',
        'schedule': 86400.0,  # Daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
