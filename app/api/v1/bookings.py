from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session
from app.core.security import get_current_user
from app.models import User
from app.schemas.bookings import BookingCreate, BookingResponse
from app.schemas.users import UserBooking
from app.services.bookings_services import (
    create_booking,
    detail_booking,
    user_booking_cancel,
    user_bookings,
)

router = APIRouter()


@router.post("/events/{event_id}/bookings", response_model=BookingResponse)
async def create_booking_events(
    data: BookingCreate,
    event_id: Annotated[UUID, Path(...)],
    db: Annotated[AsyncSession, Depends(db_session)],
    user: Annotated[User, Depends(get_current_user)],
):

    new_booking = await create_booking(data, event_id, db, user)

    return new_booking


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_one_booking(
    booking_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
    db: Annotated[AsyncSession, Depends(db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    booking = await detail_booking(booking_id=booking_id, db=db)

    return booking


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    user: Annotated[User, Depends(get_current_user)],
    booking_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
    db: Annotated[AsyncSession, Depends(db_session)],
):

    await user_booking_cancel(user=user, booking_id=booking_id, db=db)

    return {"Status": "Бронь отменена!"}


@router.get("/bookings", response_model=UserBooking)
async def get_my_bookings(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_session)],
):
    my_bookings = await user_bookings(user, db)

    return my_bookings
