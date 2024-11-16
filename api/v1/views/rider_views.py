#!/usr/bin/python
from api.v1.views import rider_bp
from flask import jsonify, request, abort, send_file
from auth import authentication
from auth.authentication import _hash_password, clean
from models import storage
from api.v1.middleware import token_required, admin_required
from models.trip import Trip
from models.notification import Notification
from models.trip_rider import TripRider
from models.payment import Payment
from models.image import Image
from api.v1.utils.pagination import paginate
from datetime import datetime
import logging
import uuid
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

Auth = authentication.Auth()

rider_key = [
    "username",
    "first_name",
    "last_name",
    "email",
    "phone_number",
    "password_hash",
    "payment_method",
]
cls = "Rider"


# Registation And Authentication
@rider_bp.route("/register", methods=["POST"], strict_slashes=False)
def register():
    """register a new rider by provided informations"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    for k in rider_key:
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


@rider_bp.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """login as rider by provided credentails"""
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
        logger.warning("email missing")
        return jsonify({"error": "password missing"}), 400

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


@rider_bp.route("/logout", methods=["POST"], strict_slashes=False)
@token_required
def logout():
    """logout and black-list jwt token"""
    return jsonify({"User": "Logged out"}), 200


# Profile Management
@rider_bp.route("/reset-token", methods=["POST"], strict_slashes=False)
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


@rider_bp.route("/forget-password", methods=["POST"], strict_slashes=False)
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
    except:
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


@rider_bp.route("/profile/image", methods=["POST"], strict_slashes=False)
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

    kwargs = {"path": full_path, "user_id": user_id, "user_type": "Rider"}
    try:
        new_image = Image(**kwargs)
        new_image.save()
    except:
        logger.exception("an internal error")
        abort(500)

    return jsonify({"image": "uploaded"}), 200


@rider_bp.route("/profile", methods=["GET"], strict_slashes=False)
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


@rider_bp.route("/profile", methods=["PUT"], strict_slashes=False)
@token_required
def put_profile():
    """update user profile by provided informations including password update"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

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
                logger.warning("old_password missing")
                return jsonify({"error": "old_password missing"}), 400
        else:
            logger.warning("password_hash missing")
            return jsonify({"error": "password_hash missing"}), 400
        try:
            storage.update(cls, id=user_id, **updates)
        except:
            logger.exception("An internal error")
            return jsonify({"error": "update Failed"}), 500
    return jsonify({"user": "Updated Successfuly"}), 200


