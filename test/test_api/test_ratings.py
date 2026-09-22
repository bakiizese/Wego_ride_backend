#!/usr/bin/python
"""Coverage for the rating flow: a rider and driver can each rate the
other once a trip is actually completed, and the ratee's aggregate
average_rating/ratings_count update atomically."""

from datetime import datetime, timedelta

import pytest

from models import storage


@pytest.fixture
def completed_ride(client, make_admin, make_user, auth_header, confirm_chapa_payment):
    """Drives a full booking through to completion: book -> start -> pay
    -> end. Returns (trip_id, driver_token, rider_id, rider_token)."""
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
    rider_headers = auth_header(rider_token)

    r = client.post(
        "/api/v1/rider/book-ride", json={"trip_id": trip.id}, headers=rider_headers
    )
    assert r.status_code == 201, r.get_json()

    r = client.post(
        "/api/v1/driver/start-ride", json={"trip_id": trip.id}, headers=driver_headers
    )
    assert r.status_code == 200, r.get_json()

    r = client.post(
        "/api/v1/rider/pay-ride", json={"trip_id": trip.id}, headers=rider_headers
    )
    assert r.status_code == 201, r.get_json()
    tx_ref = r.get_json()["tx_ref"]

    r = confirm_chapa_payment(tx_ref)
    assert r.status_code == 200, r.get_json()

    r = client.post(
        "/api/v1/driver/end-ride", json={"trip_id": trip.id}, headers=driver_headers
    )
    assert r.status_code == 200, r.get_json()

    return trip.id, driver_token, rider_id, rider_token


def test_rider_can_rate_driver_after_completed_trip(client, completed_ride, auth_header):
    trip_id, driver_token, _, rider_token = completed_ride

    r = client.post(
        f"/api/v1/rider/rate-driver/{trip_id}",
        json={"score": 5, "comment": "great ride"},
        headers=auth_header(rider_token),
    )

    assert r.status_code == 201
    assert r.get_json()["rating"]["score"] == 5

    r = client.get("/api/v1/driver/profile", headers=auth_header(driver_token))
    assert r.get_json()["user"]["average_rating"] == 5
    assert r.get_json()["user"]["ratings_count"] == 1


def test_rating_the_same_trip_twice_is_rejected(client, completed_ride, auth_header):
    trip_id, _, _, rider_token = completed_ride
    headers = auth_header(rider_token)
    client.post(
        f"/api/v1/rider/rate-driver/{trip_id}", json={"score": 4}, headers=headers
    )

    r = client.post(
        f"/api/v1/rider/rate-driver/{trip_id}", json={"score": 2}, headers=headers
    )

    assert r.status_code == 409


def test_rating_an_incomplete_trip_is_rejected(
    client, make_admin, make_user, auth_header
):
    # no vehicle registration needed here - rate-driver only checks trip
    # completion, which fails before a vehicle would ever be looked at
    _, admin_token = make_admin(admin_level="superadmin")
    driver_id, _, _ = make_user("Driver")
    admin_headers = auth_header(admin_token)
    now = datetime.utcnow()
    client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 9.03, "longitude": 38.74, "address": "Bole2"},
        headers=admin_headers,
    )
    pickup = next(v for v in storage.get_objs("Location").all() if v.address == "Bole2")
    client.post(
        "/api/v1/admin/set-location",
        json={"latitude": 8.54, "longitude": 39.27, "address": "Adama2"},
        headers=admin_headers,
    )
    dropoff = next(v for v in storage.get_objs("Location").all() if v.address == "Adama2")
    client.post(
        "/api/v1/admin/set-ride",
        json={
            "driver_id": driver_id,
            "pickup_location_id": pickup.id,
            "dropoff_location_id": dropoff.id,
            "pickup_time": now.isoformat(),
            "dropoff_time": (now + timedelta(hours=2)).isoformat(),
            "fare": 100.0,
            "distance": 10.0,
            "status": "available",
            "driver_commission": 20,
        },
        headers=admin_headers,
    )
    trip = next(iter(storage.get_objs("Trip").all()))

    _, rider_token, _ = make_user("Rider")
    r = client.post(
        f"/api/v1/rider/rate-driver/{trip.id}",
        json={"score": 5},
        headers=auth_header(rider_token),
    )

    assert r.status_code == 400


def test_driver_can_rate_rider_after_completed_trip(client, completed_ride, auth_header):
    trip_id, driver_token, rider_id, rider_token = completed_ride

    r = client.post(
        f"/api/v1/driver/rate-rider/{trip_id}",
        json={"rider_id": rider_id, "score": 4, "comment": "polite"},
        headers=auth_header(driver_token),
    )

    assert r.status_code == 201

    r = client.get("/api/v1/rider/profile", headers=auth_header(rider_token))
    assert r.get_json()["user"]["average_rating"] == 4
    assert r.get_json()["user"]["ratings_count"] == 1


def test_driver_ratings_list_returns_submitted_rating(
    client, completed_ride, auth_header
):
    trip_id, driver_token, rider_id, rider_token = completed_ride
    client.post(
        f"/api/v1/driver/rate-rider/{trip_id}",
        json={"rider_id": rider_id, "score": 3},
        headers=auth_header(driver_token),
    )

    r = client.get("/api/v1/rider/ratings", headers=auth_header(rider_token))

    assert r.status_code == 200
    assert len(r.get_json()["ratings"]) == 1
    assert r.get_json()["ratings"][0]["score"] == 3
