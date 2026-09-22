#!/usr/bin/python
"""Provider-agnostic payment gateway interface. `pay-ride` and the webhook
handler talk to this interface only - swapping providers later (Chapa ->
Stripe for a non-Ethiopian market, say) is a config change, not a rewrite."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentInitResult:
    checkout_url: str
    tx_ref: str


@dataclass
class PaymentStatus:
    tx_ref: str
    status: str  # "success" | "failed" | "pending"
    amount: Optional[float] = None
    currency: Optional[str] = None


@dataclass
class PaymentEvent:
    tx_ref: str
    status: str


class PaymentGateway(ABC):
    @abstractmethod
    def initialize_payment(
        self, amount, currency, customer, tx_ref, callback_url, return_url
    ) -> PaymentInitResult:
        """Start a hosted-checkout payment, returning the URL to redirect
        the payer's client to."""

    @abstractmethod
    def verify_payment(self, tx_ref) -> PaymentStatus:
        """Ask the provider directly for a transaction's current status -
        used as a defense-in-depth check, never trusting the webhook
        payload alone."""

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes, signature_header) -> bool:
        """Confirm an inbound webhook actually came from the provider."""

    @abstractmethod
    def parse_webhook(self, payload) -> PaymentEvent:
        """Extract the tx_ref/status this webhook is reporting."""
