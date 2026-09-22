#!/usr/bin/python
"""Coverage for the vehicle registration endpoints - previously the only
way to attach a Vehicle to a Driver was through the console, so no HTTP
route had ever been exercised."""


def _vehicle_payload(**overrides):
    data = {
        "type": "sedan",
        "model": "corolla",
        "color": "white",
        "seating_capacity": 4,
        "plate_number": "AA-123-BB",
    }
    data.update(overrides)
    return data


def test_driver_can_register_a_vehicle(client, make_user, auth_header):
    _, driver_token, _ = make_user("Driver")
    headers = auth_header(driver_token)

    r = client.post("/api/v1/driver/vehicle", json=_vehicle_payload(), headers=headers)

    assert r.status_code == 201
    assert r.get_json()["vehicle"]["plate_number"] == "AA-123-BB"


def test_registering_a_second_vehicle_is_rejected(client, make_user, auth_header):
    _, driver_token, _ = make_user("Driver")
    headers = auth_header(driver_token)
    client.post("/api/v1/driver/vehicle", json=_vehicle_payload(), headers=headers)

    r = client.post(
        "/api/v1/driver/vehicle",
        json=_vehicle_payload(plate_number="CC-999-DD"),
        headers=headers,
    )

    assert r.status_code == 409


def test_get_vehicle_returns_404_when_none_registered(client, make_user, auth_header):
    _, driver_token, _ = make_user("Driver")
    headers = auth_header(driver_token)

    r = client.get("/api/v1/driver/vehicle", headers=headers)

    assert r.status_code == 404


def test_driver_can_fetch_and_update_their_vehicle(client, make_user, auth_header):
    _, driver_token, _ = make_user("Driver")
    headers = auth_header(driver_token)
    client.post("/api/v1/driver/vehicle", json=_vehicle_payload(), headers=headers)

    r = client.get("/api/v1/driver/vehicle", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["vehicle"]["color"] == "white"

    r = client.put(
        "/api/v1/driver/vehicle",
        json={"color": "black", "license_number": "LIC-001"},
        headers=headers,
    )
    assert r.status_code == 200

    r = client.get("/api/v1/driver/vehicle", headers=headers)
    assert r.get_json()["vehicle"]["color"] == "black"

    r = client.get("/api/v1/driver/profile", headers=headers)
    assert r.get_json()["user"]["license_number"] == "LIC-001"


def test_booking_fails_cleanly_when_driver_has_no_vehicle(
    client, make_admin, make_user, auth_header
):
    _, admin_token = make_admin(admin_level="superadmin")
    driver_id, _, _ = make_user("Driver")
    admin_headers = auth_header(admin_token)

    from datetime import datetime, timedelta

    from models import storage

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
    client.post(
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
    trip = next(iter(storage.get_objs("Trip").all()))

    _, rider_token, _ = make_user("Rider")
    r = client.post(
        "/api/v1/rider/book-ride",
        json={"trip_id": trip.id},
        headers=auth_header(rider_token),
    )

    assert r.status_code == 409
    assert "vehicle" in r.get_json()["error"]
