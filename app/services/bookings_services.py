from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocalCelery
from app.models import Booking, Event, User
from app.schemas.bookings import BookingCreate
from app.tasks.email_tasks import send_event_reminder


async def create_booking(
    data: BookingCreate,
    event_id: UUID,
    db: AsyncSession,
    user: User,
):
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not active user!"
            )
    
    event_exists = await db.scalar(
        select(Event).where(Event.id == event_id).with_for_update()
    )

    if not event_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found!"
        )

    if event_exists.status != "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Event is not available"
        )

    if event_exists.available_seats == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No available seats!"
        )

    if event_exists.available_seats < data.seats:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Свободных мест всего: {event_exists.available_seats}",
        )

    data.user_id = user.id
    data.event_id = event_id
    new_booking = Booking(**data.model_dump())
    db.add(new_booking)
    await db.execute(
        update(Event)
        .where(Event.id == event_id)
        .values(available_seats=(Event.available_seats - data.seats))
    )
    await db.commit()
    await db.refresh(new_booking)
    return new_booking


async def user_bookings(user: User, db: AsyncSession):
    my_booking = (
        (
            await db.execute(
                select(User)
                .where(User.id == user.id)
                .options(selectinload(User.my_booking))
            )
        )
        .scalars()
        .first()
    )

    return my_booking


async def detail_booking(booking_id: UUID, db: AsyncSession):
    booking_exists = await db.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found!"
        )
    return booking_exists


async def user_booking_cancel(user: User, booking_id: UUID, db: AsyncSession):
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not active user!"
            )
    booking_exists = await db.scalar(select(Booking).where(Booking.id == booking_id))
    if not booking_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found!"
        )

    await db.execute(
        update(Booking).where(Booking.id == booking_id).values(status="cancelled")
    )
    await db.execute(
        update(Event)
        .where(Event.id == booking_exists.event_id)
        .values(available_seats=(Event.available_seats + booking_exists.seats))
    )
    await db.commit()


def check_booking_exp():

    with SessionLocalCelery() as db:
        exp_booking = db.execute(select(Booking).where(Booking.status == "pending", Booking.expires_at < datetime.now())).all()
        
        if exp_booking:
            for val in exp_booking:
                val.status = "cancelled"

                db.execute(
                    update(Event)
                    .where(Event.id == val.event_id)
                    .values(available_seats=(Event.available_seats + val.seats))
                )
            db.commit()
            return "Done! Made changes!"
        return "Done! Nothing has changed!"


def get_user_booking():
    with SessionLocalCelery() as db:
        confirmed_booking = db.execute(select(Booking).where(Booking.status == "confirmed")).all()
        
        if confirmed_booking:
            for val in confirmed_booking:
                event =  db.get(Event, val.event_id)
                user = db.get(User, val.user_id)
                if (
                    (datetime.now(UTC) + timedelta(hours=24))
                    < event.start_time
                    < (datetime.now(UTC) + timedelta(hours=25))
                ):
                    send_event_reminder.delay(
                        user.email,
                        event.title,
                        event.start_time.strftime("%B %d, %Y - %H:%m"),
                    )
