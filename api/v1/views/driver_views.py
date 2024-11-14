from api.v1.views import driver_bp
from flask import jsonify, request, abort, send_file
from auth import authentication
from auth.authentication import _hash_password, clean
from api.v1.middleware import token_required
from models import storage
from models.total_payment import TotalPayment
from models.image import Image
from datetime import datetime, timedelta
import logging
import os
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

Auth = authentication.Auth()

driver_key = [
    "username",
    "first_name",
    "last_name",
    "email",
    "phone_number",
    "password_hash",
    "payment_method",
]
cls = "Driver"


# Registration And Authentication
@driver_bp.route("/register", methods=["POST"], strict_slashes=False)
def register():
    """register a new driver by provided informations"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    for k in driver_key:
        if k not in user_data.keys():
            logger.warning(f"{k} missing")
            return jsonify({"error": f"{k} missing"}), 400
    try:
        int(user_data["phone_number"])
    except:
        logger.warning("phone_number must be integer")
        return jsonify({"error": "phone_number must be integer"}), 400
    try:
        user = Auth.register_user(cls, **user_data)
        message, status = user
    except:
        logger.exception("An internal error")
        abort(500)

    if status:
        return jsonify({"user": message}), 201
    logger.warning(message)
    return jsonify({"error": message}), 400


@driver_bp.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """login as driver by provided credentials"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    find_with = ""
    if "email" in user_data:
        find_with = "email"
    elif "phone_number" in user_data:
        find_with = "phone_number"
    else:
        logger.warning("email or phone_number missing")
        return jsonify({"error": "email or phone_number missing"})

    if "password_hash" not in user_data:
        logger.warning("password_hash missing")
        return jsonify({"error": "password_hash missing"}), 400

    try:
        user = Auth.verify_login(
            cls, find_with, user_data[find_with], user_data["password_hash"]
        )
        message, status = user
    except:
        logger.exception("An internal error")
        abort(500)

    if status:
        return jsonify({"user": status}), 200
    logger.warning(message)
    return jsonify({"error": message}), 400


@driver_bp.route("/logout", methods=["POST"], strict_slashes=False)
@token_required
def logout():
    """logout and black-list jwt token"""
    return jsonify({"User": "Logged out"}), 200


# Profile Management
@driver_bp.route("/reset-token", methods=["POST"], strict_slashes=False)
def get_reset_token():
    """generate a reset-token by provided informations, to be sent to user email or phone number"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    user = ""
    find_with = ""
    if "email" in user_data:
        user = storage.get(cls, email=user_data["email"])
        find_with = "email"
    elif "phone_number" in user_data:
        user = storage.get(cls, phone_number=user_data["phone_number"])
        find_with = "phone_number"
    else:
        logger.warning("email or phone_number missing")
        return jsonify({"error": "email or phone_number missing"}), 400
    if user:
        reset_token = Auth.create_reset_token(cls, find_with, user_data[find_with])
        return jsonify({"reset_token": reset_token}), 201
    else:
        logger.warning("user not found")
        abort(404)


@driver_bp.route("/forget-password", methods=["POST"], strict_slashes=False)
def forget_password():
    """update password by provided informations i.e. reset-token, e.t.c."""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    if "password_hash" not in user_data:
        logger.warning("password missing")
        return jsonify({"error": "password not provided"}), 400
    if "reset_token" in user_data:
        try:
            update_password = Auth.update_password(
                cls, user_data["reset_token"], user_data["password_hash"]
            )
        except:
            logger.exception("An internal error")
            abort(500)

        if update_password:
            return jsonify({"update": "Successful"}), 200
        else:
            logger.warning("incorrect reset-token")
            return jsonify({"update": "incorrect reset-token"}), 400
    else:
        logger.warning("rest token missing")
        return jsonify({"error": "reset token not provided"}), 400


@driver_bp.route("/profile/image", methods=["GET"], strict_slashes=False)
@token_required
def get_image():
    """returns a profile picture saved for this user"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)
    image = storage.get("Image", user_id=user_id)
    if image:
        return send_file(image.path, mimetype="image/jpeg"), 200
    logger.warning("image not found")
    return jsonify({"error": "image not found"})


