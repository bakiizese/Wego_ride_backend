#!/usr/bin/python
"""Coverage for admin-register's bootstrap behavior: the very first
admin can be created without auth (otherwise there'd be no way to
create it at all, since every other path to get a superadmin token
requires one already existing), and this closes the moment a real
admin exists. Also covers the 400 handler actually surfacing the real
reason instead of one generic message for every case."""

import random
import string
import uuid


def _admin_payload(**overrides):
    suffix = uuid.uuid4().hex[:8]
    data = {
        "username": f"admin_{suffix}",
        "first_name": "Test",
        "last_name": "Admin",
        "email": f"{suffix}@example.com",
        "phone_number": "251" + "".join(random.choices(string.digits, k=9)),
        "password_hash": "testpass123",
        "admin_level": "moderator",
    }
    data.update(overrides)
    return data


def test_bootstrap_creates_first_superadmin_without_auth(client):
    r = client.post("/api/v1/admin/admin-register", json=_admin_payload())

    assert r.status_code == 201
    body = r.get_json()
    assert "user" in body
    assert "token" in body

    # the returned token actually works for an authenticated admin route
    r = client.get(
        "/api/v1/admin/riders", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert r.status_code in (200, 404)  # 404 just means no riders yet, still authorized


def test_bootstrap_forces_superadmin_regardless_of_requested_level(client):
    r = client.post(
        "/api/v1/admin/admin-register",
        json=_admin_payload(admin_level="moderator"),
    )
    token = r.get_json()["token"]

    # a real moderator couldn't create another admin (see test below) -
    # if bootstrap had honored "moderator" here, this would 403
    r = client.post(
        "/api/v1/admin/admin-register",
        json=_admin_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


def test_registering_a_second_admin_requires_auth(client):
    client.post("/api/v1/admin/admin-register", json=_admin_payload())

    r = client.post("/api/v1/admin/admin-register", json=_admin_payload())

    assert r.status_code == 400
    # the actual reason, not a generic catch-all - this is what the
    # global 400 handler used to swallow
    assert r.get_json()["error"] == "Authorization header missing"


def test_registering_a_second_admin_rejects_a_non_superadmin_token(
    client, make_admin, auth_header
):
    client.post("/api/v1/admin/admin-register", json=_admin_payload())
    _, moderator_token = make_admin(admin_level="moderator")

    r = client.post(
        "/api/v1/admin/admin-register",
        json=_admin_payload(),
        headers=auth_header(moderator_token),
    )

    assert r.status_code == 403


def test_registering_a_second_admin_succeeds_with_a_superadmin_token(
    client, make_admin, auth_header
):
    client.post("/api/v1/admin/admin-register", json=_admin_payload())
    _, superadmin_token = make_admin(admin_level="superadmin")

    r = client.post(
        "/api/v1/admin/admin-register",
        json=_admin_payload(),
        headers=auth_header(superadmin_token),
    )

    assert r.status_code == 201
    assert "token" not in r.get_json()
