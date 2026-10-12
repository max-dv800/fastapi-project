from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_session
from app.core.security import get_refresh_payload
from app.schemas.users import TokenResponse, UserCreate, UserResponse
from app.services.auth_services import (
    get_refresh_token,
    user_cofirm_email,
    user_signin,
    user_signup,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def user_register(
    user: UserCreate, db: Annotated[AsyncSession, Depends(db_session)]
):
    new_user = await user_signup(user, db)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def user_login(
    response: Response,
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(db_session)],
) -> dict:

    access_token = await user_signin(response, user, db)

    return access_token


@router.post("/refresh", status_code=status.HTTP_201_CREATED)
async def refresh(
    response: Response,
    token: Annotated[HTTPAuthorizationCredentials, Depends(get_refresh_payload)],
    refresh_token: str | None = Cookie(default=None),
) -> dict:

    new_token_pair = await get_refresh_token(response, token, refresh_token)

    return new_token_pair


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh")


@router.get("/register_confirm", include_in_schema=False)
async def conf_register(token: str, db: Annotated[AsyncSession, Depends(db_session)]):
    conf = await user_cofirm_email(token, db)

    return conf