@driver_bp.route("/profile/remove-image", methods=["DELETE"], strict_slashes=False)
@token_required
def remove_image():
    """remove image of this user if exist"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)
    image = storage.get("Image", user_id=user_id)
    if not image:
        logger.warning("image not found")
        return jsonify({"error": "image not found"}), 404
    try:
        storage.delete("Image", image.id)
    except:
        logger.exception("an internal error")
        abort(500)
    if os.path.exists(image.path):
        try:
            os.remove(image.path)
        except:
            logger.exception("an internal error")
            abort(500)
    else:
        logger.warning("path doesn't exist")
        return jsonify({"error": "path doesn't exist"}), 404
    return jsonify({"image": "removed successfuly"}), 200


@driver_bp.route("/profile/image", methods=["POST"], strict_slashes=False)
@token_required
def upload_image():
    """uploads a profile picture for this user"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)
    try:
        image = request.files["image"]
    except Exception as e:
        logger.warning(e)
        abort(415)

    if image.filename == "":
        logger.warning("no file selected")
        return jsonify({"error": "no file selected"}), 400

    new_name = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
    file_path = os.path.join("./image_uploads", new_name)
    full_path = os.path.abspath(file_path)

    user_image = storage.get("Image", user_id=user_id)
    if user_image:
        if os.path.exists(user_image.path):
            try:
                os.remove(user_image.path)
            except:
                logger.exception("an internal error")
                abort(500)
        try:
            storage.delete("Image", user_image.id)
        except:
            logger.exception("an internal error")
            abort(500)

    image.save(file_path)

    kwargs = {"path": full_path, "user_id": user_id, "user_type": "Driver"}
    try:
        new_image = Image(**kwargs)
        new_image.save()
    except:
        logger.exception("an internal error")
        abort(500)

    return jsonify({"image": "uploaded"}), 200


@driver_bp.route("/profile", methods=["GET"], strict_slashes=False)
@token_required
def get_profile():
    """get user profile"""
    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)
    user = storage.get(cls, id=user_id)
    image = storage.get("Image", user_id=user_id)
    if not user:
        logger.warning("user not found")
        return jsonify({"error": "user not found"}), 404
    user = clean(user.to_dict())
    if image:
        user["image"] = image.path
    return jsonify({"user": user}), 200


@driver_bp.route("/profile", methods=["PUT"], strict_slashes=False)
@token_required
def put_profile():
    """update user profile by provided informations including password update"""
    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    unmutables_by_user = ["email", "phone_number", "reset_token"]
    user = storage.get_in_dict(cls, id=user_id)
    updates = {}
    if user:
        for k in user_data.keys():
            if k not in unmutables_by_user:
                updates[k] = user_data[k]

        if "password_hash" in updates:
            if "old_password" in updates:
                user_password = storage.get(cls, id=user_id)
                if not user_password:
                    logger.warning("user not found")
                    abort(404)
                check_password = Auth.verify_password(
                    updates["old_password"], user_password
                )
                if check_password:
                    updates["password_hash"] = _hash_password(updates["password_hash"])
                    del updates["old_password"]
                else:
                    logger.warning("password incorrect")
                    return jsonify({"error": "password incorrect"}), 400
            else:
                logger.warning("old password missing")
                return jsonify({"error": "old_password missing"}), 400
        else:
            logger.warning("password_hash missing")
            return jsonify({"error": "password_hash missing"}), 400
        try:
            storage.update(cls, id=user_id, **updates)
        except:
            logger.exception("An internal error")
            return jsonify({"error": "Update Failed"}), 500
    else:
        logger.warning("user not found")
        abort(404)
    return jsonify({"user": "updated Successfuly"}), 200


# Ride Management
@driver_bp.route("/availability", methods=["GET"], strict_slashes=False)
@token_required
def availability():
    """get drivers availablility"""
    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    availability = storage.get("Availability", driver_id=user_id)

    if availability:
        availability = clean(availability.to_dict())
        return jsonify({"availability": availability}), 200

    logger.warning("availability not found")
    return jsonify({"error": "availability not found"}), 404


@driver_bp.route("/ride-plans", methods=["GET"], strict_slashes=False)
@token_required
def ride_pans():
    """get all ride-plans assigned to this driver"""
    try:
        driver_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)
    driver_trips = []

    trips = storage.get_objs("Trip", driver_id=driver_id, is_available=True)

    if not trips:
        logger.warning("trips not found")
        abort(404)

    sorted_trips = sorted(trips, key=lambda trip: trip.updated_at)

    for sorted_trip in sorted_trips:
        driver_trips.append(clean(sorted_trip.to_dict()))

    return jsonify({"rides": driver_trips}), 200


