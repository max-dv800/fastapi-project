from fastapi import HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    password_encode,
    password_verify,
    token_verify,
)
from app.models import User
from app.schemas.users import UserCreate
from app.tasks.email_tasks import send_confirmation_email

serializer = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY)


async def user_signup(
    user: UserCreate,
    db: AsyncSession,
):
    user_exist = (
        await db.execute(select(User).where(User.email == user.email))
    ).scalar_one_or_none()
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists!"
        )

    hash_pass = password_encode(user.hashed_password)
    user.hashed_password = hash_pass
    n_user = User(**user.model_dump())
    db.add(n_user)

    await db.commit()
    await db.refresh(n_user)

    confirmation_token = serializer.dumps(n_user.email)
    send_confirmation_email.delay(n_user.email, confirmation_token)

    return n_user


async def user_signin(
    response: Response, user: OAuth2PasswordRequestForm, db: AsyncSession
):
    user_exists = (
        (await db.execute(select(User).where(User.email == user.username)))
        .scalars()
        .first()
    )

    if not user_exists or not password_verify(
        user_exists.hashed_password, user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password!",
        )

    access_token = create_access_token(user_exists.email)
    refresh_token = create_refresh_token(user_exists.email)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_MAX_AGE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth/refresh",
        max_age=settings.REFRESH_MAX_AGE,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


async def get_refresh_token(
    response: Response, token: HTTPAuthorizationCredentials, refresh_token: str
) -> dict:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token not found!"
        )

    data = token_verify(refresh_token, "refresh")

    if data.get("iat") != token.get("iat"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Устаревший refresh_token!"
        )

    user_name = token.get("sub")

    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")

    new_access_token = create_access_token(user_name)
    new_refresh_token = create_refresh_token(user_name)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_MAX_AGE,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth/refresh",
        max_age=settings.REFRESH_MAX_AGE,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
    }


async def user_cofirm_email(
    token: str,
    db: AsyncSession,
):
    try:
        email = serializer.loads(token, max_age=3600)
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token!"
        )

    await db.execute(update(User).where(User.email == email).values(is_active=True))
    await db.commit()

    return "Регистрация подтверждена!"
