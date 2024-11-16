#!/usr/bin/python
from functools import wraps
from flask import jsonify, request, abort
import jwt
from models import storage
from datetime import datetime
import logging

SECRET_KEY = "wego_rider_service_secret_key"

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            logger.warning("Token missing")
            return abort(400)

        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if data["role"] == "Admin":
                user = storage.get(data["role"], id=data["sub"])
                if user:
                    if user.blocked or user.deleted:
                        logger.warning("access not allowed")
                        abort(403)

            if data["role"] in ["Rider", "Driver"]:
                user = storage.get(data["role"], id=data["sub"])
                if not user:
                    logger.warning("user not found")
                    abort(404)
                if user.deleted:
                    logger.warning("access not allowed")
                    abort(403)
                if user.blocked:
                    if request.endpoint.split(".")[1] not in [
                        "get_profile",
                        "put_profile",
                        "ride_history",
                    ]:
                        logger.warning("access not allowed")
                        abort(403)
            real_user = request.endpoint.split(".")[0].split("_")[0]
            correct_user = storage.get(data["role"], id=data["sub"])
            if correct_user:
                real_user = (
                    "Rider"
                    if (real_user == "rider")
                    else "Driver" if (real_user == "driver") else "Admin"
                )
                if real_user != data["role"]:
                    logger.warning("Incorrect token")
                    return jsonify({"error": "Incorrect token"}), 401
            request.user_id = data["sub"]
            request.role = data["role"]
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return jsonify({"error": "Invalid token"}), 401
        # set availability if no data found for user
        if data["role"] == "Driver":
            availability = storage.get("Availability", driver_id=data["sub"]).id
            storage.update(
                "Availability", availability, last_active_time=datetime.utcnow()
            )

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, "role", None) != "Admin":
            g = getattr(request, "role", None)
            logger.warning("admin access required")
            return jsonify({"Error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            logger.warning("token is missing")
            return jsonify({"Error": "Token is missing"}), 400

        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if data["role"] == "Admin":
                user_id = data["sub"]
                user = storage.get("Admin", id=user_id)
                if not user.admin_level == "superadmin":
                    logger.warning("only superadmin allowed")
                    return jsonify({"Error": "only superadmin allowed"}), 403
            else:
                logger.warning("only admin allowed")
                return jsonify({"Error": "only admin allowed"}), 403

        except jwt.ExpiredSignatureError:
            logger.warning("token has expired")
            return jsonify({"Error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            logger.warning("invalid token")
            return jsonify({"Error": "Invalid token"}), 401
        return f(*args, **kwargs)

    return decorated