# Ride Booking
@rider_bp.route("/available-rides", methods=["GET"], strict_slashes=False)
@token_required
def available_rides():
    """get all rides that are available"""
    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(Trip, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify({"error": f"type object '{Trip}' has no attribute {order_by}"})

    trips = paginate(storage.get_objs("Trip", is_available=True), column.type, column)
    if not trips:
        logger.warning("trip not found")
        abort(404)
    trips_dict = {}
    for trip in trips:
        try:
            vehicle = storage.get("Driver", id=trip.driver_id)
            if vehicle:
                try:
                    vehicle = vehicle.vehicle
                except:
                    logger.exception("vehicle not found")
                    abort(500)
            else:
                logger.warning("driver not found")
                abort(404)
            riders = [
                rider.rider
                for rider in storage.get_objs(
                    "TripRider", trip_id=trip.id, is_past=False
                )
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

        except:
            logger.exception("An internal error")
            abort(500)
    if trips:
        return jsonify({"trips": trips_dict}), 200
    logger.warning("trips not found")
    abort(404)


@rider_bp.route("/book-ride", methods=["POST"], strict_slashes=False)
@token_required
def book_ride():
    """book a ride by provided trip id"""
    try:
        ride_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    try:
        rider_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    if "trip_id" not in ride_data:
        logger.warning("trip_id missing")
        return jsonify({"error": "trip_id missing"}), 400

    trip_id = ride_data["trip_id"]

    trip = storage.get("Trip", id=trip_id)

    if not trip:
        logger.warning("trip not found")
        abort(404)

    if trip.is_available == False:
        logger.warning("trip not available")
        return jsonify({"error": "trip not available"}), 400

    riders = []
    for rider in trip.riders:
        if rider.is_past == False:
            riders.append(rider.rider_id)

    if rider_id in riders:
        logger.warning("you have already booked a ride")
        return jsonify({"error": "you have already booked a ride"}), 200

    try:
        vehicle = trip.drivers.vehicle
        seating_capacity = vehicle.seating_capacity
    except:
        logger.exception("An internal error")
        abort(500)
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
        except:
            logger.exception("An internal error")
            abort(500)
        return jsonify({"ride": "you have booked a ride"}), 201

    kwargs = {"trip_id": trip_id, "rider_id": rider_id}
    try:
        book_ride = TripRider(**kwargs)
        book_ride.save()
    except:
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
    except:
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
    except:
        logger.exception("An internal error")
        abort(500)

    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(TripRider, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{TripRider}' has no attribute {order_by}"}
        )

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
        except:
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
    except:
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
    except:
        logger.exception("An internal error")
        abort(500)
    return jsonify({"ride": trip}), 200


@rider_bp.route("/ride-status/<tripride_id>", methods=["GET"], strict_slashes=False)
@token_required
def ride_status(tripride_id):
    """get ride-status by provided tripride-id"""
    try:
        trip = storage.get("TripRider", id=tripride_id, is_past=False).trip
        vehicle = trip.drivers.vehicle
        seating_capacity = vehicle.seating_capacity
    except:
        logger.exception("An internal error")
        abort(500)

    if not trip:
        logger.warning("trip not found")
        abort(404)

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
    except:
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
    except:
        logger.exception("An internal error")
        abort(500)

    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(Trip, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify({"error": f"type object '{Trip}' has no attribute {order_by}"})

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
def cancel_ride():
    """cancel a ride by provided informations"""
    try:
        request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    if "trip_id" not in request.get_json():
        logger.warning("trip missing")
        return jsonify({"error": "trip missing"}), 400

    trip_id = request.get_json()["trip_id"]

    if storage.get("Trip", id=trip_id).status == "started":
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
    except:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"trip": "canceled"}), 200


# Payment
@rider_bp.route("/pay-ride", methods=["POST"], strict_slashes=False)
@token_required
def pay_ride():
    """set payment tabe for a completed trip by provide informations"""
    try:
        request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    for i in ["amount", "status", "trip_id", "payment_method"]:
        if i not in request.get_json():
            logger.warning(f"{i} missing")
            return jsonify({"error": f"{i} missing"}), 400

    amount = request.get_json()["amount"]
    trip_id = request.get_json()["trip_id"]

    trip = storage.get("Trip", id=trip_id)
    if not trip:
        logger.warning("trip missing")
        abort(404)
    if amount < trip.fare:
        logger.warning("not the right amount")
        return jsonify({"error": "not the right amount"}), 400

    trip_rider = storage.get("TripRider", trip_id=trip_id, rider_id=request.user_id)
    if not trip_rider:
        logger.warning("you haven't booked a ride")
        return jsonify({"error": "you haven't booked a ride"}), 200
    if storage.get("Payment", trip_id=trip_id, rider_id=user_id):
        logger.warning("you haven already paid for this ride")
        return jsonify({"error": "you haven already paid for this ride"}), 200
    kwargs = {
        "trip_id": trip_id,
        "rider_id": user_id,
        "payment_method": request.get_json()["payment_method"],
        "payment_time": datetime.utcnow(),
        "amount": amount,
        "payment_status": request.get_json()["status"],
    }

    totalpayment = storage.get("TotalPayment", trip_id=trip_id)
    if not totalpayment:
        logger.warning("totalpayment not found")
        abort(404)

    try:
        rider_payment = Payment(**kwargs)
        rider_payment.save()
    except:
        logger.exception("An internal error")
        abort(500)

    try:
        storage.update(
            "TotalPayment",
            totalpayment.id,
            number_of_riders_paid=totalpayment.number_of_riders_paid + 1,
            number_of_riders_not_paid=totalpayment.number_of_riders_not_paid - 1,
            total_revenue=totalpayment.total_revenue + amount,
        )
    except:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"payment": "paid"}), 201


@rider_bp.route("/transactions", methods=["GET"], strict_slashes=False)
@token_required
def get_transaction():
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")

    try:
        order_by = request.args.get("order_by", default="created_at")
        if order_by:
            column = getattr(Payment, order_by)
    except Exception as e:
        logger.warning(e)
        abort(400)

    transactions = [
        clean(transaction.to_dict())
        for transaction in paginate(
            storage.get_objs("Payment", rider_id=user_id), column.type, column
        )
    ]

    return jsonify({"transactions": transactions})


# Ratings And Feedback
@rider_bp.route("/report-issue", methods=["POST"], strict_slashes=False)
@token_required
def report_issue():
    """report an issue by setting a notification table by provided informations"""
    try:
        data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    if "message" not in data:
        logger.warning("message missing")
        return jsonify({"error": "message missing"}), 400

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
                "message": data["message"],
                "notification_type": "issue",
            }

            try:
                notification = Notification(**kwargs)
                notification.save()
            except:
                logger.exception("An internal error")
                abort(500)

    return jsonify({"issue": "reported"}), 201


@rider_bp.route("/notifications", methods=["GET"], strict_slashes=False)
@token_required
def get_issues():
    """get all notifications"""
    try:
        user_id = request.user_id
    except:
        logger.exception("an internal error")
        abort(500)

    try:
        order_by = request.args.get("order_by", default="updated_at", type=str)
        if order_by:
            column = getattr(Notification, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{Notification}' has no attribute {order_by}"}
        )

    notification = [
        dict(clean(notif.to_dict()), sent_at=notif.created_at)
        for notif in paginate(
            storage.get_objs("Notification", receiver_id=user_id), column.type, column
        )
    ]
    return jsonify({"notifications": notification}), 200


@rider_bp.route(
    "/notification/<notification_id>", methods=["GET"], strict_slashes=False
)
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
    except:
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
    except:
        logger.exception("An internal error")
        abort(500)
    notification = clean(notification)
    return jsonify({"notification": notification}), 200
