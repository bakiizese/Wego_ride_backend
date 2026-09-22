#!/usr/bin/python
"""Regression test for the highest-priority bug this project shipped:
`delete_user`/`revalidate_user` checked `cls == "admin"` (lowercase) to
decide whether to require superadmin - which never matched the actual
loop value `"Admin"`, letting any admin (even a moderator) delete or
revalidate another admin, including a superadmin."""


def test_moderator_cannot_delete_a_superadmin(client, make_admin, auth_header):
    from models import storage

    make_admin(admin_level="superadmin")
    _, moderator_token = make_admin(admin_level="moderator")
    superadmin = next(iter(storage.get_all("Admin", admin_level="superadmin").values()))

    r = client.put(
        f"/api/v1/admin/delete-user/{superadmin.id}",
        headers=auth_header(moderator_token),
    )

    assert r.status_code == 403
    assert storage.get("Admin", id=superadmin.id).deleted is False


def test_moderator_cannot_revalidate_a_superadmin(client, make_admin, auth_header):
    from models import storage

    _, superadmin_token = make_admin(admin_level="superadmin")
    _, moderator_token = make_admin(admin_level="moderator")

    superadmin = next(iter(storage.get_all("Admin", admin_level="superadmin").values()))
    # mark deleted directly (bypassing the API) so revalidate has something to act on
    storage.update("Admin", superadmin.id, deleted=True)

    r = client.put(
        f"/api/v1/admin/revalidate-user/{superadmin.id}",
        headers=auth_header(moderator_token),
    )

    assert r.status_code == 403
    assert storage.get("Admin", id=superadmin.id).deleted is True


def test_moderator_cannot_block_or_unblock_a_superadmin(client, make_admin, auth_header):
    from models import storage

    make_admin(admin_level="superadmin")
    _, moderator_token = make_admin(admin_level="moderator")
    superadmin = next(iter(storage.get_all("Admin", admin_level="superadmin").values()))

    r = client.put(
        f"/api/v1/admin/block-user/{superadmin.id}",
        headers=auth_header(moderator_token),
    )
    assert r.status_code == 403
    assert storage.get("Admin", id=superadmin.id).blocked is False


def test_superadmin_can_delete_a_moderator(client, make_admin, auth_header):
    from models import storage

    _, superadmin_token = make_admin(admin_level="superadmin")
    moderator_id, _ = make_admin(admin_level="moderator")

    r = client.put(
        f"/api/v1/admin/delete-user/{moderator_id}",
        headers=auth_header(superadmin_token),
    )

    assert r.status_code == 200
    assert storage.get("Admin", id=moderator_id).deleted is True


def test_moderator_can_still_delete_a_rider_or_driver(
    client, make_admin, make_user, auth_header
):
    from models import storage

    _, moderator_token = make_admin(admin_level="moderator")
    rider_id, _, _ = make_user("Rider")

    r = client.put(
        f"/api/v1/admin/delete-user/{rider_id}",
        headers=auth_header(moderator_token),
    )

    assert r.status_code == 200
    assert storage.get("Rider", id=rider_id).deleted is True
