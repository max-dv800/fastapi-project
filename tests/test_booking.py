import asyncio

import pytest

from tests.conftest import auth_header, create_user, fake_events, user_login


@pytest.mark.order(after="test_events.py::test_event_empty")
@pytest.mark.asyncio
async def test_create_booking(default_client):
    user1_email, user1_password, user_id1 = await create_user(default_client)
    user2_email, user2_password, user_id2 = await create_user(default_client)
    token1 = await user_login(default_client, user1_email, user1_password)
    token2 = await user_login(default_client, user2_email, user2_password)
    headers1 = auth_header(token1)
    headers2 = auth_header(token2)
    event_id, _ = await fake_events(default_client, "Test Event")
    payload1 = {"event_id": f"{event_id}", "seats": 10, "user_id": f"{user_id1}"}
    payload2 = {"event_id": f"{event_id}", "seats": 10, "user_id": f"{user_id2}"}

    booking1 = default_client.post(
        url=f"/api/v1/events/{event_id}/bookings", json=payload1, headers=headers1
    )
    booking2 = default_client.post(
        url=f"/api/v1/events/{event_id}/bookings", json=payload2, headers=headers2
    )

    response1, response2 = await asyncio.gather(booking1, booking2)

    if response1.status_code == 200:
        assert response2.status_code == 403
        assert response2.json().get("detail") == "No available seats!"
    else:
        assert response2.status_code == 200


@pytest.mark.order(after="test_create_booking")
@pytest.mark.asyncio
async def test_get_user_booking(default_client):
    user_email, user_passsword, _ = await create_user(default_client)
    token = await user_login(default_client, user_email, user_passsword)
    headers = auth_header(token)

    response = await default_client.get("api/v1/bookings", headers=headers)

    assert response.status_code == 200, f"Ошибка: {response.text}"
    assert response.json().get("my_booking") == []
