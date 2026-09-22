#!/usr/bin/python
"""Coverage for the Chapa payment flow: pay-ride only ever *initiates*
a payment now (server computes the charge, never the client) and the
webhook is the only thing that can flip it to paid. No real HTTP calls
leave the process - `fake_payment_gateway` (conftest.py, autouse) stands
in for the real Chapa client."""

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


def test_pay_ride_ignores_client_supplied_amount_and_uses_trip_fare(
    client, booked_ride, auth_header
):
    trip_id, _, _, rider_token = booked_ride

    r = client.post(
        "/api/v1/rider/pay-ride",
        # a client-supplied amount is not even part of the schema anymore -
        # this should have zero effect on what actually gets charged
        json={"trip_id": trip_id, "amount": 1.0},
        headers=auth_header(rider_token),
    )

    assert r.status_code == 201
    body = r.get_json()
    assert "checkout_url" in body
    assert "tx_ref" in body

    payment = storage.get("Payment", trip_id=trip_id)
    assert payment.amount == 250.0
    assert payment.payment_status == "pending"
    assert payment.provider == "chapa"
    assert payment.provider_tx_ref == body["tx_ref"]


def test_webhook_confirms_payment_and_updates_totalpayment(
    client, booked_ride, auth_header, confirm_chapa_payment
):
    trip_id, _, _, rider_token = booked_ride
    r = client.post(
        "/api/v1/rider/pay-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )
    tx_ref = r.get_json()["tx_ref"]
    # snapshot plain values, not the ORM object - storage.update()'s
    # synchronize_session="fetch" mutates any already-loaded object for
    # the same row in place, so a held object reference isn't a real
    # "before" snapshot
    paid_before = storage.get("TotalPayment", trip_id=trip_id).number_of_riders_paid
    not_paid_before = storage.get(
        "TotalPayment", trip_id=trip_id
    ).number_of_riders_not_paid
    revenue_before = storage.get("TotalPayment", trip_id=trip_id).total_revenue

    r = confirm_chapa_payment(tx_ref)

    assert r.status_code == 200
    payment = storage.get("Payment", provider_tx_ref=tx_ref)
    assert payment.payment_status == "paid"

    totalpayment = storage.get("TotalPayment", trip_id=trip_id)
    assert totalpayment.number_of_riders_paid == paid_before + 1
    assert totalpayment.number_of_riders_not_paid == not_paid_before - 1
    assert totalpayment.total_revenue == revenue_before + 250.0


def test_webhook_rejects_an_invalid_signature(client, booked_ride, auth_header):
    trip_id, _, _, rider_token = booked_ride
    r = client.post(
        "/api/v1/rider/pay-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )
    tx_ref = r.get_json()["tx_ref"]

    r = client.post(
        "/api/v1/webhooks/chapa",
        json={"tx_ref": tx_ref, "status": "success"},
        headers={"Chapa-Signature": "not-the-right-signature"},
    )

    assert r.status_code == 401
    assert storage.get("Payment", provider_tx_ref=tx_ref).payment_status == "pending"


def test_webhook_for_an_unknown_tx_ref_is_rejected(client, confirm_chapa_payment):
    r = confirm_chapa_payment("this-tx-ref-does-not-exist")

    assert r.status_code == 404


def test_webhook_is_idempotent_for_an_already_paid_payment(
    client, booked_ride, auth_header, confirm_chapa_payment
):
    trip_id, _, _, rider_token = booked_ride
    r = client.post(
        "/api/v1/rider/pay-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )
    tx_ref = r.get_json()["tx_ref"]
    confirm_chapa_payment(tx_ref)
    totalpayment_after_first = storage.get("TotalPayment", trip_id=trip_id)

    r = confirm_chapa_payment(tx_ref)

    assert r.status_code == 200
    totalpayment = storage.get("TotalPayment", trip_id=trip_id)
    assert (
        totalpayment.number_of_riders_paid
        == totalpayment_after_first.number_of_riders_paid
    )
    assert totalpayment.total_revenue == totalpayment_after_first.total_revenue


def test_webhook_marks_failed_when_gateway_verification_disagrees(
    client, booked_ride, auth_header, confirm_chapa_payment, fake_payment_gateway
):
    trip_id, _, _, rider_token = booked_ride
    r = client.post(
        "/api/v1/rider/pay-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )
    tx_ref = r.get_json()["tx_ref"]
    # simulate Chapa's own verify-transaction endpoint disagreeing with
    # what the webhook payload claims - this is exactly the case the
    # defense-in-depth verify_payment() call exists to catch
    fake_payment_gateway.outcomes[tx_ref] = "failed"

    r = confirm_chapa_payment(tx_ref, status="success")

    assert r.status_code == 200
    payment = storage.get("Payment", provider_tx_ref=tx_ref)
    assert payment.payment_status == "failed"
    totalpayment = storage.get("TotalPayment", trip_id=trip_id)
    assert totalpayment.number_of_riders_paid == 0


def test_cannot_initiate_payment_again_once_already_paid(
    client, booked_ride, auth_header, confirm_chapa_payment
):
    trip_id, _, _, rider_token = booked_ride
    headers = auth_header(rider_token)
    r = client.post("/api/v1/rider/pay-ride", json={"trip_id": trip_id}, headers=headers)
    confirm_chapa_payment(r.get_json()["tx_ref"])

    r = client.post("/api/v1/rider/pay-ride", json={"trip_id": trip_id}, headers=headers)

    assert r.status_code == 200
    assert "already paid" in r.get_json()["error"]


def test_end_ride_blocks_while_payment_is_still_pending(client, booked_ride, auth_header):
    trip_id, driver_token, _, rider_token = booked_ride
    driver_headers = auth_header(driver_token)
    client.post(
        "/api/v1/rider/pay-ride",
        json={"trip_id": trip_id},
        headers=auth_header(rider_token),
    )
    client.post(
        "/api/v1/driver/start-ride", json={"trip_id": trip_id}, headers=driver_headers
    )

    r = client.post(
        "/api/v1/driver/end-ride", json={"trip_id": trip_id}, headers=driver_headers
    )

    assert r.status_code == 409
    assert "unpaid" in r.get_json()
