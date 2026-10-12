from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session
from app.core.security import CurrentUser, get_current_user
from app.models import User
from app.schemas.users import UserPartialUpdate, UserPasswordUpdate, UserResponse
from app.services.users_services import partial_update, update_my_password

router = APIRouter()


@router.post("/me", response_model=UserResponse)
async def my_page(
    user: CurrentUser,
) -> User:
    return user


@router.patch("/me", response_model=UserResponse)
async def partial_update_user(
    data: UserPartialUpdate,
    user: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(db_session)],
):
    update_user = await partial_update(data, user, db)

    return update_user


@router.patch("/me/change_password")
async def update_password(
    user: Annotated[User, Depends(get_current_user)],
    data: UserPasswordUpdate,
    db: Annotated[AsyncSession, Depends(db_session)],
):
    new_pass = await update_my_password(user, data, db)

    return new_pass
