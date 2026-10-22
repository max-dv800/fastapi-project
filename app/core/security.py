from datetime import UTC, datetime, timedelta
from typing import Annotated

import argon2
import jwt
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Response, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

from .config import settings
from .database import db_session

ph = argon2.PasswordHasher()
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

security = HTTPBearer()


def password_encode(passw: str) -> str:
    return ph.hash(passw)


def password_verify(hash_passw: str, origin_passw: str) -> bool:
    try:
        data = ph.verify(hash_passw, origin_passw)
        return data
    except VerifyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password!"
        )


def create_access_token(user):
    payload = {
        "sub": user,
        "type": "access",
        "username": user,
        "exp": datetime.now(tz=UTC) + timedelta(seconds=settings.ACCESS_MAX_AGE),
        "iat": datetime.now(tz=UTC),
    }
    acces_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return acces_token


def create_refresh_token(user):
    payload = {
        "sub": user,
        "type": "refresh",
        "exp": datetime.now(tz=UTC) + timedelta(seconds=settings.REFRESH_MAX_AGE),
        "iat": datetime.now(tz=UTC),
    }
    refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return refresh_token


def token_verify(token: str, expected: str) -> dict:
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if data.get("type") != expected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid type token!"
            )
        return data
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token is invalid or expired!"
        )


def get_refresh_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    return token_verify(credentials.credentials, "refresh")


def authenticate(token: Annotated[str, Depends(oauth2_schema)]):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired!",
        )
    decode_token = token_verify(token)
    return decode_token


async def get_current_user(
    response: Response,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(db_session)],
    access_token: str | None = Cookie(default=None),
) -> User:

    data = token_verify(token.credentials, "access")

    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired!",
        )
    try:
        user_email = data.get("username")
    except (TypeError, ValueError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired!",
        )
    user = (
        await db.execute(select(User).where(User.email == user_email))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found!"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
