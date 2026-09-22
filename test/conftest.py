#!/usr/bin/python
import os
import random
import string
import sys
import uuid
from pathlib import Path

# must happen before `config.settings` is instantiated anywhere (it's read
# once at import time) - disables the real rate limiter for the test app
# and would gate any other test-only behavior later
os.environ.setdefault("FLASK_ENV", "testing")

import pytest
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: E402
from config import settings  # noqa: E402
from models.base_model import Base  # noqa: E402
from api.v1.app import create_app  # noqa: E402


def _test_db_url():
    test_db_name = os.environ.get("TEST_DB_NAME", "wego_test_db")
    return "mysql+pymysql://{}:{}@{}:{}/{}".format(
        settings.db_user,
        settings.db_password,
        settings.db_host,
        settings.db_port,
        test_db_name,
    )


@pytest.fixture(scope="session", autouse=True)
def _redirect_storage_to_test_db():
    """Point the process-wide `storage` singleton at an isolated test
    database for the whole test session. Mutates the existing DBStorage
    instance in place, which works regardless of how many modules already
    hold a `from models import storage` reference to it."""
    models.storage.configure(_test_db_url())
    yield


@pytest.fixture(autouse=True)
def _clean_database():
    """Truncate every app table before each test, for isolation.

    DBStorage never closes/commits its session after read-only queries
    (a pre-existing quirk - a SELECT with no follow-up write leaves an
    open transaction sitting on the pooled connection), which otherwise
    blocks TRUNCATE with a metadata-lock wait forever. Roll it back first.
    """
    models.storage.rollback()
    engine = create_engine(_test_db_url())
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    engine.dispose()
    yield


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def _random_phone():
    return "251" + "".join(random.choices(string.digits, k=9))


@pytest.fixture
def make_user(client):
    """Factory fixture: registers + logs in a fresh Rider or Driver via the
    real HTTP endpoints, returning (user_id, token, registration_data)."""

    def _make(role="Rider", **overrides):
        path_role = role.lower()
        suffix = uuid.uuid4().hex[:8]
        data = {
            "username": f"test_{path_role}_{suffix}",
            "first_name": "Test",
            "last_name": role,
            "email": f"{suffix}@example.com",
            "phone_number": _random_phone(),
            "password_hash": "testpass123",
            "payment_method": "cash",
        }
        data.update(overrides)

        r = client.post(f"/api/v1/{path_role}/register", json=data)
        assert r.status_code == 201, r.get_json()
        user_id = r.get_json()["user"]

        r = client.post(
            f"/api/v1/{path_role}/login",
            json={"email": data["email"], "password_hash": data["password_hash"]},
        )
        assert r.status_code == 200, r.get_json()
        token = r.get_json()["user"]

        return user_id, token, data

    return _make


@pytest.fixture
def make_admin(client):
    """Factory fixture: creates an Admin directly via the Auth class
    (registration is superadmin-only over HTTP, a chicken-and-egg problem
    for tests) then logs in for real over HTTP to get a real token."""

    def _make(admin_level="moderator", **overrides):
        from auth.authentication import Auth

        suffix = uuid.uuid4().hex[:8]
        email = f"{suffix}@example.com"
        password = "testpass123"
        kwargs = dict(
            username=f"test_admin_{suffix}",
            first_name="Test",
            last_name="Admin",
            email=email,
            phone_number=_random_phone(),
            password_hash=password,
            admin_level=admin_level,
        )
        kwargs.update(overrides)

        admin_id, ok = Auth().register_user("Admin", **kwargs)
        assert ok is True, admin_id

        r = client.post(
            "/api/v1/admin/login", json={"email": email, "password_hash": password}
        )
        assert r.status_code == 200, r.get_json()
        return admin_id, r.get_json()["user"]

    return _make


@pytest.fixture
def auth_header():
    def _header(token):
        return {"Authorization": f"Bearer {token}"}

    return _header


@pytest.fixture(autouse=True)
def fake_payment_gateway(monkeypatch):
    """Test double for the Chapa gateway - no real HTTP calls anywhere in
    the suite. A test can steer the webhook's defense-in-depth
    verify_payment check via `fake_payment_gateway.outcomes[tx_ref]`."""

    class _FakeGateway:
        def __init__(self):
            self.outcomes = {}

        def initialize_payment(
            self, amount, currency, customer, tx_ref, callback_url, return_url
        ):
            from payments.base import PaymentInitResult

            self.outcomes.setdefault(tx_ref, "success")
            return PaymentInitResult(
                checkout_url=f"https://checkout.chapa.co/{tx_ref}", tx_ref=tx_ref
            )

        def verify_payment(self, tx_ref):
            from payments.base import PaymentStatus

            return PaymentStatus(
                tx_ref=tx_ref, status=self.outcomes.get(tx_ref, "success")
            )

        def verify_webhook_signature(self, payload_bytes, signature_header):
            return signature_header == "test-signature"

        def parse_webhook(self, payload):
            from payments.base import PaymentEvent

            return PaymentEvent(
                tx_ref=payload.get("tx_ref"), status=payload.get("status", "success")
            )

    gateway = _FakeGateway()
    monkeypatch.setattr("api.v1.views.rider_views.get_gateway", lambda: gateway)
    monkeypatch.setattr("api.v1.views.webhook_views.get_gateway", lambda: gateway)
    return gateway


@pytest.fixture
def confirm_chapa_payment(client):
    """Simulate Chapa calling our webhook to confirm (or fail) a payment
    initiated through /rider/pay-ride."""

    def _confirm(tx_ref, status="success"):
        return client.post(
            "/api/v1/webhooks/chapa",
            json={"tx_ref": tx_ref, "status": status},
            headers={"Chapa-Signature": "test-signature"},
        )

    return _confirm
