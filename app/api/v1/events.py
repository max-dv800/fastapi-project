from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session
from app.core.security import get_current_user
from app.models import User
from app.schemas.events import (
    EventCreate,
    EventFilter,
    EventResponse,
    EventResponseDetail,
    EventUpdate,
)
from app.services.events_services import (
    create_new_event,
    get_all_events,
    get_one_event,
    partial_update_event,
    status_delete_event,
)

router = APIRouter()


@router.post("/", response_model=EventResponse)
async def event_create(
    event: EventCreate,
    db: Annotated[AsyncSession, Depends(db_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    new_event = await create_new_event(event, db, user)
    return new_event


@router.get("/", response_model=list[EventResponse])
async def get_events(
    db: Annotated[AsyncSession, Depends(db_session)],
    filters: Annotated[EventFilter, Depends()],
):

    all_events = await get_all_events(filters, db)
    return all_events


@router.get("/{event_id}", response_model=EventResponseDetail)
async def one_event(
    db: Annotated[AsyncSession, Depends(db_session)],
    event_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
):
    event = await get_one_event(event_id=event_id, db=db)
    return event


@router.patch("/{event_id}", response_model=EventResponseDetail)
async def update_event(
    data: EventUpdate,
    db: Annotated[AsyncSession, Depends(db_session)],
    user: Annotated[User, Depends(get_current_user)],
    event_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
):
    update_event = await partial_update_event(
        event_id=event_id, data=data, db=db, user=user
    )

    return update_event


@router.delete("/{event_id}")
async def delete_event(
    db: Annotated[AsyncSession, Depends(db_session)],
    user: Annotated[User, Depends(get_current_user)],
    event_id: Annotated[UUID, Path(description="ID for event must by valid UUID")],
):
    del_event = await status_delete_event(event_id=event_id, db=db, user=user)

    return del_event
