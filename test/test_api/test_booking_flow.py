#!/usr/bin/python
"""Coverage for the core booking state machine: book -> ride-status ->
cancel-ride / start-ride / end-ride.
"""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def ride_setup(client, make_admin, make_user, auth_header):
    """Admin creates two locations + a ride assigned to a driver with a
    registered vehicle. Returns (trip_id, driver_token, admin_token)."""
    _, admin_token = make_admin(admin_level="superadmin")
    driver_id, driver_token, _ = make_user("Driver")

    r = client.post(
        "/api/v1/driver/vehicle",
        json={
            "type": "sedan",
            "model": "corolla",
            "color": "white",
            "seating_capacity": 4,
            "plate_number": "AA-123-BB",
        },
        headers=auth_header(driver_token),
    )
    assert r.status_code == 201, r.get_json()

    headers = auth_header(admin_token)
    r = client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 9.03, "longitude": 38.74, "address": "Bole"},
        headers=headers,
    )
    assert r.status_code == 200
    # set-location doesn't return the id, so look it up
    from models import storage

    pickup = next(v for v in storage.get_objs("Location").all() if v.address == "Bole")

    r = client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 8.54, "longitude": 39.27, "address": "Adama"},
        headers=headers,
    )
    assert r.status_code == 200
    dropoff = next(v for v in storage.get_objs("Location").all() if v.address == "Adama")

    now = datetime.utcnow()
    r = client.post(
        "/api/v1/admin/set-ride",
        json={
            "driver_id": driver_id,
            "pickup_location_id": pickup.id,
            "dropoff_location_id": dropoff.id,
            "pickup_time": now.isoformat(),
            "dropoff_time": (now + timedelta(hours=2)).isoformat(),
            "fare": 250.0,
            "distance": 100.0,
            "status": "available",
            "driver_commission": 20,
        },
        headers=headers,
    )
    assert r.status_code == 200, r.get_json()

    trip = next(iter(storage.get_objs("Trip").all()))
    return trip.id, driver_token, admin_token


def test_rider_can_book_an_available_ride(client, ride_setup, make_user, auth_header):
    trip_id, _, _ = ride_setup
    _, rider_token, _ = make_user("Rider")

    r = client.post(
        "/api/v1/rider/book-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )

    assert r.status_code == 201


def test_booked_ride_shows_up_in_booked_rides(client, ride_setup, make_user, auth_header):
    trip_id, _, _ = ride_setup
    _, rider_token, _ = make_user("Rider")
    headers = auth_header(rider_token)
    client.post("/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=headers)

    r = client.get("/api/v1/rider/booked-ride", headers=headers)

    assert r.status_code == 200
    assert any(trip_id in key for key in r.get_json()["ride"].keys())


def test_rider_can_cancel_before_ride_starts(client, ride_setup, make_user, auth_header):
    trip_id, _, _ = ride_setup
    _, rider_token, _ = make_user("Rider")
    headers = auth_header(rider_token)
    client.post("/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=headers)

    r = client.post(
        "/api/v1/rider/cancel-ride", json={"trip_id": trip_id}, headers=headers
    )

    assert r.status_code == 200


def test_rider_cannot_cancel_after_driver_starts_ride(
    client, ride_setup, make_user, auth_header
):
    trip_id, driver_token, _ = ride_setup
    _, rider_token, _ = make_user("Rider")
    rider_headers = auth_header(rider_token)
    client.post(
        "/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=rider_headers
    )

    r = client.post(
        "/api/v1/driver/start-ride",
        json={"trip_id": trip_id},
        headers=auth_header(driver_token),
    )
    assert r.status_code == 200

    r = client.post(
        "/api/v1/rider/cancel-ride", json={"trip_id": trip_id}, headers=rider_headers
    )

    assert r.status_code == 409


def test_driver_cannot_end_ride_with_unpaid_riders(
    client, ride_setup, make_user, auth_header
):
    trip_id, driver_token, _ = ride_setup
    _, rider_token, _ = make_user("Rider")
    rider_headers = auth_header(rider_token)
    driver_headers = auth_header(driver_token)
    client.post(
        "/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=rider_headers
    )
    client.post(
        "/api/v1/driver/start-ride", json={"trip_id": trip_id}, headers=driver_headers
    )

    r = client.post(
        "/api/v1/driver/end-ride", json={"trip_id": trip_id}, headers=driver_headers
    )

    assert r.status_code == 409
    assert "unpaid" in r.get_json()


def test_double_booking_the_same_ride_is_a_noop(
    client, ride_setup, make_user, auth_header
):
    trip_id, _, _ = ride_setup
    _, rider_token, _ = make_user("Rider")
    headers = auth_header(rider_token)
    client.post("/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=headers)

    r = client.post("/api/v1/rider/book-ride", json={"trip_id": trip_id}, headers=headers)

    assert r.status_code == 200
    assert "already booked" in r.get_json()["error"]
