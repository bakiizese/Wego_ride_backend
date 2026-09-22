#!/usr/bin/python
"""Coverage for the register/login/logout HTTP flows across all three
roles - previously zero of the 75 HTTP routes had any test coverage."""

import pytest


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_register_then_login_then_get_profile(client, role):
    import random
    import string
    import uuid

    suffix = uuid.uuid4().hex[:8]
    data = {
        "username": f"user_{suffix}",
        "first_name": "Test",
        "last_name": role,
        "email": f"{suffix}@example.com",
        "phone_number": "251" + "".join(random.choices(string.digits, k=9)),
        "password_hash": "testpass123",
        "payment_method": "cash",
    }

    r = client.post(f"/api/v1/{role}/register", json=data)
    assert r.status_code == 201

    r = client.post(
        f"/api/v1/{role}/login",
        json={"email": data["email"], "password_hash": data["password_hash"]},
    )
    assert r.status_code == 200
    token = r.get_json()["user"]

    r = client.get(
        f"/api/v1/{role}/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.get_json()["user"]["email"] == data["email"]
    # password hash must never be returned
    assert "password_hash" not in r.get_json()["user"]


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_login_with_wrong_password_fails(client, make_user, role):
    _, _, data = make_user(role.capitalize())

    r = client.post(
        f"/api/v1/{role}/login",
        json={"email": data["email"], "password_hash": "definitely_wrong"},
    )

    assert r.status_code == 400


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_logout_blacklists_the_token(client, make_user, role):
    _, token, _ = make_user(role.capitalize())
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(f"/api/v1/{role}/logout", headers=headers)
    assert r.status_code == 200

    r = client.get(f"/api/v1/{role}/profile", headers=headers)
    assert r.status_code == 401
    assert "blacklisted" in r.get_json().get("error", "")


@pytest.mark.parametrize("role", ["rider", "driver", "admin"])
def test_missing_auth_header_returns_400(client, role):
    path = "profile" if role != "admin" else "riders"
    r = client.get(f"/api/v1/{role}/{path}")
    assert r.status_code == 400


@pytest.mark.parametrize("role", ["rider", "driver", "admin"])
def test_malformed_auth_header_returns_400_not_500(client, role):
    """regression test: a header with no space used to raise an unguarded
    IndexError (token.split(' ')[1]), surfacing as a raw 500"""
    path = "profile" if role != "admin" else "riders"
    r = client.get(
        f"/api/v1/{role}/{path}", headers={"Authorization": "NoSpaceHereAtAll"}
    )
    assert r.status_code == 400


@pytest.mark.parametrize("role", ["rider", "driver", "admin"])
def test_garbage_token_returns_401_not_500(client, role):
    path = "profile" if role != "admin" else "riders"
    r = client.get(
        f"/api/v1/{role}/{path}", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert r.status_code == 401


def test_empty_json_body_returns_400_not_500(client):
    """regression test: request.get_json() returning None on an empty body
    used to slip past the try/except and crash with an unguarded
    AttributeError on the next line's .keys() call"""
    r = client.post(
        "/api/v1/rider/register", data="null", content_type="application/json"
    )
    assert r.status_code == 400


def test_register_rejects_non_numeric_phone_number(client):
    import uuid

    suffix = uuid.uuid4().hex[:8]
    r = client.post(
        "/api/v1/rider/register",
        json={
            "username": f"user_{suffix}",
            "first_name": "Test",
            "last_name": "Rider",
            "email": f"{suffix}@example.com",
            "phone_number": "not-a-number",
            "password_hash": "testpass123",
            "payment_method": "cash",
        },
    )
    assert r.status_code == 400
