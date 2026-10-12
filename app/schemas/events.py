from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import StrEnum, auto
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    field_validator,
    model_validator,
)

from app.models import Status

msk = timedelta(hours=3)


def partial_schema(schema: type[BaseModel]):
    fields = {}
    for field, val in schema.model_fields.items():
        fields[field] = (val.annotation | None, None)
    return create_model(f"Update{schema.__name__}", **fields)


class StartDate(StrEnum):
    EARLIER = auto()
    LATER = auto()


class Price(StrEnum):
    FREE = auto()
    PAID = auto()
    LESS_THAN_5000 = auto()


class BaseEvent(BaseModel):
    title: str
    description: str


class EventCreate(BaseEvent):
    start_time: datetime
    end_time: datetime
    location: str
    capacity: int
    available_seats: int
    price: Decimal
    organizer_id: UUID
    status: Status = Field(default=Status.DRAFT)

    @field_validator("start_time", mode="after")
    @classmethod
    def valid_start_time(cls, val):
        now = datetime.now(timezone(msk))
        if val < now:
            raise ValueError("Начало мероприятия не корректно!")
        return val

    @model_validator(mode="after")
    def valid_date_start_end(self):
        if self.end_time < self.start_time:
            raise ValueError(
                "Время окончания мероприяти не может быть раньше его начала!"
            )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My new forum",
                "description": "Forum",
                "start_time": (
                    datetime.now(timezone(msk)) + timedelta(hours=3)
                ).isoformat(),
                "end_time": (
                    datetime.now(timezone(msk)) + timedelta(hours=6)
                ).isoformat(),
                "location": "Expoforum",
                "capacity": 200,
                "available_seats": 200,
                "price": 5200.00,
                "organizer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        }
    )


class EventResponse(BaseEvent):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    start_time: datetime
    price: Decimal


class EventResponseDetail(BaseEvent):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    start_time: datetime
    price: Decimal
    capacity: int
    available_seats: int


class EventFilter(BaseModel):

    price: Price | None = Field(default=None)
    status: str = Field(default=Status.PUBLISHED)
    start_date: StartDate | None = Field(default=None, alias="startDate")
    skip: int = Field(default=0)
    limit: int = Field(ge=1, le=100, default=10)


class EventUpdate(partial_schema(EventCreate)):
    pass
