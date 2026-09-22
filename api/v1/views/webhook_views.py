#!/usr/bin/python
"""Chapa webhook receiver - registered without @token_required, since
Chapa's own servers call this, not an authenticated app client."""

import logging

from flask import abort, jsonify, request

from api.v1.views import webhook_bp
from models import storage
from payments.factory import get_gateway

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


@webhook_bp.route("/chapa", methods=["POST"], strict_slashes=False)
def chapa_webhook():
    """Verifies the webhook signature, then double-checks the transaction
    status directly with Chapa's API before touching anything - per
    Chapa's own docs, the webhook payload alone is never trusted."""
    raw_body = request.get_data()
    signature = request.headers.get("Chapa-Signature")

    gateway = get_gateway()
    if not gateway.verify_webhook_signature(raw_body, signature):
        logger.warning("chapa webhook: invalid signature")
        abort(401)

    payload = request.get_json(silent=True)
    if payload is None:
        abort(400)

    event = gateway.parse_webhook(payload)
    if not event.tx_ref:
        logger.warning("chapa webhook: missing tx_ref")
        abort(400)

    payment = storage.get("Payment", provider_tx_ref=event.tx_ref)
    if not payment:
        logger.warning("chapa webhook: unknown tx_ref %s", event.tx_ref)
        abort(404)

    if payment.payment_status == "paid":
        # webhook deliveries can repeat - already-processed is a no-op,
        # not an error
        return jsonify({"status": "already processed"}), 200

    verified = gateway.verify_payment(event.tx_ref)

    if verified.status != "success":
        try:
            storage.update("Payment", payment.id, payment_status="failed")
        except Exception:
            logger.exception("failed to record failed payment")
            abort(500)
        return jsonify({"status": "payment not successful"}), 200

    totalpayment = storage.get("TotalPayment", trip_id=payment.trip_id)
    if not totalpayment:
        logger.warning(
            "chapa webhook: totalpayment not found for trip %s", payment.trip_id
        )
        abort(404)

    try:
        storage.update("Payment", payment.id, payment_status="paid")
        storage.update(
            "TotalPayment",
            totalpayment.id,
            number_of_riders_paid=totalpayment.number_of_riders_paid + 1,
            number_of_riders_not_paid=totalpayment.number_of_riders_not_paid - 1,
            total_revenue=totalpayment.total_revenue + payment.amount,
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)

    try:
        storage.get("TotalPayment", id=totalpayment.id).validate_rider_counts()
    except ValueError:
        logger.exception(
            "total_payment rider counts are inconsistent for trip %s", payment.trip_id
        )

    return jsonify({"status": "payment confirmed"}), 200
