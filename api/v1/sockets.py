#!/usr/bin/python
"""Live ride-status over WebSocket. A `/rides` namespace, one room per
trip_id. Connecting requires a JWT in the Socket.IO `auth` payload
(reusing `decode_token` from middleware.py - see that module for why
`token_required` itself can't be reused directly here); joining a
specific trip's room additionally checks the connecting user is
actually the rider who booked it, the driver assigned to it, or an
admin. The existing polling GET endpoints are left in place as a
fallback / initial-state fetch - this is additive, not a replacement."""

import logging

import jwt
from flask import session
from flask_socketio import emit, join_room

from api.v1.extensions import socketio
from api.v1.middleware import (
    TokenBlacklisted,
    TokenUserDeleted,
    TokenUserMissing,
    decode_token,
)
from models import storage

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


@socketio.on("connect", namespace="/rides")
def handle_connect(auth):
    token = (auth or {}).get("token")
    if not token:
        logger.warning("socket connect rejected: missing token")
        raise ConnectionRefusedError("missing token")

    try:
        user, role, data = decode_token(token)
    except (TokenBlacklisted, TokenUserMissing, TokenUserDeleted, jwt.PyJWTError):
        logger.warning("socket connect rejected: invalid token")
        raise ConnectionRefusedError("unauthorized")

    if user.blocked and role != "Admin":
        logger.warning("socket connect rejected: blocked user")
        raise ConnectionRefusedError("unauthorized")

    session["user_id"] = data["sub"]
    session["role"] = role


@socketio.on("join", namespace="/rides")
def handle_join(payload):
    # emit() (unlike socketio.emit()) is context-aware inside a handler -
    # it targets the calling client on the namespace the handler is
    # registered for, so there's no namespace/recipient to get wrong here
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        emit("error", {"error": "not authenticated"})
        return

    trip_id = (payload or {}).get("trip_id")
    if not trip_id:
        emit("error", {"error": "trip_id required"})
        return

    trip = storage.get("Trip", id=trip_id)
    if not trip:
        emit("error", {"error": "trip not found"})
        return

    authorized = (
        role == "Admin"
        or (role == "Driver" and trip.driver_id == user_id)
        or (
            role == "Rider"
            and storage.get("TripRider", trip_id=trip_id, rider_id=user_id) is not None
        )
    )
    if not authorized:
        logger.warning("socket join rejected: not authorized for trip %s", trip_id)
        emit("error", {"error": "not authorized for this trip"})
        return

    join_room(trip_id)
    emit("joined", {"trip_id": trip_id})


def emit_ride_status_update(trip_id, event, **extra):
    """Called from the state-transition routes (start/end/cancel-ride,
    admin's set-ride, the Chapa webhook) to push a live update to
    whoever's joined that trip's room. Never lets a Socket.IO/Redis
    hiccup fail the HTTP request it's called from."""
    try:
        socketio.emit(
            "ride_status_update",
            {"trip_id": trip_id, "event": event, **extra},
            room=trip_id,
            namespace="/rides",
        )
    except Exception:
        logger.exception("failed to emit ride_status_update for trip %s", trip_id)
