#!/usr/bin/python
from api.v1.views import rider_bp
from flask import jsonify, request, abort, send_file
from auth import authentication
from auth.authentication import _hash_password, clean
from models import storage
from api.v1.middleware import token_required
from models.trip import Trip
from models.notification import Notification
from models.trip_rider import TripRider
from models.payment import Payment
from models.image import Image
from api.v1.utils.pagination import paginate, get_sort_column
from api.v1.utils.validation import (
    parse_json_body,
    validate_body,
    UserRegisterSchema,
    LoginSchema,
    ProfileUpdateSchema,
    BookRideSchema,
    NotificationSchema,
    RatingSchema,
    PayRideSchema,
)
from api.v1.utils.mail import send_reset_token_email
from api.v1.utils.ratings import submit_rating
from api.v1.extensions import limiter
from models.rating import Rating
from payments.factory import get_gateway
from datetime import datetime
from ..utils.redis import Redis
import logging
import uuid
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

Auth = authentication.Auth()

cls = "Rider"


# Registation And Authentication
@rider_bp.route("/register", methods=["POST"], strict_slashes=False)
@limiter.limit("5 per minute")
@validate_body(UserRegisterSchema)
def register():
    """register a new rider by provided informations"""
    user_data = request.validated.model_dump()

    try:
        user = Auth.register_user(cls, **user_data)
        message, status = user
    except Exception:
        logger.exception("An internal error")
        abort(500)

    if status:
        return jsonify({"user": message}), 201
    logger.warning(message)
    return jsonify({"error": message}), 400


@rider_bp.route("/login", methods=["POST"], strict_slashes=False)
@limiter.limit("5 per minute")
@validate_body(LoginSchema)
def login():
    """login as rider by provided credentails"""
    user_data = request.validated

    if user_data.email:
        find_with, find = "email", user_data.email
    elif user_data.phone_number:
        find_with, find = "phone_number", user_data.phone_number
    else:
        logger.warning("email or phone_number missing")
        return jsonify({"error": "email or phone_number missing"}), 400

    try:
        user = Auth.verify_login(cls, find_with, find, user_data.password_hash)
        message, status = user
    except Exception:
        logger.exception("An internal error")
        abort(500)

    if status:
        return jsonify({"user": status}), 200
    logger.warning(message)
    return jsonify({"error": message}), 400


@rider_bp.route("/logout", methods=["POST"], strict_slashes=False)
@token_required
def logout():
    """logout and black-list jwt token"""
    try:
        jwt_token = request.jwt_token
        jwt_exp = request.jwt_exp
    except Exception:
        logger.exception("an internal error")
        abort(500)
    redis = Redis()
    redis.jwt_blacklist(jwt_token, jwt_exp)

    return jsonify({"User": "Logged out"}), 200


# Profile Management
@rider_bp.route("/reset-token", methods=["POST"], strict_slashes=False)
@limiter.limit("5 per minute")
def get_reset_token():
    """generate a reset-token and email it to the account's registered
    address - never returned in the response, and always answers the
    same way whether or not the account exists (avoids enumeration)"""
    user_data = parse_json_body()
    user = None
    find_with = None
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
        send_reset_token_email(user.email, reset_token)
    else:
        logger.warning("user not found for reset-token request")

    return (
        jsonify({"message": "if that account exists, a reset code has been sent"}),
        200,
    )


@rider_bp.route("/forget-password", methods=["POST"], strict_slashes=False)
@limiter.limit("5 per minute")
def forget_password():
    """update password by provided informations i.e. reset-token, e.t.c."""
    user_data = parse_json_body()

    if "password_hash" not in user_data:
        logger.warning("password missing")
        return jsonify({"error": "password not provided"}), 400
    if "reset_token" in user_data:
        try:
            update_password = Auth.update_password(
                cls, user_data["reset_token"], user_data["password_hash"]
            )
        except Exception:
            logger.exception("An internal error")
            abort(500)
        if update_password:
            return jsonify({"update": "Successful"}), 200
        else:
            logger.warning("incorrect reset-token")
            return jsonify({"error": "incorrect token"}), 400
    else:
        logger.warning("reset token missing")
        return jsonify({"error": "reset token not provided"}), 400


