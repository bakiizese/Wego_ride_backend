#!/usr/bin/python
import io
import sys
import uuid

import pytest

import console
from models import storage

WegoCommand = console.WegoCommand()


@pytest.mark.parametrize(
    "args,expected",
    [
        (['email="bereket@gmail.com"'], {"email": "bereket@gmail.com"}),
        (["email"], {}),
        (["email=1234"], {"email": 1234}),
        (['email="1234"'], {"email": "1234"}),
        (['email="12.34"'], {"email": "12.34"}),
        # unquoted, non-numeric values fall through unconverted rather
        # than being skipped - this matches the parser's actual behavior
        (["email=baki"], {"email": "baki"}),
        (["email='baki'"], {"email": "'baki'"}),
        (["email="], {"email": ""}),
    ],
)
def test_key_value_parser(args, expected):
    """parses cli-style key=value args into a dict"""
    assert WegoCommand._key_value_parser(args) == expected


def _capture(fn, *args):
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        result = fn(*args)
    finally:
        sys.stdout = sys.__stdout__
    return result, captured_output.getvalue().strip()


@pytest.mark.parametrize(
    "arg,expected_print",
    [
        ("", "** class name missing **"),
        ("Drive", "** class doesn't exist **"),
        ("Driver", "username: is missing"),
        ('Driver username="bekii"', "first_name: is missing"),
        (
            'Driver username="bekii" first_name="bereket"',
            "last_name: is missing",
        ),
    ],
)
def test_do_create_rejects_missing_or_invalid_input(arg, expected_print):
    result, printed = _capture(WegoCommand.do_create, arg)
    assert result is False
    assert printed == expected_print


def test_do_create_succeeds_with_complete_valid_input():
    suffix = uuid.uuid4().hex[:8]
    arg = (
        f'Driver username="bekii{suffix}" first_name="bereket" last_name="zesess" '
        f'email="bereket{suffix}@example.com" phone_number={1234560 + int(suffix[:2], 16) % 999} '
        f'password_hash="passcode" payment_method="cash"'
    )
    result, printed = _capture(WegoCommand.do_create, arg)
    # do_create prints the new id and returns None on success (doesn't
    # return the id - a pre-existing quirk of the console, not touched here)
    assert result is None
    assert printed  # the printed instance id
    driver = storage.get("Driver", id=printed)
    assert driver is not None


def test_do_create_rejects_duplicate_username():
    suffix = uuid.uuid4().hex[:8]
    base_arg = (
        f'Driver username="dup{suffix}" first_name="bereket" last_name="zesess" '
        f'email="dup{suffix}@example.com" phone_number={1234561} password_hash="passcode" '
        f'payment_method="cash"'
    )
    _capture(WegoCommand.do_create, base_arg)

    dup_arg = (
        f'Driver username="dup{suffix}" first_name="bereket" last_name="zesess" '
        f'email="other{suffix}@example.com" phone_number={1234562} password_hash="passcode" '
        f'payment_method="cash"'
    )
    result, printed = _capture(WegoCommand.do_create, dup_arg)

    assert result is False
    assert printed == "** username already exists **"


@pytest.mark.parametrize(
    "arg,expected_print,expected_return",
    [
        ("", "** class name missing **", False),
        ("Dr", "** class doesn't exist **", False),
        ("Driver id=not-a-real-id", "", None),
    ],
)
def test_do_show(arg, expected_print, expected_return):
    result, printed = _capture(WegoCommand.do_show, arg)
    assert printed == expected_print
    assert result == expected_return


@pytest.mark.parametrize(
    "arg,expected_print,expected_return",
    [
        ("", "** class name missing **", False),
        ("Drivr", "** class doesn't exist **", False),
        ("Driver", "** instance id missing **", False),
        ("Driver adsasd", '** "id" property missing **', False),
        ("Driver id=asdasd", "** update argumnets missing **", False),
        (
            'Driver i=asdsads used="jack"',
            '** "id" property missing **',
            False,
        ),
        (
            'Driver id=asdsads username="jack"',
            "** instance id doesn't exist **",
            False,
        ),
    ],
)
def test_do_update_rejects_invalid_input(arg, expected_print, expected_return):
    result, printed = _capture(WegoCommand.do_update, arg)
    assert printed == expected_print
    assert result == expected_return


def test_console_end_to_end_create_update_destroy():
    suffix = uuid.uuid4().hex[:8]
    arg = (
        f'Driver username="bak{suffix}" first_name="bere" last_name="zese" '
        f'email="bere{suffix}@example.com" phone_number={1234563} password_hash="password" '
        f'payment_method="cash"'
    )
    _, driver_id = _capture(WegoCommand.do_create, arg)

    user_check = storage.get("Driver", email=f"bere{suffix}@example.com")
    assert user_check is not None
    assert user_check.id == driver_id
    assert user_check.first_name != "baki"

    WegoCommand.do_update(f'Driver id={user_check.id} first_name="baki"')
    updated = storage.get("Driver", id=user_check.id)
    assert updated.first_name == "baki"

    WegoCommand.do_destroy(f"Driver id={user_check.id}")
    assert storage.get("Driver", email=f"bere{suffix}@example.com") is None
