#!/usr/bin/python
"""Returns the configured PaymentGateway instance - swapping providers
is a `PAYMENT_PROVIDER` env var change, not a code change."""

from config import settings
from payments.chapa import ChapaGateway

_GATEWAYS = {
    "chapa": ChapaGateway,
}


def get_gateway():
    gateway_cls = _GATEWAYS.get(settings.payment_provider)
    if gateway_cls is None:
        raise ValueError(f"unsupported payment provider: {settings.payment_provider!r}")
    return gateway_cls()