@rider_bp.route("/profile/image", methods=["GET"], strict_slashes=False)
@token_required
def get_image():
    """returns a profile picture saved for this user"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("an internal error")
        abort(500)
    image = storage.get("Image", user_id=user_id)
    if image:
        return send_file(image.path, mimetype="image/jpeg"), 200
    logger.warning("image not found")
    return jsonify({"error": "image not found"})


@rider_bp.route("/profile/remove-image", methods=["DELETE"], strict_slashes=False)
@token_required
def remove_image():
    """remove image of this user if exist"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("an internal error")
        abort(500)
    image = storage.get("Image", user_id=user_id)
    if not image:
        logger.warning("image not found")
        return jsonify({"error": "image not found"}), 404
    try:
        storage.delete("Image", image.id)
    except Exception:
        logger.exception("an internal error")
        abort(500)
    if os.path.exists(image.path):
        try:
            os.remove(image.path)
        except Exception:
            logger.exception("an internal error")
            abort(500)
    else:
        logger.warning("path doesn't exist")
        return jsonify({"error": "path doesn't exist"}), 404
    return jsonify({"image": "removed successfuly"}), 200


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_IMAGE_MIMETYPES = {"image/png", "image/jpeg"}


@rider_bp.route("/profile/image", methods=["POST"], strict_slashes=False)
@token_required
def upload_image():
    """uploads a profile picture for this user"""
    try:
        user_id = request.user_id
    except Exception:
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

    ext = os.path.splitext(image.filename)[1].lower()
    if (
        ext not in ALLOWED_IMAGE_EXTENSIONS
        or image.mimetype not in ALLOWED_IMAGE_MIMETYPES
    ):
        logger.warning(
            "rejected upload with extension %s / mimetype %s", ext, image.mimetype
        )
        return jsonify({"error": "only png/jpg/jpeg images are allowed"}), 400

    new_name = str(uuid.uuid4()) + ext
    file_path = os.path.join("./image_uploads", new_name)

    user_image = storage.get("Image", user_id=user_id)
    if user_image:
        if os.path.exists(user_image.path):
            try:
                os.remove(user_image.path)
            except Exception:
                logger.exception("an internal error")
                abort(500)
        try:
            storage.delete("Image", user_image.id)
        except Exception:
            logger.exception("an internal error")
            abort(500)

    image.save(file_path)

    kwargs = {"path": file_path, "user_id": user_id, "user_type": "Rider"}
    try:
        new_image = Image(**kwargs)
        new_image.save()
    except Exception:
        logger.exception("an internal error")
        abort(500)

    return jsonify({"image": "uploaded"}), 200


@rider_bp.route("/profile", methods=["GET"], strict_slashes=False)
@token_required
def get_profile():
    """get user profile"""
    try:
        user_id = request.user_id
    except Exception:
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


