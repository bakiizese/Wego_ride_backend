#!/usr/bin/python
"""Regression test: PUT /profile used to unconditionally require
password_hash/old_password even for an unrelated field update like
first_name - now the password-change branch only runs when requested."""
import pytest


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_can_update_first_name_without_touching_password(
    client, make_user, auth_header, role
):
    _, token, _ = make_user(role.capitalize())
    headers = auth_header(token)

    r = client.put(
        f"/api/v1/{role}/profile", json={"first_name": "Renamed"}, headers=headers
    )

    assert r.status_code == 200
    r = client.get(f"/api/v1/{role}/profile", headers=headers)
    assert r.get_json()["user"]["first_name"] == "Renamed"


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_password_change_requires_old_password(client, make_user, auth_header, role):
    _, token, _ = make_user(role.capitalize())

    r = client.put(
        f"/api/v1/{role}/profile",
        json={"password_hash": "a_new_password123"},
        headers=auth_header(token),
    )

    assert r.status_code == 400
    assert "old_password" in r.get_json()["error"]


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_password_change_rejects_wrong_old_password(
    client, make_user, auth_header, role
):
    _, token, _ = make_user(role.capitalize())

    r = client.put(
        f"/api/v1/{role}/profile",
        json={"password_hash": "a_new_password123", "old_password": "wrong_one"},
        headers=auth_header(token),
    )

    assert r.status_code == 400


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_password_change_succeeds_with_correct_old_password(
    client, make_user, auth_header, role
):
    user_id, token, data = make_user(role.capitalize())

    r = client.put(
        f"/api/v1/{role}/profile",
        json={
            "password_hash": "a_new_password123",
            "old_password": data["password_hash"],
        },
        headers=auth_header(token),
    )
    assert r.status_code == 200

    # old token still works until logout/expiry, but the new password
    # should now be the one that authenticates
    r = client.post(
        f"/api/v1/{role}/login",
        json={"email": data["email"], "password_hash": "a_new_password123"},
    )
    assert r.status_code == 200
