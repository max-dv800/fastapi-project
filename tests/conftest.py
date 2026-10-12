import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import aiodocker
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.main
from app.core import settings
from app.models import Base
from app.tasks.celery_config import app_celery

test_engine = create_async_engine(url=settings.db_url, poolclass=NullPool)
TestAsyncSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
async def docker_container():
    client = aiodocker.Docker()

    try:
        container = await client.containers.run(
            config={
                "Image": "redis:latest",
                "Cmd": [
                    "redis-server",
                ],
                "HostConfig": {
                    "PortBindings": {"6379/tcp": [{"HostPort": "6380"}]},
                },
            },
            name="test_redis",
        )

        await asyncio.sleep(1.5)
        yield container

    finally:
        await container.stop()
        await container.delete(force=True)
        await client.close()


@pytest.fixture(scope="session")
def test_celery_app():
    app_celery.conf.task_always_eager = True

    yield

    app_celery.conf.task_always_eager = False


@pytest.fixture(scope="session")
async def test_db():
    async with test_engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as session:
        await session.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def test_session(test_db):
    async with TestAsyncSession() as db:
        try:
            yield db
        finally:
            await db.close()
            await db.rollback()


@pytest.fixture
async def default_client(test_session):
    async with AsyncClient(
        transport=ASGITransport(app=app.main.app), base_url="http://test"
    ) as ac:
        yield ac


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_user_organizer(client: AsyncClient):
    email = f"test-organizer-{uuid4().hex[:5]}@example.com"
    payload = {
        "email": email,
        "full_name": "User Organizer",
        "hashed_password": "test_passwordP_32",
        "is_organizer": True,
        "is_active": True,
    }
    with patch("app.tasks.email_tasks.send_confirmation_email.delay") as mock_delay:
        response = await client.post(url="/api/v1/auth/register", json=payload)
        assert (
            response.status_code == 200
        ), f"Ошибка создания пользовыателя: {response.text}"

        return email, "test_passwordP_32"


async def create_user(client: AsyncClient):
    email = f"test-user-{uuid4().hex[:5]}@example.com"
    payload = {
        "email": email,
        "full_name": "User User",
        "hashed_password": "test_passwordP_32",
        "is_active": True,
    }
    with patch("app.tasks.email_tasks.send_confirmation_email.delay") as mock_delay:
        response = await client.post(url="/api/v1/auth/register", json=payload)
        assert (
            response.status_code == 200
        ), f"Ошибка создания пользователя: {response.text}"
        user_id = response.json().get("id")
        return email, "test_passwordP_32", user_id


async def user_login(client: AsyncClient, username: str, password: str) -> str:
    payload = {"username": username, "password": password}

    response = await client.post(url="/api/v1/auth/login", data=payload)
    assert (
        response.status_code == 200
    ), f"Ошибка авторизации пользователя: {response.text}"

    return response.json().get("access_token")


async def fake_events(client: AsyncClient, title):
    payload = {
        "title": title,
        "description": "Test",
        "start_time": (datetime.now(UTC) + timedelta(hours=3)).isoformat(),
        "end_time": (datetime.now(UTC) + timedelta(hours=6)).isoformat(),
        "location": "Test",
        "capacity": 10,
        "available_seats": 10,
        "price": 2500,
        "organizer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "published",
    }
    user_email, user_password = await create_user_organizer(client)
    token = await user_login(client, username=user_email, password=user_password)
    headers = auth_header(token)
    response = await client.post(url="/api/v1/events/", json=payload, headers=headers)

    assert response.status_code == 200, f"Ошибка создания события: {response.text}"

    return response.json().get("id"), headers


async def fake_booking(client: AsyncClient):

    event_id, _ = await fake_events(client, "Event for Payment")
    user_email, user_password, user_id = await create_user(client)
    token = await user_login(client, username=user_email, password=user_password)
    headers = auth_header(token)

    payload = {
        "event_id": event_id,
        "seats": 5,
        "user_id": user_id,
    }

    response = await client.post(
        url=f"/api/v1/events/{event_id}/bookings", json=payload, headers=headers
    )

    assert response.status_code == 200, f"Ошибка создания бронирования: {response.text}"

    return response.json().get("id"), user_id
