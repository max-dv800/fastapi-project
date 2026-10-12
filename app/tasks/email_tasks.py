import smtplib
from email.message import EmailMessage

from celery import shared_task
from fastapi.templating import Jinja2Templates


from app.core.config import settings
from app.services.tasks_services import get_task_id, save_task_id
from app.tasks.celery_config import BaseTaskWithRetry
from app.services.tasks_services import cache

TEMPLATES = Jinja2Templates(directory="./templates")

@shared_task(bind=True, base=BaseTaskWithRetry)
def send_confirmation_email(self, to_email: str, token: str):
    
    new_task_id = f"conf-email:{to_email}"
    lock_key = f"lock:{new_task_id}"

    if not cache.set(lock_key, "await", ex=300, nx=True):
        return "Task in processing!"

    if get_task_id(new_task_id):
        return "The task has already been completed!"

    
    confirmation_url = f"{settings.FRONTEND_URL}/auth/register_confirm?token={token}"
    template = TEMPLATES.get_template(name="confirmation_email.html")
    html_content = template.render(confirmation_url=confirmation_url)

    message = EmailMessage()
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.EMAIL_USERNAME
    message["To"] = to_email
    message["Subject"] = "Подтверждение регистрации"

    try:
        with smtplib.SMTP_SSL(
            host=settings.EMAIL_HOST, port=settings.EMAIL_PORT, timeout=20
            ) as client:
            client.login(
                user=settings.EMAIL_USERNAME,
                password=settings.EMAIL_PASSWORD.get_secret_value(),
                )
            client.send_message(message)
            save_task_id(new_task_id)
    except (smtplib.SMTPException, OSError) as exc:
        cache.delete(lock_key)
        raise self.retry(exc=exc, countdown=60)
    finally:
        cache.delete(lock_key)


@shared_task(bind=True, base=BaseTaskWithRetry)
def send_booking_confirmation(
    self,
    booking_id,
    event_title,
    booking_status,
    user_email,
):

    new_task_id = f"conf-email-{user_email}-and-booking-{booking_id}"
    lock_key = f"lock:{new_task_id}"

    if not cache.set(lock_key, "await", ex=300, nx=True):
        return "Task in processing!"
    
    if get_task_id(new_task_id):
        return "The task has already been completed!"

    template = TEMPLATES.get_template(name="confirmation_booking.html")
    html_content = template.render(
        booking_id=booking_id, status_booking=booking_status, event=event_title
    )

    message = EmailMessage()
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.EMAIL_USERNAME
    message["To"] = user_email
    message["Subject"] = "Результат оплаты брони"

    try:
        with smtplib.SMTP_SSL(
            host=settings.EMAIL_HOST, port=settings.EMAIL_PORT, timeout=20
            ) as client:
                client.login(
                    user=settings.EMAIL_USERNAME,
                    password=settings.EMAIL_PASSWORD.get_secret_value(),
                    )
                client.send_message(message)
                save_task_id(new_task_id)
    except (smtplib.SMTPException, OSError) as exc:
        cache.delete(lock_key)
        raise self.retry(exc=exc, countdown=60)
    finally:
        cache.delete(lock_key)


@shared_task(bind=True, base=BaseTaskWithRetry)
def send_event_reminder(self, to_email: str, event_title: str, event_start):
    new_task_id = f"conf-email-{to_email}-and-enent-{event_title}-start-{event_start}"
    lock_key = f"lock:{new_task_id}"
    
    if not cache.set(lock_key, "await", ex=300, nx=True):
        return "Task in processing!"
    
    if get_task_id(new_task_id):
            return "The task has already been completed!"

    template = TEMPLATES.get_template(name="reminder_for_event.html")
    html_content = template.render(event_start=event_start, event=event_title)

    message = EmailMessage()
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.EMAIL_USERNAME
    message["To"] = to_email
    message["Subject"] = f"Мероприятие - {event_title}"

    try:
        with smtplib.SMTP_SSL(
            host=settings.EMAIL_HOST, port=settings.EMAIL_PORT, timeout=20
            ) as client:
                client.login(
                   user=settings.EMAIL_USERNAME,
                   password=settings.EMAIL_PASSWORD.get_secret_value(),
                   )
                client.send_message(message)
                save_task_id(new_task_id)
    except (smtplib.SMTPException, OSError) as exc:
        cache.delete(lock_key)
        raise self.retry(exc=exc, countdown=60)
    finally:
        cache.delete(lock_key)
