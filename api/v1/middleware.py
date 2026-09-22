#!/usr/bin/python
from functools import wraps
from flask import jsonify, request, abort
import jwt
from models import storage
from models.availability import Availability
from datetime import datetime
import logging
from .utils.redis import Redis
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def _extract_bearer_token():
    """Pull the token out of `Authorization: Bearer <token>`, aborting with
    a clean 400 for a missing/malformed header instead of an IndexError."""
    header = request.headers.get("Authorization")
    if not header:
        logger.warning("Token missing")
        abort(400, description="Authorization header missing")
    parts = header.split(" ")
    if len(parts) != 2:
        logger.warning("malformed Authorization header")
        abort(400, description="Authorization header must be 'Bearer <token>'")
    return parts[1]


def touch_driver_availability(driver_id):
    """Update (or create) a driver's Availability row. Called explicitly
    from ride-related driver routes, not baked into auth as a side effect."""
    availability = storage.get("Availability", driver_id=driver_id)
    if availability:
        storage.update(
            "Availability", availability.id, last_active_time=datetime.utcnow()
        )
        return
    try:
        Availability(
            driver_id=driver_id,
            is_available=True,
            last_active_time=datetime.utcnow(),
        ).save()
    except Exception:
        logger.exception("failed to update driver availability")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()

        try:
            redis = Redis()
            if redis.check_jwt_blacklist(token):
                logger.warning("Token blacklisted")
                return jsonify({"error": "token blacklisted"}), 401

            data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user = storage.get(data["role"], id=data["sub"])
            if not user:
                logger.warning("user not found")
                abort(404)
            if user.deleted:
                logger.warning("access not allowed")
                abort(403)
            if user.blocked:
                if data["role"] == "Admin" or request.endpoint.split(".")[1] not in [
                    "get_profile",
                    "put_profile",
                    "ride_history",
                ]:
                    logger.warning("access not allowed")
                    abort(403)

            real_user = request.endpoint.split(".")[0].split("_")[0]
            real_user = (
                "Rider"
                if (real_user == "rider")
                else "Driver"
                if (real_user == "driver")
                else "Admin"
            )
            if real_user != data["role"]:
                logger.warning("Incorrect token")
                return jsonify({"error": "Incorrect token"}), 401

            request.user_id = data["sub"]
            request.role = data["role"]
            request.jwt_token = token
            request.jwt_exp = int(data["exp"] - datetime.utcnow().timestamp())
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, "role", None) != "Admin":
            logger.warning("admin access required")
            return jsonify({"Error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


def superadmin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, "role", None) != "Admin":
            logger.warning("only admin allowed")
            return jsonify({"Error": "only admin allowed"}), 403
        admin = storage.get("Admin", id=request.user_id)
        if not admin or admin.admin_level != "superadmin":
            logger.warning("only superadmin allowed")
            return jsonify({"Error": "only superadmin allowed"}), 403
        return f(*args, **kwargs)

    return decorated
