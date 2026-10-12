from unittest.mock import patch
from uuid import uuid4

import pytest

from .conftest import auth_header, create_user

test_email = f"test-{uuid4().hex[:9]}@example.com"
TEST_TOKEN = "sd45as7r4f12s1c-test"


@pytest.mark.asyncio
async def test_register_user(default_client):

    payload = {
        "email": test_email,
        "full_name": "Test User",
        "hashed_password": "test_passwordP_32",
    }
    with patch(
        "app.tasks.email_tasks.send_confirmation_email.delay"
    ) as mock_delay, patch(
        "app.services.auth_services.serializer.dumps", return_value=TEST_TOKEN
    ) as mock_token:

        response = await default_client.post(url="/api/v1/auth/register", json=payload)
        assert response.status_code == 200
        mock_delay.assert_called_once()
        mock_delay.assert_called_once_with(test_email, TEST_TOKEN)


@pytest.mark.asyncio
async def test_user_login_success(default_client):
    payload = {"username": test_email, "password": "test_passwordP_32"}

    response = await default_client.post(url="/api/v1/auth/login", data=payload)

    assert response.status_code == 200
    assert response.json().get("token_type") == "Bearer"
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_user_login_failure(default_client):
    payload = {"username": test_email, "password": "wrong_passwordP_32"}

    response = await default_client.post(url="/api/v1/auth/login", data=payload)

    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid password!"


@pytest.mark.asyncio
async def test_auth_token_success(default_client):
    payload = {"username": test_email, "password": "test_passwordP_32"}

    response = await default_client.post(url="/api/v1/auth/login", data=payload)
    token = response.json().get("access_token")
    headers = auth_header(token)

    response = await default_client.post(url="/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json().get("email") == test_email


@pytest.mark.asyncio
async def test_auth_not_token(default_client):
    response = await default_client.post(url="/api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirm_register(default_client):
    email, _, _ = await create_user(default_client)
    test_token = "IEO546545DFfd1633fg6eIIo"
    with patch(
        "app.services.auth_services.serializer.loads", return_value=email
    ) as mock_serializer:
        response = await default_client.get(
            url=f"/api/v1/auth/register_confirm?token={test_token}"
        )
        assert response.status_code == 200
        mock_serializer.assert_called_once_with(
            test_token,
            max_age=3600,
        )