@driver_bp.route("/current-ride/<trip_id>", methods=["GET"], strict_slashes=False)
@token_required
def current_ride(trip_id):
    """get detailed current-ride information by provided trip_id"""
    try:
        request.user_id
    except:
        logger.exception("An internal error")
        abort(500)
    trip = storage.get("Trip", id=trip_id)

    if not trip:
        logger.warning("trip not found")
        abort(404)
    trip = clean(trip.to_dict())

    if trip["driver_id"] != request.user_id:
        logger.warning("driver not assigned to this particular trip")
        return jsonify({"error": "driver not assigned to this particular trip"}), 400

    tripriders = storage.get_objs("TripRider", trip_id=trip["id"], is_past=False)

    count = 0
    for _ in tripriders:
        count += 1

    try:
        trip["pickup_location_id"] = clean(
            storage.get("Location", id=trip["pickup_location_id"]).to_dict()
        )
        trip["dropoff_location_id"] = clean(
            storage.get("Location", id=trip["dropoff_location_id"]).to_dict()
        )
    except:
        logger.exception("An internal error")
        abort(500)

    del trip["driver_id"]
    trip["number_of_passengers"] = count

    return jsonify({"ride": trip}), 200


@driver_bp.route("/ride-requests", methods=["GET"], strict_slashes=False)
@token_required
def ride_requests():
    """get all detailed ride-requests to all rides assigned to this driver"""
    try:
        driver_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    riders = {}
    trips = storage.get_objs("Trip", driver_id=driver_id, is_available=True)
    trip_dict = {}

    if not trips:
        logger.warning("no requests found")
        return jsonify({"rider": "no requests found"}), 404

    for trip in trips:
        tripriders = storage.get_objs("TripRider", trip_id=trip.id, is_past=False)
        if not tripriders:
            logger.warning("tripriders not found")
            abort(404)
        for triprider in tripriders:
            try:
                riders["Rider." + triprider.rider.id] = clean(triprider.rider.to_dict())
                trip_dict["Trip." + trip.id] = riders
            except:
                logger.exception("An internal error")
                abort(500)
        riders = {}

    return jsonify({"riders": trip_dict}), 200


@driver_bp.route("/start-ride", methods=["POST"], strict_slashes=False)
@token_required
def start_ride():
    """mark a start-ride by updating trip table, by provided informations"""
    try:
        trip_id = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    if "trip_id" not in trip_id:
        logger.warning("trip_id missing")
        return jsonify({"error": "trip_id missing"}), 400
    trip_id = trip_id["trip_id"]
    if not storage.get("Trip", id=trip_id).is_available:
        logger.warning("trip not available")
        return jsonify({"error": "trip not available"}), 400
    try:
        storage.update(
            "Trip",
            trip_id,
            status="started",
            is_available=False,
            pickup_time=datetime.now(),
        )
    except:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"ride": "started"}), 200


@driver_bp.route("/end-ride", methods=["POST"], strict_slashes=False)
@token_required
def end_ride():
    """mark an end-ride by updating trip, triprider, totalpayment tables, by provided informations"""
    try:
        trip_id = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    if "trip_id" not in trip_id:
        logger.warning("trip_id missing")
        return jsonify({"error": "trip_id missing"}), 400
    trip_id = trip_id["trip_id"]

    tripriders = storage.get_objs("TripRider", trip_id=trip_id, is_past=False)
    if not tripriders:
        logger.warning("tripriders not found")
        abort(404)
    if tripriders.count() == 0:
        logger.warning("no rides booked")
        return jsonify({"ride": "no riders booked"}), 200
    if storage.get("Trip", id=trip_id).status != "started":
        logger.warning("unable to end ride, ride never started")
        return jsonify({"ride": "unable to end ride, ride never started"}), 200
    riders_not_paid = []
    riders_paid = []
    for triprider in tripriders:
        try:
            if storage.get("Payment", trip_id=trip_id, rider_id=triprider.rider.id):
                riders_paid.append(triprider.rider.id)
            else:
                riders_not_paid.append(triprider.rider.id)
                continue
            storage.update(
                "TripRider",
                triprider.id,
                status="completed",
                status_by="completed-Paid-Ride",
                is_past=True,
            )
        except:
            logger.exception("An internal error")
            abort(500)
    if len(riders_not_paid) != 0:
        logger.warning("unfinished riders payment")
        return jsonify({"unpaid": riders_not_paid}), 409
    totalpayment = storage.get(
        "TotalPayment", trip_id=trip_id, driver_id=request.user_id
    )
    driver_earning = totalpayment.total_revenue * (totalpayment.driver_commission / 100)
    try:
        storage.update("Trip", trip_id, status="completed", is_available=False)
        storage.update(
            "TotalPayment",
            totalpayment.id,
            transaction_over=True,
            driver_earning=driver_earning,
            transaction_time=datetime.now(),
            status="paid",
        )
    except:
        logger.exception("An internal error")
        abort(500)
    return jsonify({"ride": "completed"}), 200


