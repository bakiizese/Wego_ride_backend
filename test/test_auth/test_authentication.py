#!/usr/bin/python
import uuid

from auth.authentication import Auth, _hash_password
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


def test_register_user_succeeds_and_hashes_the_password():
    kwargs = _unique_driver_kwargs()
    user_id, ok = auth.register_user("Driver", **kwargs)
    assert ok is True
    driver = storage.get("Driver", id=user_id)
    assert driver is not None
    assert driver.password_hash != kwargs["password_hash"]


def test_register_user_rejects_duplicate_username():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)
    message, ok = auth.register_user(
        "Driver", **_unique_driver_kwargs(username=kwargs["username"])
    )
    assert ok is False
    assert "username already exists" in message


def test_register_user_rejects_duplicate_email():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)
    message, ok = auth.register_user(
        "Driver", **_unique_driver_kwargs(email=kwargs["email"])
    )
    assert ok is False
    assert "email already exists" in message


def test_register_user_rejects_duplicate_phone_number():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)
    message, ok = auth.register_user(
        "Driver", **_unique_driver_kwargs(phone_number=kwargs["phone_number"])
    )
    assert ok is False
    assert "phone number already exists" in message


def test_update_password_changes_the_stored_hash():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)
    reset_token = auth.create_reset_token("Driver", "email", kwargs["email"])
    pre = storage.get("Driver", email=kwargs["email"]).password_hash

    updated = auth.update_password("Driver", reset_token, "a_new_password")

    assert updated is True
    post = storage.get("Driver", email=kwargs["email"]).password_hash
    assert pre != post


def test_verify_login_succeeds_with_correct_credentials():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)

    message, token = auth.verify_login(
        "Driver", "email", kwargs["email"], kwargs["password_hash"]
    )

    assert token is not False
    assert isinstance(token, (str, bytes))


def test_verify_login_fails_with_wrong_password():
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)

    message, token = auth.verify_login(
        "Driver", "email", kwargs["email"], "wrong_password"
    )

    assert token is False


def test_verify_login_does_not_leak_whether_the_account_exists():
    """regression test: verify_login must answer identically whether the
    email is unregistered or the password was wrong (user-enumeration fix)"""
    kwargs = _unique_driver_kwargs()
    auth.register_user("Driver", **kwargs)

    _, unknown_email_token = auth.verify_login(
        "Driver", "email", "nobody-registered@example.com", "whatever"
    )
    unknown_email_message, _ = auth.verify_login(
        "Driver", "email", "nobody-registered@example.com", "whatever"
    )
    wrong_password_message, wrong_password_token = auth.verify_login(
        "Driver", "email", kwargs["email"], "wrong_password"
    )

    assert unknown_email_token is False
    assert wrong_password_token is False
    assert unknown_email_message == wrong_password_message


def test_hash_password_returns_str_not_bytes():
    """regression test: bcrypt.hashpw returns bytes - _hash_password must
    decode it, since it's stored in a String DB column and later compared
    via verify_password's saved_password.password_hash.encode()"""
    hashed = _hash_password("some_password")
    assert isinstance(hashed, str)