@rider_bp.route("/profile", methods=["PUT"], strict_slashes=False)
@token_required
@validate_body(ProfileUpdateSchema)
def put_profile():
    """update user profile by provided informations - password change is
    optional and only validated when actually requested"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("An internal error")
        abort(500)

    user = storage.get_in_dict(cls, id=user_id)
    if not user:
        logger.warning("user not found")
        abort(404)

    updates = request.validated.model_dump(exclude_unset=True, exclude_none=True)

    if "password_hash" in updates:
        if "old_password" not in updates:
            logger.warning("old_password missing")
            return jsonify({"error": "old_password missing"}), 400
        user_password = storage.get(cls, id=user_id)
        check_password = Auth.verify_password(updates["old_password"], user_password)
        if not check_password:
            logger.warning("password incorrect")
            return jsonify({"error": "password incorrect"}), 400
        updates["password_hash"] = _hash_password(updates["password_hash"])
        del updates["old_password"]
    else:
        updates.pop("old_password", None)

    try:
        storage.update(cls, id=user_id, **updates)
    except Exception:
        logger.exception("An internal error")
        return jsonify({"error": "update Failed"}), 500
    return jsonify({"user": "Updated Successfuly"}), 200


# Ride Booking
@rider_bp.route("/available-rides", methods=["GET"], strict_slashes=False)
@token_required
def available_rides():
    """get all rides that are available"""
    order_by = request.args.get("order_by", default="updated_at")
    column = get_sort_column(Trip, "Trip", order_by)

    trips = paginate(storage.get_objs("Trip", is_available=True), column.type, column)
    if not trips:
        logger.warning("trip not found")
        abort(404)
    trips_dict = {}
    for trip in trips:
        driver = storage.get("Driver", id=trip.driver_id)
        if not driver:
            logger.warning("driver not found, skipping trip %s", trip.id)
            continue
        vehicle = driver.vehicle
        if not vehicle:
            logger.warning("driver has no vehicle registered, skipping trip %s", trip.id)
            continue
        try:
            riders = [
                rider.rider
                for rider in storage.get_objs("TripRider", trip_id=trip.id, is_past=False)
            ]
            available_seats = vehicle.seating_capacity - len(riders)
            trips_dict["Trip." + trip.id] = clean(trip.to_dict())
            trips_dict["Trip." + trip.id]["vehicle_holds"] = vehicle.seating_capacity
            trips_dict["Trip." + trip.id]["available_seats"] = available_seats

            trips_dict["Trip." + trip.id]["driver_id"] = clean(
                storage.get(
                    "Driver", id=trips_dict["Trip." + trip.id]["driver_id"]
                ).to_dict()
            )
            trips_dict["Trip." + trip.id]["pickup_location_id"] = clean(
                storage.get(
                    "Location", id=trips_dict["Trip." + trip.id]["pickup_location_id"]
                ).to_dict()
            )
            trips_dict["Trip." + trip.id]["dropoff_location_id"] = clean(
                storage.get(
                    "Location", id=trips_dict["Trip." + trip.id]["dropoff_location_id"]
                ).to_dict()
            )

        except Exception:
            logger.exception("An internal error")
            abort(500)
    if trips:
        return jsonify({"trips": trips_dict}), 200
    logger.warning("trips not found")
    abort(404)


@rider_bp.route("/book-ride", methods=["POST"], strict_slashes=False)
@token_required
@validate_body(BookRideSchema)
def book_ride():
    """book a ride by provided trip id"""
    try:
        rider_id = request.user_id
    except Exception:
        logger.exception("An internal error")
        abort(500)

    trip_id = request.validated.trip_id

    trip = storage.get("Trip", id=trip_id)

    if not trip:
        logger.warning("trip not found")
        abort(404)

    if trip.is_available == False:  # noqa: E712 - nullable column, `not x` would also flip NULL handling
        logger.warning("trip not available")
        return jsonify({"error": "trip not available"}), 400

    riders = []
    for rider in trip.riders:
        if rider.is_past == False:  # noqa: E712 - nullable column, `not x` would also flip NULL handling
            riders.append(rider.rider_id)

    if rider_id in riders:
        logger.warning("you have already booked a ride")
        return jsonify({"error": "you have already booked a ride"}), 200

    vehicle = trip.drivers.vehicle
    if not vehicle:
        logger.warning("driver has no vehicle registered")
        return jsonify({"error": "driver has no vehicle registered"}), 409
    seating_capacity = vehicle.seating_capacity
    number_of_passengers = 0

    for _ in trip.riders:
        if _:
            if _.status != "canceled":
                number_of_passengers += 1

    if number_of_passengers >= seating_capacity:
        logger.warning("maximam seat capacity")
        return jsonify({"error": "maximam seat capacity"}), 409

    riders_canceled = []
    for rider in trip.riders:
        if rider:
            if rider.status == "canceled":
                riders_canceled.append(rider.rider_id)

    if rider_id in riders_canceled:
        trip_rider_id = storage.get("TripRider", trip_id=trip_id, rider_id=rider_id)
        if not trip_rider_id:
            abort(404)
        trip_rider_id = trip_rider_id.id
        try:
            storage.update("TripRider", trip_rider_id, is_past=False, status="booked")
        except Exception:
            logger.exception("An internal error")
            abort(500)
        return jsonify({"ride": "you have booked a ride"}), 201

    kwargs = {"trip_id": trip_id, "rider_id": rider_id}
    try:
        book_ride = TripRider(**kwargs)
        book_ride.save()
    except Exception:
        logger.exception("An internal error")
        abort(500)
    try:
        totalpaymnet = storage.get("TotalPayment", trip_id=trip_id)
        storage.update(
            "TotalPayment",
            totalpaymnet.id,
            total_number_of_riders=totalpaymnet.total_number_of_riders + 1,
            number_of_riders_not_paid=totalpaymnet.number_of_riders_not_paid + 1,
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"ride": "you have booked a ride"}), 201


@rider_bp.route("/ride-estimate", methods=["POST"], strict_slashes=False)
@token_required
def ride_estimate():
    """get estimated km/h, eta... by provided informations"""
    try:
        ride_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    keys = ["distance", "km/h", "km_left", "trip_id"]
    for i in keys:
        if i not in ride_data:
            logger.warning(f"{i} missing")
            return jsonify({"error": f"{i} missing"}), 400
    distance = ride_data["distance"]
    kmh = ride_data["km/h"]
    km_left = ride_data["km_left"]
    eta = km_left / kmh
    trip = storage.get("Trip", id=ride_data["trip_id"])
    if not trip:
        logger.warning("trip not found")
        return jsonify({"error": "trip not found"}), 404
    estimate = {
        "eta": eta,
        "km/h": kmh,
        "km_left": km_left,
        "pickup_time": trip.pickup_time,
        "expected_time_arrival": "",
        "pickup_location": trip.pickup_location,
        "dropoff_location": trip.dropoff_location,
        "distance": distance,
    }
    return jsonify({"estimate": estimate}), 200


@rider_bp.route("/booked-ride", methods=["GET"], strict_slashes=False)
@token_required
def booked_ride():
    """get all booked-rides by the rider"""
    try:
        rider_id = request.user_id
    except Exception:
        logger.exception("An internal error")
        abort(500)

    order_by = request.args.get("order_by", default="updated_at")
    column = get_sort_column(TripRider, "TripRider", order_by)

    rides = paginate(
        storage.get_objs("TripRider", rider_id=rider_id), column.type, column
    )

    if not rides:
        logger.warning("rides not found")
        abort(404)

    trips = [ride for ride in rides if not ride.is_past]

    rides_dict = {}

    for trip in trips:
        try:
            rides_dict["Trip." + trip.trip.id] = clean(trip.trip.to_dict())
            rides_dict["Trip." + trip.trip.id]["trip_ride_id"] = trip.id
        except Exception:
            logger.warning("An internal error")
            abort(500)

    return jsonify({"ride": rides_dict}), 200


@rider_bp.route("/current-ride/<tripride_id>", methods=["GET"], strict_slashes=False)
@token_required
def current_ride(tripride_id):
    """get detailed current-ride by provided tripride-id"""
    try:
        trip = clean(
            storage.get("TripRider", id=tripride_id, is_past=False).trip.to_dict()
        )
    except Exception:
        logger.warning("trip not found")
        abort(500)

    try:
        trip["pickup_location_id"] = clean(
            next(
                iter(
                    storage.get_in_dict(
                        "Location", id=trip["pickup_location_id"]
                    ).values()
                )
            )
        )
        trip["dropoff_location_id"] = clean(
            next(
                iter(
                    storage.get_in_dict(
                        "Location", id=trip["dropoff_location_id"]
                    ).values()
                )
            )
        )
        trip["driver_id"] = clean(storage.get("Driver", id=trip["driver_id"]).to_dict())
    except Exception:
        logger.exception("An internal error")
        abort(500)
    return jsonify({"ride": trip}), 200


@rider_bp.route("/ride-status/<tripride_id>", methods=["GET"], strict_slashes=False)
@token_required
def ride_status(tripride_id):
    """get ride-status by provided tripride-id"""
    try:
        trip = storage.get("TripRider", id=tripride_id, is_past=False).trip
    except Exception:
        logger.exception("An internal error")
        abort(500)

    if not trip:
        logger.warning("trip not found")
        abort(404)

    vehicle = trip.drivers.vehicle
    if not vehicle:
        logger.warning("driver has no vehicle registered")
        abort(404)
    seating_capacity = vehicle.seating_capacity

    number_of_passengers = 0
    for _ in trip.riders:
        number_of_passengers += 1

    trip = trip.to_dict()
    try:
        pickup_location = clean(
            next(
                iter(
                    storage.get_in_dict(
                        "Location", id=trip["pickup_location_id"]
                    ).values()
                )
            )
        )
        dropoff_location = clean(
            next(
                iter(
                    storage.get_in_dict(
                        "Location", id=trip["dropoff_location_id"]
                    ).values()
                )
            )
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)
    seats_left = seating_capacity - number_of_passengers

    ride_status = {
        "pickup_location": pickup_location,
        "dropoff_location": dropoff_location,
        "pickup_time": trip["pickup_time"],
        "status": trip["status"],
        "seats_left": seats_left,
        "distance": trip["distance"],
        "fare": trip["fare"],
    }

    return jsonify({"ride": ride_status}), 200


# Ride History And Management
@rider_bp.route("/ride-history", methods=["GET"], strict_slashes=False)
@token_required
def ride_history():
    """get all ride-histories of this rider"""
    try:
        rider_id = request.user_id
    except Exception:
        logger.exception("An internal error")
        abort(500)

    order_by = request.args.get("order_by", default="updated_at")
    # note: this paginates TripRider rows, so sort against TripRider - the
    # original code resolved order_by against Trip here, a mismatched-model
    # bug that would break as soon as a non-default order_by was passed
    column = get_sort_column(TripRider, "TripRider", order_by)

    try:
        rides = [
            ride.trip
            for ride in paginate(
                storage.get_objs("TripRider", rider_id=rider_id, is_past=True),
                column.type,
                column,
            )
            if ride.trip.status in ["completed", "canceled"]
        ]
    except Exception as e:
        logger.warning(e)
        abort(404)
    ride_dict = {}

    for ride in rides:
        if ride:
            ride_dict["Trip." + ride.id] = clean(ride.to_dict())
        else:
            logger.warning("ride not found")
            return jsonify({"error": "ride not found"}), 404

    return jsonify({"ride": ride_dict}), 200


@rider_bp.route("/cancel-ride", methods=["POST"], strict_slashes=False)
@token_required
@validate_body(BookRideSchema)
def cancel_ride():
    """cancel a ride by provided informations"""
    trip_id = request.validated.trip_id

    trip = storage.get("Trip", id=trip_id)
    if not trip:
        logger.warning("trip not found")
        abort(404)
    if trip.status == "started":
        logger.warning("unable to cancel ride already started")
        return jsonify({"error": "unable to cancel ride already started"}), 409

    triprider = storage.get("TripRider", trip_id=trip_id, rider_id=request.user_id)
    if not triprider:
        logger.warning("triprider not found")
        abort(404)
    triprider = triprider.id

    try:
        storage.update(
            "TripRider",
            id=triprider,
            is_past=True,
            status="canceled",
            status_by="rider",
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"trip": "canceled"}), 200


# Payment
@rider_bp.route("/pay-ride", methods=["POST"], strict_slashes=False)
@token_required
@validate_body(PayRideSchema)
def pay_ride():
    """initiate a Chapa payment for a booked ride. The charge is always
    computed server-side from the trip's fare, never taken from the
    client - the payment only becomes "paid" once the Chapa webhook
    confirms it (see webhook_views.chapa_webhook), not here."""
    user_id = request.user_id
    trip_id = request.validated.trip_id

    trip = storage.get("Trip", id=trip_id)
    if not trip:
        logger.warning("trip missing")
        abort(404)

    trip_rider = storage.get("TripRider", trip_id=trip_id, rider_id=user_id)
    if not trip_rider:
        logger.warning("you haven't booked a ride")
        return jsonify({"error": "you haven't booked a ride"}), 200
    if storage.get("Payment", trip_id=trip_id, rider_id=user_id, payment_status="paid"):
        logger.warning("you have already paid for this ride")
        return jsonify({"error": "you have already paid for this ride"}), 200

    totalpayment = storage.get("TotalPayment", trip_id=trip_id)
    if not totalpayment:
        logger.warning("totalpayment not found")
        abort(404)

    rider = storage.get("Rider", id=user_id)
    tx_ref = f"wego-{trip_id[:8]}-{user_id[:8]}-{uuid.uuid4().hex[:8]}"
    callback_url = f"{request.host_url.rstrip('/')}/api/v1/webhooks/chapa"
    return_url = request.validated.return_url or f"{request.host_url.rstrip('/')}/health"

    try:
        gateway = get_gateway()
        result = gateway.initialize_payment(
            amount=trip.fare,
            currency="ETB",
            customer={
                "email": rider.email,
                "first_name": rider.first_name,
                "last_name": rider.last_name,
            },
            tx_ref=tx_ref,
            callback_url=callback_url,
            return_url=return_url,
        )
    except Exception:
        logger.exception("failed to initialize chapa payment")
        abort(502)

    kwargs = {
        "trip_id": trip_id,
        "rider_id": user_id,
        "payment_method": "chapa",
        "payment_time": datetime.utcnow(),
        "amount": trip.fare,
        "payment_status": "pending",
        "provider": "chapa",
        "provider_tx_ref": result.tx_ref,
    }
    try:
        rider_payment = Payment(**kwargs)
        rider_payment.save()
    except Exception:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"checkout_url": result.checkout_url, "tx_ref": result.tx_ref}), 201


@rider_bp.route("/transactions", methods=["GET"], strict_slashes=False)
@token_required
def get_transaction():
    """get all transactions made by rider"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("an internal error")

    order_by = request.args.get("order_by", default="created_at")
    column = get_sort_column(Payment, "Payment", order_by)

    transactions = [
        clean(transaction.to_dict())
        for transaction in paginate(
            storage.get_objs("Payment", rider_id=user_id), column.type, column
        )
    ]

    return jsonify({"transactions": transactions}), 200