@driver_bp.route("/cancel-ride", methods=["POST"], strict_slashes=False)
@token_required
def cancel_ride():
    """cancel a ride by updating triprider, trip tables, by provided informations"""
    try:
        trip_id = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    if "trip_id" not in trip_id:
        logger.warning("trip_id missing")
        return jsonify({"error": "trip_id missing"}), 400
    trip_id = trip_id["trip_id"]

    tripriders = storage.get_objs("TripRider", trip_id=trip_id, is_past=False)
    trips = [trips for trips in tripriders]

    if not trips:
        logger.warning("trips not found")
        abort(404)

    if not storage.get("Trip", id=trip_id):
        logger.warning("trip not found")
        abort(404)
    for triprider in tripriders:
        try:
            storage.update(
                "TripRider",
                triprider.id,
                status="canceled",
                status_by="Driver",
                is_past=True,
            )
        except:
            logger.exception("An internal error")
            abort(500)
    try:
        storage.update("Trip", trip_id, status="canceled", is_available=False)
    except:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"ride": "canceled"}), 200


# Ride History And Earning
@driver_bp.route("/ride-history", methods=["GET"], strict_slashes=False)
@token_required
def ride_history():
    """get all ride-histories of this driver"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)
    trips = storage.get_objs("Trip", driver_id=user_id, is_available=False)

    trips_dict = {}

    for trip in trips:
        if trip:
            trips_dict["Trip." + trip.id] = clean(trip.to_dict())

    return jsonify({"rides": trips_dict}), 200


@driver_bp.route("/earnings/<date>", methods=["GET"], strict_slashes=False)
@driver_bp.route(
    "/earnings", defaults={"date": None}, methods=["GET"], strict_slashes=False
)
@token_required
def earnings(date):
    """show driver's earning daily, monthly, annually or by date if provided"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)
    payments = [
        payment for payment in storage.get_objs("TotalPayment", driver_id=user_id)
    ]
    total_earning = sum([payment.driver_earning for payment in payments])
    now = datetime.now()
    try:
        if date:
            date = datetime.strptime(date, "%d-%m-%Y")
            (
                day_earning,
                month_earning,
                year_earning,
            ) = (0,) * 3
            for payment in payments:
                if payment.transaction_time.date() == date.date():
                    day_earning += payment.driver_earning
                if (
                    payment.transaction_time.year == date.year
                    and payment.transaction_time.month == date.month
                ):
                    month_earning += payment.driver_earning
                if payment.transaction_time.year == date.year:
                    year_earning += payment.driver_earning

            earnings = {
                f"day_{date.day}_earning": day_earning,
                f"month_{date.month}_earning": month_earning,
                f"year_{date.year}_earning": year_earning,
            }
            return jsonify({"earning": earnings}), 200
        (
            today_earning,
            yesterday_earning,
            this_month_earning,
            last_month_earning,
            this_year_earning,
        ) = (0,) * 5

        for payment in payments:
            if payment.transaction_time.date() == now.date():
                today_earning += payment.driver_earning
            if payment.transaction_time.date() == (now - timedelta(days=1)).date():
                yesterday_earning += payment.driver_earning
            if (
                payment.transaction_time.month == now.month
                and payment.transaction_time.year == now.year
            ):
                this_month_earning += payment.driver_earning
            if (
                payment.transaction_time.month == (now.month - 1)
                and payment.transaction_time.year == now.year
            ):
                last_month_earning += payment.driver_earning
            if payment.transaction_time.year == now.year:
                this_year_earning += payment.driver_earning
    except:
        logger.exception("An internal error")
        abort(500)
    earnings = {
        "total_earning": total_earning,
        "today_earning": today_earning,
        "yesterday_earning": yesterday_earning,
        f"this_month_earning": this_month_earning,
        f"last_month_earning": last_month_earning,
        f"this_year_earning": this_year_earning,
    }
    return jsonify({"earning": earnings}), 200
