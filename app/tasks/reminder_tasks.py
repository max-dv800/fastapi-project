from asgiref.sync import async_to_sync
from celery import shared_task

from app.services.bookings_services import check_booking_exp, get_user_booking
from .celery_config import BaseTaskWithRetry, app_celery

app_celery.conf.beat_schedule = {
    "task-ever-5min": {
        "task": "app.tasks.reminder_tasks.checking_booking_expire",
        "schedule": 300.0,
    },
    "task-ever-hour": {
        "task": "app.tasks.reminder_tasks.checking_reminder_event",
        "schedule": 3600.0,
    },
}


@shared_task(bind=True, base=BaseTaskWithRetry)
def checking_booking_expire(self):
    new = check_booking_exp()
    return new


@shared_task
def checking_reminder_event():
    check = get_user_booking()
    return check
