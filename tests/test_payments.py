import logging
from unittest.mock import patch

import pytest

from tests.conftest import fake_booking

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger()


@pytest.mark.asyncio
async def test_create_payments(default_client):
    booking_id, user_id = await fake_booking(default_client)
    payload = {
        "booking_id": booking_id,
        "user_id": user_id,
    }
    with patch("app.tasks.email_tasks.send_booking_confirmation.delay") as mock_delay:
        response = await default_client.post(
            url=f"/api/v1/bookings/{booking_id}/users/{user_id}/pay", json=payload
        )
        logger.warning(msg=f"Booking_id: {booking_id}, User_id: {user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["succeeded", "failed"]
        mock_delay.assert_called_once()
