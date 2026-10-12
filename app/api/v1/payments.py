from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session
from app.schemas.payments import PaymentInitiateResponse, PaymentResponse
from app.services.payments_services import (
    decode_request_webhook,
    handle_webhook,
    payment_init,
)

router = APIRouter()


@router.post(
    "/{booking_id}/users/{user_id}/pay", response_model=PaymentInitiateResponse
)
async def pay_for_booking(
    db: Annotated[AsyncSession, Depends(db_session)],
    booking_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
    user_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
):
    payment, payment_url = await payment_init(db, booking_id, user_id)
    result = PaymentInitiateResponse(
        payment_id=payment.id,
        payment_url=payment_url,
        amount=payment.amount,
        status=payment.status,
    )

    return result


@router.post("/webhook", response_model=PaymentResponse)
async def payment_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(db_session)]
):
    payload = await decode_request_webhook(request)
    payment = await handle_webhook(db, payload)

    return payment
