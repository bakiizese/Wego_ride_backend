#!/usr/bin/python
"""Chapa (https://chapa.co) implementation of PaymentGateway. A thin
client against Chapa's documented REST API rather than an unofficial
SDK. Chapa's flow is redirect-based: initialize returns a hosted
checkout URL, the payer completes payment there, and Chapa calls our
webhook + redirects the payer back to `return_url`."""

import hashlib
import hmac
import logging

import httpx

from config import settings
from payments.base import PaymentEvent, PaymentGateway, PaymentInitResult, PaymentStatus

logger = logging.getLogger(__name__)

CHAPA_BASE_URL = "https://api.chapa.co/v1"


class ChapaGateway(PaymentGateway):
    def __init__(self, secret_key=None, webhook_secret=None):
        self.secret_key = secret_key or settings.chapa_secret_key
        self.webhook_secret = webhook_secret or settings.chapa_webhook_secret

    def _headers(self):
        return {"Authorization": f"Bearer {self.secret_key}"}

    def initialize_payment(
        self, amount, currency, customer, tx_ref, callback_url, return_url
    ):
        payload = {
            "amount": str(amount),
            "currency": currency,
            "email": customer.get("email"),
            "first_name": customer.get("first_name"),
            "last_name": customer.get("last_name"),
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": return_url,
        }
        response = httpx.post(
            f"{CHAPA_BASE_URL}/transaction/initialize",
            json=payload,
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return PaymentInitResult(checkout_url=data["data"]["checkout_url"], tx_ref=tx_ref)

    def verify_payment(self, tx_ref):
        response = httpx.get(
            f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data") or {}
        status = "success" if data.get("status") == "success" else "failed"
        return PaymentStatus(
            tx_ref=tx_ref,
            status=status,
            amount=data.get("amount"),
            currency=data.get("currency"),
        )

    def verify_webhook_signature(self, payload_bytes, signature_header):
        if not self.webhook_secret or not signature_header:
            return False
        computed = hmac.new(
            self.webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature_header)

    def parse_webhook(self, payload):
        tx_ref = payload.get("tx_ref")
        status = payload.get("status", "unknown")
        return PaymentEvent(tx_ref=tx_ref, status=status)
