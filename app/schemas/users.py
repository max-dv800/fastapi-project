import re
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.bookings import BookingResponse
from app.schemas.events import EventResponse

pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$_*&%@~])[a-zA-Z\d$_*&%@~]{8,}$"


class BaseUser(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = False


class UserCreate(BaseUser):
    hashed_password: str
    is_organizer: bool = False
    is_superuser: bool = False
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime = Field(default=datetime.now(UTC))

    @field_validator("hashed_password", mode="after")
    @classmethod
    def valid_password(cls, passw):
        if not re.match(pattern, passw):
            raise ValueError("Не безопасный пароль!")
        return passw

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "my_email@pochta.gu",
                "full_name": "Alex Smith",
                "hashed_password": "passwordP_32",
            }
        }
    )


class UserResponse(BaseUser):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_organizer: bool
    is_superuser: bool
    created_at: datetime
    events: list[EventResponse] | None = None
    my_booking: list[BookingResponse] | None = None


class UserResponseShort(BaseUser):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserPartialUpdate(BaseModel):
    email: EmailStr
    full_name: str


class UserBooking(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    my_booking: list[BookingResponse] | None = None


class UserPasswordUpdate(BaseModel):
    hashed_password: str = Field(alias="new_password")

    @field_validator("hashed_password", mode="after")
    @classmethod
    def valid_password(cls, passw):
        if not re.match(pattern, passw):
            raise ValueError("Не безопасный пароль!")
        return passw


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
