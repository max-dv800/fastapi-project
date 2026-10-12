from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import StatusPayment


class BasePayment(BaseModel):
    amount: Decimal
    status: StatusPayment = Field(default=StatusPayment.PENDING)
    booking_id: UUID
    external_id: int = Field(default=1001)
    created_at: datetime
    updated_at: datetime


class PaymentCreate(BaseModel):
    pass


class PaymentResponse(BasePayment):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class PaymentInitiateResponse(BaseModel):
    payment_id: UUID
    payment_url: str
    amount: Decimal
    status: StatusPayment


class WebhookPayload(BaseModel):
    payment_id: UUID = Field(alias="external_payment_id")
    status: StatusPayment
    signature: str
