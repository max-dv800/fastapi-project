from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from .conftest import (
    auth_header,
    create_user,
    create_user_organizer,
    fake_events,
    user_login,
)


@pytest.mark.asyncio
async def test_event_create_auth_user(default_client):
    payload = {
        "title": "Петербургский международный газовый форум",
        "description": "Петербургский международный газовый форум",
        "start_time": (datetime.now(UTC) + timedelta(hours=3)).isoformat(),
        "end_time": (datetime.now(UTC) + timedelta(hours=6)).isoformat(),
        "location": "КВЦ Экспофорум",
        "capacity": 200,
        "available_seats": 200,
        "price": 2500,
        "organizer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "published",
    }

    username, password = await create_user_organizer(default_client)
    token = await user_login(default_client, username, password)
    headers = auth_header(token)

    response = await default_client.post(
        url="/api/v1/events/", json=payload, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data.get("title") == "Петербургский международный газовый форум"
    assert data.get("price") == "2500"


@pytest.mark.asyncio
async def test_create_event_incorrect_date(default_client):
    payload = {
        "title": "Тестовое мероприятие",
        "description": "Тест",
        "start_time": (datetime.now(UTC) + timedelta(hours=3)).isoformat(),
        "end_time": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "location": "КВЦ Экспофорум",
        "capacity": 200,
        "available_seats": 200,
        "price": 2500,
        "organizer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }

    username, password = await create_user_organizer(default_client)
    token = await user_login(default_client, username, password)
    headers = auth_header(token)

    response = await default_client.post(
        url="/api/v1/events/", json=payload, headers=headers
    )

    assert response.status_code == 422
    data = response.json()["detail"][0]
    assert (
        data["msg"]
        == "Value error, Время окончания мероприяти не может быть раньше его начала!"
    )


@pytest.mark.asyncio
async def test_create_event_not_organizer(default_client):
    payload = {
        "title": "Петербургский международный газовый форум",
        "description": "Петербургский международный газовый форум",
        "start_time": (datetime.now(UTC) + timedelta(hours=3)).isoformat(),
        "end_time": (datetime.now(UTC) + timedelta(hours=6)).isoformat(),
        "location": "КВЦ Экспофорум",
        "capacity": 200,
        "available_seats": 200,
        "price": 2500,
        "organizer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }

    user_email, user_password, _ = await create_user(default_client)
    token = await user_login(
        default_client, username=user_email, password=user_password
    )
    headers = auth_header(token)

    response = await default_client.post(
        url="/api/v1/events/", json=payload, headers=headers
    )

    assert response.status_code == 403
    assert response.json().get("detail") == "No access!"


@pytest.mark.order(before="test_event_create_auth_user")
@pytest.mark.asyncio
async def test_event_empty(default_client):
    with patch("app.utils.cache.CacheRedis.exists", return_value=None), patch(
        "app.utils.cache.CacheRedis.set", return_value=[]
    ):
        response = await default_client.get("/api/v1/events/")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.order(after="test_event_create_auth_user")
@pytest.mark.asyncio
async def test_pagination_event_redis(default_client, docker_container):
    response_free = await default_client.get(
        "/api/v1/events/?price=free&status=published&skip=1&limit=5"
    )
    assert response_free.status_code == 200
    assert response_free.json() == []

    response_paid = await default_client.get(
        "/api/v1/events/?price=paid&status=published&startDate=later&skip=0&limit=20"
    )
    assert response_paid.status_code == 200
    data = response_paid.json()
    assert data is not None


@pytest.mark.order(after="test_event_create_auth_user")
@pytest.mark.asyncio
async def test_pagination_event(default_client):
    with patch(
        "app.utils.cache.CacheRedis.exists", return_value=None
    ) as mock_exists, patch(
        "app.utils.cache.CacheRedis.set", return_value=[]
    ) as mock_send:

        response_free = await default_client.get(
            "/api/v1/events/?price=free&status=published&skip=1&limit=5"
        )

        assert response_free.status_code == 200
        assert response_free.json() == []

        response_paid = await default_client.get(
            "/api/v1/events/?price=paid&status=published&startDate=later&skip=0&limit=20"
        )
        assert response_paid.status_code == 200
        data = response_paid.json()
        assert data is not None
        mock_exists.assert_called()
        mock_send.assert_called()


@pytest.mark.order(after="test_event_create_auth_user")
@pytest.mark.asyncio
async def test_partial_update_event(default_client):
    event_id, headers = await fake_events(default_client, "Test Event for Update")
    response = await default_client.patch(
        url=f"/api/v1/events/{event_id}",
        json={"title": "TestUpdateEvent"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json().get("title") == "TestUpdateEvent"
