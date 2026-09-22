#!/usr/bin/python
"""Coverage for the /rides Socket.IO namespace: connecting requires a
valid JWT, joining a trip's room requires actually being party to that
trip, and the state-transition routes push a real ride_status_update to
whoever's joined."""

from datetime import datetime, timedelta

import pytest

from models import storage


@pytest.fixture
def booked_ride(client, make_admin, make_user, auth_header):
    """Admin + driver-with-vehicle + trip + a rider who has booked it.
    Returns (trip_id, driver_token, rider_id, rider_token)."""
    _, admin_token = make_admin(admin_level="superadmin")
    driver_id, driver_token, _ = make_user("Driver")
    admin_headers = auth_header(admin_token)
    driver_headers = auth_header(driver_token)

    client.post(
        "/api/v1/driver/vehicle",
        json={
            "type": "sedan",
            "model": "corolla",
            "color": "white",
            "seating_capacity": 4,
            "plate_number": "AA-123-BB",
        },
        headers=driver_headers,
    )

    client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 9.03, "longitude": 38.74, "address": "Bole"},
        headers=admin_headers,
    )
    pickup = next(v for v in storage.get_objs("Location").all() if v.address == "Bole")
    client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 8.54, "longitude": 39.27, "address": "Adama"},
        headers=admin_headers,
    )
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
        headers=admin_headers,
    )
    assert r.status_code == 200, r.get_json()
    trip = next(iter(storage.get_objs("Trip").all()))

    rider_id, rider_token, _ = make_user("Rider")
    r = client.post(
        "/api/v1/rider/book-ride",
        json={"trip_id": trip.id},
        headers=auth_header(rider_token),
    )
    assert r.status_code == 201, r.get_json()

    return trip.id, driver_token, rider_id, rider_token


def test_connect_without_a_token_is_rejected(socket_client):
    sio = socket_client()

    assert not sio.is_connected(namespace="/rides")


def test_connect_with_an_invalid_token_is_rejected(socket_client):
    sio = socket_client("this-is-not-a-real-jwt")

    assert not sio.is_connected(namespace="/rides")


def test_connect_with_a_valid_token_succeeds(socket_client, make_user):
    _, token, _ = make_user("Rider")

    sio = socket_client(token)

    assert sio.is_connected(namespace="/rides")


def test_rider_can_join_a_trip_they_booked(socket_client, booked_ride):
    trip_id, _, _, rider_token = booked_ride
    sio = socket_client(rider_token)

    sio.emit("join", {"trip_id": trip_id}, namespace="/rides")

    received = sio.get_received(namespace="/rides")
    events = [msg["name"] for msg in received]
    assert "joined" in events


def test_driver_can_join_their_assigned_trip(socket_client, booked_ride):
    trip_id, driver_token, _, _ = booked_ride
    sio = socket_client(driver_token)

    sio.emit("join", {"trip_id": trip_id}, namespace="/rides")

    received = sio.get_received(namespace="/rides")
    events = [msg["name"] for msg in received]
    assert "joined" in events


def test_rider_cannot_join_a_trip_they_have_no_part_in(
    socket_client, booked_ride, make_user
):
    trip_id, _, _, _ = booked_ride
    _, other_rider_token, _ = make_user("Rider")
    sio = socket_client(other_rider_token)

    sio.emit("join", {"trip_id": trip_id}, namespace="/rides")

    received = sio.get_received(namespace="/rides")
    events = [msg["name"] for msg in received]
    assert "joined" not in events
    assert "error" in events


def test_starting_a_ride_emits_update_to_joined_clients(
    client, socket_client, booked_ride, auth_header
):
    trip_id, driver_token, _, rider_token = booked_ride
    sio = socket_client(rider_token)
    sio.emit("join", {"trip_id": trip_id}, namespace="/rides")
    sio.get_received(namespace="/rides")  # drain the "joined" event

    r = client.post(
        "/api/v1/driver/start-ride",
        json={"trip_id": trip_id},
        headers=auth_header(driver_token),
    )
    assert r.status_code == 200

    received = sio.get_received(namespace="/rides")
    updates = [msg["args"][0] for msg in received if msg["name"] == "ride_status_update"]
    assert len(updates) == 1
    assert updates[0]["trip_id"] == trip_id
    assert updates[0]["event"] == "started"


def test_a_client_not_in_the_room_does_not_receive_the_update(
    client, socket_client, booked_ride, make_user, auth_header
):
    trip_id, driver_token, _, _ = booked_ride
    # connected, but never joined this trip's room
    _, bystander_token, _ = make_user("Rider")
    sio = socket_client(bystander_token)

    client.post(
        "/api/v1/driver/start-ride",
        json={"trip_id": trip_id},
        headers=auth_header(driver_token),
    )

    received = sio.get_received(namespace="/rides")
    assert not any(msg["name"] == "ride_status_update" for msg in received)
