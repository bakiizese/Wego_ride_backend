#!/usr/bin/python
"""Regression test: `order_by` used to be resolved via an unguarded
getattr() straight from the query string - a client could sort by any
column, including password_hash, or a relationship attribute that would
blow up deeper in SQLAlchemy. Now it's checked against an explicit
per-model allowlist."""
import pytest


def test_sorting_riders_by_password_hash_is_rejected(client, make_admin, auth_header):
    _, admin_token = make_admin(admin_level="moderator")

    r = client.get(
        "/api/v1/admin/riders?order_by=password_hash",
        headers=auth_header(admin_token),
    )

    assert r.status_code == 400


def test_sorting_riders_by_a_nonexistent_column_is_rejected(client, make_admin, auth_header):
    _, admin_token = make_admin(admin_level="moderator")

    r = client.get(
        "/api/v1/admin/riders?order_by=this_column_does_not_exist",
        headers=auth_header(admin_token),
    )

    assert r.status_code == 400


def test_sorting_riders_by_an_allowed_column_still_works(client, make_admin, auth_header):
    _, admin_token = make_admin(admin_level="moderator")

    r = client.get(
        "/api/v1/admin/riders?order_by=username", headers=auth_header(admin_token)
    )

    assert r.status_code == 200


def test_searching_admin_users_by_a_disallowed_column_is_rejected(
    client, make_admin, auth_header
):
    _, admin_token = make_admin(admin_level="moderator")

    r = client.get(
        "/api/v1/admin/user_by/Admin/password_hash/x", headers=auth_header(admin_token)
    )

    assert r.status_code == 400


@pytest.mark.parametrize("role", ["rider", "driver"])
def test_sorting_own_notifications_by_a_disallowed_column_is_rejected(
    client, make_user, auth_header, role
):
    _, token, _ = make_user(role.capitalize())

    r = client.get(
        f"/api/v1/{role}/notifications?order_by=message", headers=auth_header(token)
    )

    assert r.status_code == 400
