from uuid import UUID
import logging
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Status, User
from app.schemas.events import EventCreate, EventFilter, EventResponse, EventUpdate
from app.utils.cache import CacheRedis
from app.utils.pagination import query_sql

cache_api = CacheRedis()
logger = logging.getLogger()

async def get_all_events(
    filters: EventFilter,
    db: AsyncSession,
):
    key = f"event:{filters.status}:{filters.price}:{filters.start_date}:{filters.skip}:{filters.limit}"
    key_exists = await cache_api.exists(key)
    if key_exists:
        cache_event = await cache_api.get(key)
        return cache_event

    stmt = query_sql(**filters.model_dump())
    logger.warning(f"Запрос sql {stmt}")
    events = (await db.execute(stmt)).scalars().all()
    
    event_valid = [EventResponse.model_validate(val) for val in events]

    await cache_api.set(key, [val.model_dump() for val in event_valid], ex=60)

    return event_valid


async def get_one_event(
    event_id: UUID,
    db: AsyncSession,
):
    event = await db.scalar(select(Event).where(Event.id == event_id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found!"
        )
    return event


async def create_new_event(
    data: EventCreate,
    db: AsyncSession,
    user: User,
):
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not active user!"
            )
    
    if user.is_organizer is False and user.is_superuser is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access!")

    event_exists = (
        await db.execute(select(Event).where(Event.title == data.title))
    ).scalar_one_or_none()
    if event_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Event already exists!"
        )
    data.organizer_id = user.id
    new_event = Event(**data.model_dump(exclude_unset=True))
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event


async def partial_update_event(
    event_id: UUID,
    data: EventUpdate,
    db: AsyncSession,
    user: User,
):
    event_exists = (
        await db.execute(select(Event).where(Event.id == event_id))
    ).scalar_one_or_none()
    if not event_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found!"
        )

    if user.id != event_exists.organizer_id and user.is_superuser is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access!")

    valid_data = data.model_dump(exclude_unset=True)
    if valid_data:
        for field, val in valid_data.items():
            setattr(event_exists, field, val)

    await db.commit()
    await db.refresh(event_exists)
    return event_exists


async def status_delete_event(event_id: UUID, db: AsyncSession, user: User):
    event_exists = (
        await db.execute(select(Event).where(Event.id == event_id))
    ).scalar_one_or_none()
    if not event_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found!"
        )

    if user.id != event_exists.organizer_id and user.is_superuser is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access!")

    await db.execute(
        update(Event).where(Event.id == event_id).values(status=Status.cancelled)
    )
    await db.commit()

    return f"Event {event_exists.title} - удален!"
