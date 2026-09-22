#!/usr/bin/python
"""Regression test: `order_by` used to be resolved via an unguarded
getattr() straight from the query string - a client could sort by any
column, including password_hash, or a relationship attribute that would
blow up deeper in SQLAlchemy. Now it's checked against an explicit
per-model allowlist."""

from datetime import datetime, timedelta

import pytest

from models import storage


def test_sorting_riders_by_password_hash_is_rejected(client, make_admin, auth_header):
    _, admin_token = make_admin(admin_level="moderator")

    r = client.get(
        "/api/v1/admin/riders?order_by=password_hash",
        headers=auth_header(admin_token),
    )

    assert r.status_code == 400


def test_sorting_riders_by_a_nonexistent_column_is_rejected(
    client, make_admin, auth_header
):
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


def test_default_page_still_includes_a_row_stored_slightly_in_the_future(
    client, make_admin, make_user, auth_header
):
    """Regression: `updated_at` is stored in a MySQL DATETIME column with
    no fractional-seconds precision, so a Python timestamp with
    microseconds gets *rounded* (round-to-nearest-second) on insert, not
    truncated - a row's stored value can land up to just under 0.5s
    "in the future" relative to when it was actually written. The
    default (no `next_page` cursor) page used to filter on
    `updated_at < datetime.now()` at read time with no slack (and using
    local server time to boot), so a row rounded forward past that
    instant would silently drop off the very first page right after
    being created. Simulates the worst-case rounding directly rather
    than relying on hitting the real timing window."""
    _, admin_token = make_admin(admin_level="moderator")
    rider_id, _, _ = make_user("Rider")

    storage.update(
        "Rider", rider_id, updated_at=datetime.utcnow() + timedelta(milliseconds=450)
    )

    r = client.get("/api/v1/admin/riders", headers=auth_header(admin_token))

    assert r.status_code == 200
    assert any(r_["id"] == rider_id for r_ in r.get_json()["riders"])
