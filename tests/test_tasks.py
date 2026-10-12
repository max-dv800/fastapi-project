from unittest.mock import patch

from app.tasks.email_tasks import (
    send_booking_confirmation,
    send_confirmation_email,
    send_event_reminder,
)
from app.tasks.reminder_tasks import checking_reminder_event, checking_booking_expire
from app.core.config import settings


@patch("app.tasks.email_tasks.smtplib.SMTP_SSL")
def test_task_email_confirmation(mock_smtp, test_celery_app, docker_container):

    data1 = send_confirmation_email.delay("email@gmail.com", "my-test-token")
    data2 = send_confirmation_email.delay("email@gmail.com", "my-test-token")
    data3 = send_confirmation_email.delay("email@gmail.com", "my-test-token")
    data4 = send_confirmation_email.delay("email@gmail.com", "my-test-token")

    assert data1.ready() is True
    assert data2.ready() is True
    assert data3.ready() is True
    assert data4.ready() is True

    assert mock_smtp.called

    mock_smtp.assert_called_once()

    mock_instance = mock_smtp.return_value.__enter__.return_value

    mock_instance.login.assert_called_once_with(
        user=settings.EMAIL_USERNAME,
        password=settings.EMAIL_PASSWORD.get_secret_value(),
    )
    mock_instance.send_message.assert_called_once()


@patch("app.tasks.email_tasks.smtplib.SMTP_SSL")
def test_task_booking_confirmation(mock_smtp, test_celery_app, docker_container):

    data = send_booking_confirmation.delay(
        "123ddf", "Test Forum", "Confirm", "test_user@email.ru"
    )

    assert data.ready() is True
    assert mock_smtp.called

    mock_smtp.assert_called_once()

    mock_instance = mock_smtp.return_value.__enter__.return_value

    mock_instance.login.assert_called_once_with(
        user=settings.EMAIL_USERNAME,
        password=settings.EMAIL_PASSWORD.get_secret_value(),
    )
    mock_instance.send_message.assert_called_once()


@patch("app.tasks.email_tasks.smtplib.SMTP_SSL")
def test_task_event_reminder(mock_smtp, test_celery_app, docker_container):
    data = send_event_reminder.delay(
        "email@gmail.com", "MyTstEvent", "11.10.2026 12:00"
    )

    assert data.ready() is True
    assert mock_smtp.called

    mock_smtp.assert_called_once()

    mock_instance = mock_smtp.return_value.__enter__.return_value

    mock_instance.login.assert_called_once_with(
        user=settings.EMAIL_USERNAME,
        password=settings.EMAIL_PASSWORD.get_secret_value(),
    )

    mock_instance.send_message.assert_called_once()


def test_task_checking_booking_exp(test_session, test_celery_app):
    data = checking_booking_expire.delay()

    assert data.get() in ["Done! Made changes!", "Done! Nothing has changed!"]
    assert data.ready() is True


def test_task_checking_reminder_event(test_session, test_celery_app):
    data = checking_reminder_event.delay()

    assert data.ready() is True