# Ratings
@rider_bp.route("/rate-driver/<trip_id>", methods=["POST"], strict_slashes=False)
@token_required
@validate_body(RatingSchema)
def rate_driver(trip_id):
    """rate the driver of a trip this rider completed"""
    rider_id = request.user_id

    trip = storage.get("Trip", id=trip_id)
    if not trip:
        logger.warning("trip not found")
        abort(404)

    triprider = storage.get("TripRider", trip_id=trip_id, rider_id=rider_id)
    if not triprider or triprider.status != "completed":
        logger.warning("trip not completed for this rider")
        return jsonify({"error": "you can only rate a completed trip"}), 400

    rating, error = submit_rating(
        trip_id=trip_id,
        rater_type="Rider",
        rater_id=rider_id,
        ratee_type="Driver",
        ratee_id=trip.driver_id,
        score=request.validated.score,
        comment=request.validated.comment,
    )
    if error:
        message, status = error
        logger.warning(message)
        return jsonify({"error": message}), status

    return jsonify({"rating": clean(rating.to_dict())}), 201


@rider_bp.route("/ratings", methods=["GET"], strict_slashes=False)
@token_required
def get_rider_ratings():
    """get all ratings this rider has received from drivers"""
    rider_id = request.user_id
    order_by = request.args.get("order_by", default="updated_at")
    column = get_sort_column(Rating, "Rating", order_by)

    ratings = [
        clean(rating.to_dict())
        for rating in paginate(
            storage.get_objs("Rating", ratee_type="Rider", ratee_id=rider_id),
            column.type,
            column,
        )
    ]
    return jsonify({"ratings": ratings}), 200


