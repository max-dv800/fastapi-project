import hashlib
import hmac
import json
import random
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Booking, Event, Payment, StatusBooking, StatusPayment, User
from app.tasks.email_tasks import send_booking_confirmation


def verify_signature(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        key=settings.HMAC_KEY.encode(), msg=raw_body, digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def payment_init(
    db: AsyncSession, booking_id: UUID, user_id: UUID
) -> tuple[Payment, str]:
    booking_exists = (
        await db.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one_or_none()
    if not booking_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found!"
        )
    if booking_exists.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="It`s booking another user!"
        )
    if booking_exists.status != StatusPayment.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Status booking - {booking_exists.status}, not possible to initiate the payment!",
        )
    user_email = (await db.scalar(select(User).where(User.id == user_id))).email

    event = await db.scalar(select(Event).where(Event.id == booking_exists.event_id))
    payment = Payment(
        booking_id=booking_id,
        amount=event.price * booking_exists.seats,
        status="pending",
    )
    db.add(payment)
    await db.flush()

    payment_url = f"https://fake-pay.example.com/pay/{payment.id}"

    if random.random() < 0.8:
        await process_payment_success(payment, booking_exists, event, user_email)
    else:
        await process_payment_failure(payment, booking_exists, event, user_email)

    await db.commit()
    return payment, payment_url


async def process_payment_success(
    payment: Payment,
    booking: Booking,
    event: Event,
    email: str,
):
    payment.status = StatusPayment.SUCCEEDED
    booking.status = StatusBooking.CONFIRMED

    send_booking_confirmation.delay(
        str(booking.id),
        str(event.title),
        str(booking.status),
        email,
    )


async def process_payment_failure(
    payment: Payment,
    booking: Booking,
    event: Event,
    email: str,
):
    payment.status = StatusPayment.FAILED
    booking.status = StatusBooking.CANCELLED
    event.available_seats += booking.seats

    send_booking_confirmation.delay(
        str(booking.id),
        str(event.title),
        str(booking.status),
        email,
    )


async def handle_webhook(db: AsyncSession, payload: dict) -> Payment:
    payment = await db.scalar(
        select(Payment).where(Payment.id == payload["payment_id"])
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found!"
        )

    if payment.status == StatusPayment.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Paymet already processed!"
        )

    booking = (
        (await db.execute(select(Booking).where(Booking.id == payment.booking_id)))
        .scalars()
        .first()
    )
    event = (
        (await db.execute(select(Event).where(Event.id == booking.event_id)))
        .scalars()
        .first()
    )
    email_user = (
        (await db.execute(select(User).where(User.id==booking.user_id)))
        .scalars()
        .first()
    ).email

    if payload["status"] == StatusPayment.SUCCEEDED:
        await process_payment_success(payment, booking, event, email_user)
    elif payload["status"] == StatusPayment.FAILED:
        await process_payment_failure(payment, booking, event, email_user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknow status payment: {payload['status']}",
        )

    await db.commit()
    return payment


async def decode_request_webhook(
    request: Request,
):
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON!"
        )

    signature = request.headers.get("X-Payments-Signature", "")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Payment-Signature header",
        )

    if not verify_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
        )

    return payload
