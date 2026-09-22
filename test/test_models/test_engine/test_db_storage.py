#!/usr/bin/python
import uuid

from auth.authentication import Auth
from models import storage

auth = Auth()


def _unique_driver_kwargs(**overrides):
    suffix = uuid.uuid4().hex[:8]
    kwargs = dict(
        username=f"driver_{suffix}",
        first_name="Test",
        last_name="Driver",
        email=f"{suffix}@example.com",
        phone_number="251" + suffix[:9].ljust(9, "0"),
        password_hash="mypassword",
        payment_method="cash",
    )
    kwargs.update(overrides)
    return kwargs


def _make_driver(**overrides):
    kwargs = _unique_driver_kwargs(**overrides)
    driver_id, ok = auth.register_user("Driver", **kwargs)
    assert ok is True
    return driver_id, kwargs


def test_get_returns_the_matching_instance():
    driver_id, kwargs = _make_driver()

    driver = storage.get("Driver", id=driver_id)

    assert driver is not None
    assert driver.username == kwargs["username"]


def test_get_returns_none_for_no_match():
    assert storage.get("Driver", id="not-a-real-id") is None


def test_get_all_returns_a_dict_keyed_by_class_and_id():
    driver_id, kwargs = _make_driver()

    result = storage.get_all("Driver", phone_number=kwargs["phone_number"])

    assert isinstance(result, dict)
    assert f"Driver.{driver_id}" in result


def test_get_all_returns_false_for_an_invalid_column():
    assert storage.get_all("Driver", not_a_real_column="x") is False


def test_delete_removes_the_instance():
    driver_id, _ = _make_driver()
    assert storage.get("Driver", id=driver_id) is not None

    storage.delete("Driver", f"id={driver_id}")

    assert storage.get("Driver", id=driver_id) is None


def test_update_changes_a_single_field():
    driver_id, _ = _make_driver()

    storage.update("Driver", driver_id, username="renamed_driver")

    assert storage.get("Driver", id=driver_id).username == "renamed_driver"


def test_update_is_a_single_atomic_write_for_multiple_fields():
    """regression test: update() used to commit once per kwarg in a loop -
    now it's one dict, one update, one commit"""
    driver_id, _ = _make_driver()

    storage.update(
        "Driver", driver_id, username="multi_update_driver", first_name="Changed"
    )

    driver = storage.get("Driver", id=driver_id)
    assert driver.username == "multi_update_driver"
    assert driver.first_name == "Changed"


def test_update_rejects_a_duplicate_username():
    _, taken = _make_driver()
    driver_id, _ = _make_driver()

    result = storage.update("Driver", driver_id, username=taken["username"])

    assert result is False
    assert storage.get("Driver", id=driver_id).username != taken["username"]


def test_count_reflects_inserts_and_deletes():
    before = storage.count("Driver")
    driver_id, _ = _make_driver()

    assert storage.count("Driver") == before + 1

    storage.delete("Driver", f"id={driver_id}")

    assert storage.count("Driver") == before