# Notifications
@rider_bp.route("/report-issue", methods=["POST"], strict_slashes=False)
@token_required
@validate_body(NotificationSchema)
def report_issue():
    """report an issue by setting a notification table by provided informations"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("An internal error")
        abort(500)

    message = request.validated.message

    admins = [
        admin
        for admin in storage.get_objs("Admin")
        if not admin.blocked and not admin.deleted
    ]
    for admin in admins:
        if admin:
            kwargs = {
                "sender_id": user_id,
                "sender_type": "Rider",
                "receiver_id": admin.id,
                "receiver_type": admin.__class__.__name__,
                "message": message,
                "notification_type": "issue",
            }

            try:
                notification = Notification(**kwargs)
                notification.save()
            except Exception:
                logger.exception("An internal error")
                abort(500)

    return jsonify({"issue": "reported"}), 201


@rider_bp.route("/notifications", methods=["GET"], strict_slashes=False)
@token_required
def get_issues():
    """get all notifications"""
    try:
        user_id = request.user_id
    except Exception:
        logger.exception("an internal error")
        abort(500)

    order_by = request.args.get("order_by", default="updated_at", type=str)
    column = get_sort_column(Notification, "Notification", order_by)

    notification = [
        dict(clean(notif.to_dict()), sent_at=notif.created_at)
        for notif in paginate(
            storage.get_objs("Notification", receiver_id=user_id), column.type, column
        )
    ]
    return jsonify({"notifications": notification}), 200


@rider_bp.route("/notification/<notification_id>", methods=["GET"], strict_slashes=False)
@token_required
def get_notification(notification_id):
    """get notification by notification_id"""
    notification = storage.get("Notification", id=notification_id)
    if not notification:
        logger.warning("notification not found")
        return jsonify({"notification": "notification not found"}), 404
    try:
        storage.update(
            "Notification", id=notification_id, is_read=True, read_at=datetime.utcnow()
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)
    notification = storage.get("Notification", id=notification_id).to_dict()

    notification["sent_at"] = notification["created_at"]
    try:
        notification["sender_id"] = clean(
            storage.get(
                notification["sender_type"], id=notification["sender_id"]
            ).to_dict()
        )
    except Exception:
        logger.exception("An internal error")
        abort(500)
    notification = clean(notification)
    return jsonify({"notification": notification}), 200
