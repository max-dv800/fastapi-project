from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import StatusBooking


class BaseBooking(BaseModel):
    seats: int = Field(ge=1, le=10, description="Нельзя бронировать более 10 мест!")
    status: StatusBooking = Field(default=StatusBooking.PENDING)


class BookingCreate(BaseBooking):
    user_id: UUID
    event_id: UUID
    expires_at: datetime = Field(default=datetime.now(UTC) + timedelta(minutes=30))
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime = Field(default=datetime.now(UTC))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "seats": 5,
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "event_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        }
    )


class BookingResponse(BaseBooking):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
