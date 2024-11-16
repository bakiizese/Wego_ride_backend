#!/usr/bin/python
from models import storage
from api.v1.middleware import admin_required, superadmin_required
from api.v1.views import admin_bp
from flask import jsonify, request, abort
from auth import authentication
from auth.authentication import clean
from models.rider import Rider
from models.driver import Driver
from models.admin import Admin
from models.trip import Trip
from models.location import Location
from datetime import datetime, timedelta
from models.notification import Notification
from models.total_payment import TotalPayment
from models.payment import Payment
import logging
from api.v1.utils.pagination import paginate
from collections import OrderedDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

Auth = authentication.Auth()
cls = "Admin"
admin_key = [
    "email",
    "username",
    "first_name",
    "last_name",
    "phone_number",
    "password_hash",
    "admin_level",
]
classes = {"Driver": Driver, "Rider": Rider, "Admin": Admin}


# Admin Authentication
@admin_bp.route("/admin-register", methods=["POST"], strict_slashes=False)
@superadmin_required
def register():
    """register a new admin by providing necessary informations"""
    try:
        user_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    for k in admin_key:
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
        logger.exception("An internal errro")
        abort(500)
    if status:
        return jsonify({"user": message}), 201
    logger.warning(message)
    return jsonify({"error": message}), 400


@admin_bp.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """login as admin by provided credentials"""
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
        logger.warning("password missing")
        return jsonify({"error": "password missing"}), 400
    try:
        user = Auth.verify_login(
            cls, find_with, user_data[find_with], user_data["password_hash"]
        )
        message, status = user
    except:
        logger.warning("an internal error")
        abort(500)

    if status:
        return jsonify({"user": status}), 200
    logger.warning(message)
    return jsonify({"error": message}), 400


@admin_bp.route("/logout", methods=["POST"], strict_slashes=False)
@admin_required
def logout():
    """logout and black-list jwt token"""
    return jsonify({"admin": "Logged out"}), 200


# Rider And Driver Management
@admin_bp.route("/riders", methods=["GET"], strict_slashes=False)
@admin_required
def get_riders():
    """get all rider-users that are not deleted and blocked"""
    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(classes["Rider"], order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{classes['Rider']}' has no attribute {order_by}"}
        )
    riders = [
        clean(v.to_dict())
        for v in paginate(storage.get_objs("Rider"), column.type, column)
        if not v.deleted and not v.blocked
    ]

    return jsonify({"riders": riders}), 200


@admin_bp.route("/drivers", methods=["GET"], strict_slashes=False)
@admin_required
def get_drivers():
    """get all driver-users that are not deleted and blocked"""
    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(classes["Driver"], order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{classes['Driver']}' has no attribute {order_by}"}
        )
    drivers = [
        clean(v.to_dict())
        for v in paginate(storage.get_objs("Driver"), column.type, column)
        if not v.deleted and not v.blocked
    ]

    return jsonify({"drivers": drivers}), 200


@admin_bp.route("/block-user/<user_id>", methods=["PUT"], strict_slashes=False)
@admin_required
def block_user(user_id):
    """block a user by provided user-id"""
    cls_ = ""
    for cls in ["Driver", "Rider", "Admin"]:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == "Admin":

                    @superadmin_required
                    def unblock_admin():
                        try:
                            storage.update(cls, user_id, blocked=True)
                        except:
                            logger.exception("an internal error")
                            abort(500)

                    unblock_admin()
                else:
                    try:
                        storage.update(cls, user_id, blocked=True)
                    except:
                        logger.exception("an internal erro")
                        abort(500)
                cls_ = cls
                break
            except:
                logger.warning(f"unable to block {cls}")
                return jsonify({"error": f"Unable to block {cls}"}), 400
        else:
            logger.warning(f"{cls} already blocked")
            return jsonify({"user": f"{cls} already blocked"}), 200
    if not cls_:
        logger.warning("user not found")
        return jsonify({"user": "user not found"}), 404
    return jsonify({"user": f"{cls_} blocked"}), 200


@admin_bp.route("/unblock-user/<user_id>", methods=["PUT"], strict_slashes=False)
@admin_required
def unblock_user(user_id):
    """unblock a user by provided user id"""
    cls_ = ""
    for cls in ["Driver", "Rider", "Admin"]:
        if not storage.get(cls, id=user_id):
            continue
        if storage.get(cls, id=user_id).blocked:
            try:
                if cls == "Admin":

                    @superadmin_required
                    def unblock_admin():
                        try:
                            storage.update(cls, user_id, blocked=False)
                        except:
                            logger.exception("An internal error")
                            abort(500)

                    unblock_admin()
                else:
                    try:
                        storage.update(cls, user_id, blocked=False)
                    except:
                        logger.exception("An internal error")
                        abort(500)
                cls_ = cls
                break
            except:
                logger.warning(f"unable to unblock {cls}")
                return jsonify({"error": f"Unable to unblock {cls}"}), 400
        else:
            logger.warning(f"{cls} already unblocked")
            return jsonify({"user": f"{cls} already unblocked"}), 200
    if not cls_:
        logger.warning("user not found")
        return jsonify({"user": "user not found"}), 404
    return jsonify({"user": f"{cls_} unblocked"}), 200


@admin_bp.route("/delete-user/<user_id>", methods=["PUT"], strict_slashes=False)
@admin_required
def delete_user(user_id):
    """delete a user by provided user-id"""
    cls_ = ""
    for cls in ["Driver", "Rider", "Admin"]:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == "admin":

                    @superadmin_required
                    def delete_admin():
                        try:
                            storage.update(cls, user_id, deleted=True)
                        except:
                            logger.exception("An internal error")
                            abort(500)

                    delete_admin()
                else:
                    try:
                        storage.update(cls, user_id, deleted=True)
                    except:
                        logger.exception("An internal error")
                        abort(500)
                cls_ = cls
                break
            except:
                logger.warning(f"unable to delete {cls}")
                return jsonify({"error": f"Unable to delete {cls}"}), 400
        else:
            logger.warning(f"{cls} already deleted")
            return jsonify({"user": f"{cls} already deleted"}), 200
    if not cls_:
        logger.warning("user not found")
        return jsonify({"user": "user not found"}), 404
    return jsonify({"user": f"{cls_} deleted"}), 200


@admin_bp.route("/revalidate-user/<user_id>", methods=["PUT"], strict_slashes=False)
@admin_required
def revalidate_user(user_id):
    """revalidate a user by provided user-id"""
    cls_ = ""
    for cls in ["Driver", "Rider", "Admin"]:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == "admin":

                    @superadmin_required
                    def delete_admin():
                        try:
                            storage.update(cls, user_id, deleted=False)
                        except:
                            logger.exception("An internal error")
                            abort(500)

                    delete_admin()
                else:
                    try:
                        storage.update(cls, user_id, deleted=False)
                    except:
                        logger.exception("An internal error")
                        abort(500)
                cls_ = cls
                break
            except:
                logger.warning(f"unable to revalidate {cls}")
                return jsonify({"error": f"Unable to revalidate {cls}"}), 400
        else:
            logger.warning(f"{cls} already revalidated")
            return jsonify({"user": f"{cls} already revalidated"}), 200
    if not cls_:
        logger.warning("user not found")
        return jsonify({"user": "user not found"}), 404
    return jsonify({"user": f"{cls_} revalidated"}), 200


@admin_bp.route("/deleted-users/<user_type>", methods=["GET"], strict_slashes=False)
@admin_required
def deleted_users(user_type):
    """get all users that are deleted by provided user-type"""
    if user_type not in ["Rider", "Driver", "Admin"]:
        logger.warning("incorrect user_type")
        return jsonify({"error": "incorrect user_type"}), 400

    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(classes[user_type], order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{classes[user_type]}' has no attribute {order_by}"}
        )

    users = [
        clean(v.to_dict())
        for v in paginate(storage.get_objs(user_type), column.type, column)
        if v.deleted
    ]
    return jsonify({"users": users}), 200


@admin_bp.route("/blocked-users/<user_type>", methods=["GET"], strict_slashes=False)
@admin_required
def blocked_users(user_type):
    """get all users that are blocked by provided user-type"""
    if user_type not in ["Rider", "Driver", "Admin"]:
        logger.warning("incorrect user_type")
        return jsonify({"error": "incorrect user_type"}), 400

    try:
        order_by = request.args.get("order_by", default="updated_at")
        if order_by:
            column = getattr(classes[user_type], order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{classes[user_type]}' has no attribute {order_by}"}
        )

    users = [
        clean(v.to_dict())
        for v in paginate(storage.get_objs(user_type), column.type, column)
        if v.blocked
    ]

    return jsonify({"users": users}), 200


@admin_bp.route("/user-profile/<user_id>", methods=["GET"], strict_slashes=False)
@admin_required
def user_profile(user_id):
    """get user profile by provided user-id"""
    user = ""
    for i in ["Rider", "Driver", "Admin"]:
        user = storage.get(i, id=user_id)
        if user:
            user = clean(user.to_dict())
            break
    if user:
        return jsonify({"user": user}), 200
    logger.warning("user not found")
    return jsonify({"error": "user not found"}), 404


@admin_bp.route(
    "/user_by/<user_type>/<search_type>/<search_by>",
    methods=["GET"],
    strict_slashes=False,
)
@admin_required
def filter_user(user_type, search_type, search_by):
    """search user by provided search_by"""
    if user_type not in ["Admin", "Driver", "Rider"]:
        logger.warning("user_type doesnt exist")
        abort(400)
    try:
        column = getattr(classes[user_type], search_type)
    except Exception as e:
        logger.warning(e)
        return abort(400)

    users = [
        clean(user.to_dict())
        for user in storage.get_objs(
            user_type,
        )
        .filter(column.like(f"%{search_by}%"))
        .all()
    ]

    return jsonify({"users": users})


# Ride Management
@admin_bp.route("/get-rides", methods=["GET"], strict_slashes=False)
@admin_required
def get_rides():
    """get all rides"""
    trips = storage.get_objs("Trip")
    if not trips:
        logger.warning("trips not found")
        return jsonify({"error": "trip not found"}), 404

    trips_dict = OrderedDict()
    try:
        order_by = request.args.get("order_by", default="updated_at", type=str)
        if order_by:
            column = getattr(Trip, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify({"error": f"type object '{Trip}' has no attribute {order_by}"})

    trips = [trip for trip in paginate(trips, column.type, column)]
    try:
        for trip in trips:
            try:
                vehicle = storage.get("Driver", id=trip.driver_id).vehicle
            except:
                logger.exception
                abort(500)
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
            trips_dict["Trip." + trip.id]["vehicle"] = clean(
                storage.get("Vehicle", driver_id=trip.driver_id).to_dict()
            )
    except:
        logger.exception("An internal error")
        abort(500)
    return jsonify({"trips": trips_dict}), 200


@admin_bp.route("/get-ride/<ride_id>", methods=["GET"], strict_slashes=False)
@admin_required
def get_ride(ride_id):
    """get detailed ride by provided ride-id"""
    booked_riders = []
    canceled_riders = []
    payment = None

    try:
        ride = storage.get("Trip", id=ride_id)
        if not ride:
            logger.warning("ride not found")
            abort(404)
        ride = clean(ride.to_dict())
        try:
            booked_riders = [
                clean(rider.rider.to_dict())
                for rider in storage.get_objs("TripRider", trip_id=ride_id)
                if rider.status == "booked"
            ]
        except:
            booked_riders = None
        try:
            canceled_riders = [
                clean(rider.rider.to_dict())
                for rider in storage.get_objs("TripRider", trip_id=ride_id)
                if rider.status == "Canceled"
            ]
        except:
            canceled_riders = None
        try:
            payment = clean(storage.get("Payment", trip_id=ride_id).to_dict())
        except:
            payment = None
    except:
        logger.exception("an internal error")
        abort(500)
    ride["riders"] = {"booked": booked_riders, "canceled": canceled_riders}
    ride["payment"] = payment

    return jsonify({"ride": ride}), 200


@admin_bp.route("/delete-ride/<ride_id>", methods=["PUT"], strict_slashes=False)
@admin_required
def delete_ride(ride_id):
    """delete a ride by provided ride-id"""
    try:
        storage.update("Trip", ride_id, is_available=False)
    except:
        logger.exception("An internal error")
        abort(500)
    return jsonify({"admin": "Ride deleted"}), 200


@admin_bp.route("/set-location", methods=["POST"], strict_slashes=False)
@admin_required
def set_location():
    """set a new location by provided informations"""
    try:
        location_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    for i in ["latitude", "longitude", "address"]:
        if i not in location_data:
            logger.warning(f"{i} missing")
            return jsonify({"error": f"{i} missing"}), 400
    kwargs = {
        "latitude": location_data["latitude"],
        "longitude": location_data["longitude"],
        "address": location_data["address"],
    }
    try:
        location = Location(**kwargs)
        location.save()
    except:
        logger.exception("an internal error")
        abort(500)
    return jsonify({"location": "location created"}), 200


@admin_bp.route("/get-locations", methods=["GET"], strict_slashes=False)
@admin_required
def get_locations():
    """get all locations"""
    try:
        order_by = request.args.get("order_by", default="updated_at", type=str)
        if order_by:
            column = getattr(Location, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{Location}' has no attribute {order_by}"}
        )

    locations = [
        clean(location.to_dict())
        for location in paginate(storage.get_objs("Location"), column.type, column)
    ]
    if not locations:
        logger.warning("locations not found")
        return jsonify({"error": "location not found"}), 404
    return jsonify({"locations": locations}), 200


@admin_bp.route("/set-ride", methods=["POST"], strict_slashes=False)
@admin_required
def set_ride():
    """set a new ride(trip) and totalpayment table by provieded informations"""
    try:
        ride_data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)
    args = [
        "driver_id",
        "pickup_location_id",
        "dropoff_location_id",
        "pickup_time",
        "dropoff_time",
        "fare",
        "distance",
        "status",
        "driver_commission",
    ]
    for i in args:
        if i not in ride_data:
            logger.warning(f"{i} missing")
            return jsonify({"error": f"{i} missing"}), 400
    availability = True
    if "is_available" in ride_data:
        availability = ride_data["is_available"]

    kwargs = {
        "driver_id": ride_data["driver_id"],
        "pickup_location_id": ride_data["pickup_location_id"],
        "dropoff_location_id": ride_data["dropoff_location_id"],
        "pickup_time": ride_data["pickup_time"],
        "dropoff_time": ride_data["dropoff_time"],
        "fare": ride_data["fare"],
        "distance": ride_data["distance"],
        "status": ride_data["status"],
        "is_available": availability,
    }
    try:
        trip = Trip(**kwargs)
        trip.save()
    except:
        logger.exception("An internal error")
        abort(500)

    kwargs = {
        "trip_id": trip.id,
        "driver_id": trip.driver_id,
        "trip_fare": trip.fare,
        "driver_commission": ride_data["driver_commission"],
    }
    try:
        totalpayment = TotalPayment(**kwargs)
        totalpayment.save()
    except Exception as e:
        logger.exception("An internal error")
        abort(500)

    return jsonify({"ride": "ride created"}), 200


# Payment Management
@admin_bp.route("/transactions", methods=["GET"], strict_slashes=False)
@admin_required
def get_transactions():
    """get all transactions(payments)"""
    try:
        order_by = request.args.get("order_by", default="updated_at", type=str)
        if order_by:
            column = getattr(Payment, order_by)
    except Exception as e:
        logger.warning(e)
        return jsonify(
            {"error": f"type object '{Payment}' has no attribute {order_by}"}
        )

    transactions = [
        clean(transaction.to_dict())
        for transaction in paginate(storage.get_objs("Payment"), column.type, column)
    ]

    if transactions:
        return jsonify({"admin": transactions}), 200

    logger.warning("transactions not found")
    return jsonify({"admin": "Transactions not found"}), 404


@admin_bp.route("payment/<ride_id>", methods=["GET"], strict_slashes=False)
@admin_required
def payment_detail(ride_id):
    """get a payment by provided ride-id"""
    payment = storage.get("TotalPayment", trip_id=ride_id)
    if payment:
        payment = clean(payment.to_dict())
        return jsonify({"payment": payment}), 200
    logger.warning("payment not found")
    return jsonify({"error": "payment not found"}), 404


@admin_bp.route("/payment-detail/<ride_id>", methods=["GET"], strict_slashes=False)
@admin_required
def get_payment_detail(ride_id):
    """get detailed payment by provided ride-id"""
    trip = storage.get("Trip", id=ride_id)
    if not trip:
        logger.warning("ride not found")
        return jsonify({"error": "ride not found"}), 404

    trip_dict = clean(trip.to_dict())
    total_amount = 0
    try:
        riders = [rider.rider for rider in storage.get("Trip", id=ride_id).riders]
    except:
        logger.exception("An internal error")
        abort(500)

    for py in riders:
        if py.payment:
            total_amount += py.payment[0].amount

    riders_dict = [clean(ride.to_dict()) for ride in riders]
    for ride in riders_dict:
        if ride["payment"]:
            ride["payment"] = clean(ride["payment"][0].to_dict())
    try:
        payment_status = [
            payment.payment_status
            for payment in storage.get("Trip", id=ride_id).payment
        ]
        number_of_riders = len(
            [rider for rider in storage.get("Trip", id=ride_id).riders]
        )
    except:
        logger.exception("An internal error")
        abort(500)

    payment_dict = {
        "trip": trip_dict,
        "total_paid_amount": total_amount,
        "payment_status": payment_status,
        "number_of_riders": number_of_riders,
        "riders": riders_dict,
    }
    return jsonify({"payment": payment_dict}), 200


# Reports And Analytics
@admin_bp.route("/reports/earnings/<date>", methods=["GET"], strict_slashes=False)
@admin_bp.route(
    "/reports/earnings", defaults={"date": None}, methods=["GET"], strict_slashes=False
)
@admin_required
def get_earnings(date):
    """get all earnings report or by provieded date"""
    payments = [
        payment
        for payment in storage.get_objs("TotalPayment")
        if payment.transaction_over == True
    ]
    now = datetime.now()

    (
        today_drivers_earning,
        today_total_earning,
        yesterday_drivers_earning,
        yesterday_total_earning,
        this_month_drivers_earning,
        this_month_total_earning,
        last_month_drivers_earning,
        last_month_total_earning,
        this_year_drivers_earning,
        this_year_total_earning,
    ) = (0,) * 10
    try:
        if date:
            date = datetime.strptime(date, "%d-%m-%Y")
            for payment in payments:
                if payment.transaction_time.date() == date.date():
                    today_drivers_earning += payment.driver_earning
                    today_total_earning += payment.total_revenue
                if (
                    payment.transaction_time.month == date.month
                    and payment.transaction_time.year == date.year
                ):
                    this_month_drivers_earning += payment.driver_earning
                    this_month_total_earning += payment.total_revenue
                if payment.transaction_time.year == date.year:
                    this_year_drivers_earning += payment.driver_earning
                    this_year_total_earning += payment.total_revenue

            earnings = {
                f"day_{date.day}_earning": {
                    "total_platform_earning": today_total_earning
                    - today_drivers_earning,
                    "total_driver_earning": today_drivers_earning,
                    "total": today_total_earning,
                },
                f"month_{date.month}_earning": {
                    "total_platform_earning": this_month_total_earning
                    - this_month_drivers_earning,
                    "total_driver_earning": this_month_drivers_earning,
                    "total": this_month_total_earning,
                },
                f"year_{date.year}_earning": {
                    "total_platform_earning": this_year_total_earning
                    - this_year_drivers_earning,
                    "total_driver_earning": this_year_drivers_earning,
                    "total": this_year_total_earning,
                },
            }
            return jsonify({"Admin": earnings}), 200

        total_driver_revenue = sum([payment.driver_earning for payment in payments])
        total_revenue = sum([payment.total_revenue for payment in payments])
        total_platform_revenue = total_revenue - total_driver_revenue

        for payment in payments:
            if payment.transaction_time.date() == now.date():
                today_drivers_earning += payment.driver_earning
                today_total_earning += payment.total_revenue
            if payment.transaction_time.date() == (now - timedelta(days=1)).date():
                yesterday_drivers_earning += payment.driver_earning
                yesterday_total_earning += payment.total_revenue
            if (
                payment.transaction_time.month == now.month
                and payment.transaction_time.year == now.year
            ):
                this_month_drivers_earning += payment.driver_earning
                this_month_total_earning += payment.total_revenue
            if (
                payment.transaction_time.year == now.year
                and payment.transaction_time.month == (now.month - 1)
            ):
                last_month_drivers_earning += payment.driver_earning
                last_month_total_earning += payment.total_revenue
            if payment.transaction_time.year == now.year:
                this_year_drivers_earning += payment.driver_earning
                this_year_total_earning += payment.total_revenue

        today_platform_earning = today_total_earning - today_drivers_earning
        yesterday_platform_earning = yesterday_total_earning - yesterday_drivers_earning
        this_month_platform_earning = (
            this_month_total_earning - this_month_drivers_earning
        )
        last_month_platform_earning = (
            last_month_total_earning - last_month_drivers_earning
        )
        this_year_platform_earning = this_year_total_earning - this_year_drivers_earning
    except:
        logger.exception("An internal error")
        abort(500)
    earnings = {
        "total_revenue": {
            "total_platform_earning": total_platform_revenue,
            "total_driver_earning": total_driver_revenue,
            "total": total_revenue,
        },
        "today_earning": {
            "total_platform_earning": today_platform_earning,
            "total_driver_earning": today_drivers_earning,
            "total": today_total_earning,
        },
        "yesterday_earning": {
            "total_platform_earning": yesterday_platform_earning,
            "total_driver_earning": yesterday_drivers_earning,
            "total": yesterday_total_earning,
        },
        "this_month": {
            "total_platform_earning": this_month_platform_earning,
            "total_driver_earning": this_month_drivers_earning,
            "total": this_month_total_earning,
        },
        "last_month": {
            "total_platform_earning": last_month_platform_earning,
            "total_driver_earning": last_month_drivers_earning,
            "total": last_month_total_earning,
        },
        "this_year": {
            "total_platform_earning": this_year_platform_earning,
            "total_driver_earning": this_year_drivers_earning,
            "total": this_year_total_earning,
        },
    }
    return jsonify({"Admin": earnings}), 200


@admin_bp.route("/reports/ride-activity", methods=["GET"], strict_slashes=False)
@admin_required
def get_ride_activity():
    """get all detailed rides activities"""
    rides = [ride for ride in storage.get_objs("Trip")]
    (
        completed,
        canceled,
        in_progress,
        paid,
        pending,
        morning,
        afternoon,
        evening,
    ) = (0,) * 8
    drivers = []
    locations = []

    try:
        for ride in rides:
            if ride.status == "completed":
                completed += 1
            elif ride.status == "canceled":
                canceled += 1
            elif ride.status in ["available", "started"]:
                in_progress += 1
            locations.append(ride.pickup_location_id + "." + ride.dropoff_location_id)
            drivers.append(ride.drivers.username)
            status = ride.total_payment
            if status[0].status == "pending":
                pending += 1
            elif status[0].status == "paid":
                paid += 1
            if ride.pickup_time.hour > 5 and ride.pickup_time.hour < 12:
                morning += 1
            elif ride.pickup_time.hour > 12 and ride.pickup_time.hour < 17:
                afternoon += 1
            elif ride.pickup_time.hour > 17:
                evening += 1

        location_dict = {}
        for location in locations:
            location_dict[location] = locations.count(location)
        driver_dict = {}
        for driver in drivers:
            driver_dict[driver] = drivers.count(driver)
    except:
        logger.exception("An internal error")
        abort(500)
    ride_activity = {
        "total_rides": len(rides),
        "rides_by_status": {
            "completed": completed,
            "canceled": canceled,
            "in-progress": in_progress,
        },
        "ride_by_driver": driver_dict,
        "ride_by_location": location_dict,
        "ride_by_time": {
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
        },
        "ride_by_paymnet": {"paid": paid, "pending": pending},
    }
    return jsonify({"Admin": ride_activity})


@admin_bp.route("/reports/announcements", methods=["GET"], strict_slashes=False)
@admin_required
def get_announcement():
    """get all reported isssues"""
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

    announcement = [
        dict(clean(announ.to_dict()), sent_at=announ.created_at)
        for announ in paginate(
            storage.get_objs(
                "Notification",
                sender_id=user_id,
            ),
            column.type,
            column,
        )
    ]
    return jsonify({"announcemet": announcement}), 200


@admin_bp.route("/reports/issues", methods=["GET"], strict_slashes=False)
@admin_required
def get_issues():
    """get all reported isssues"""
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

    issues = [
        dict(clean(issue.to_dict()), sent_at=issue.created_at)
        for issue in paginate(
            storage.get_objs(
                "Notification",
                notification_type="issue",
                receiver_id=user_id,
            ),
            column.type,
            column,
        )
    ]
    return jsonify({"issues": issues}), 200


@admin_bp.route("/reports/issues/<issue_id>", methods=["GET"], strict_slashes=False)
@admin_required
def get_issue(issue_id):
    """get reported issue by provided issue-id"""
    issue = storage.get("Notification", id=issue_id)
    if not issue:
        logger.warning("issue not found")
        return jsonify({"notification": "issue not found"}), 404
    try:
        storage.update(
            "Notification", id=issue_id, is_read=True, read_at=datetime.utcnow()
        )
    except:
        logger.exception("An internal error")
        abort(500)

    issue = issue.to_dict()

    issue["sent_at"] = issue["created_at"]
    try:
        issue["sender_id"] = clean(
            storage.get(issue["sender_type"], id=issue["sender_id"]).to_dict()
        )
    except:
        logger.exception("An internal error")
        abort(500)
    issue = clean(issue)
    return jsonify({"issue": issue}), 200


# System Configuration
@admin_bp.route("/notification", methods=["POST"], strict_slashes=False)
@admin_required
def notification():
    """set a notification by provided information"""
    try:
        user_id = request.user_id
    except:
        logger.exception("An internal error")
        abort(500)

    try:
        data = request.get_json()
    except Exception as e:
        logger.warning(e)
        abort(415)

    if "massage" not in data:
        logger.warning("message missing")
        return jsonify({"error": "massage missing"}), 400
    if "notification_type" not in data:
        logger.warning("notification_type missing")
        return jsonify({"error": "notification_type missing"}), 400
    if "to" not in data:
        logger.warning("to missing")
        return jsonify({"error": "to missing"}), 400

    if data["to"] == "all":
        receivers = [
            rider
            for rider in storage.get_objs("Rider")
            if not rider.deleted and not rider.blocked
        ] + [
            driver
            for driver in storage.get_objs("Driver")
            if not driver.deleted and not driver.blocked
        ]
    elif data["to"] in ["Driver", "Rider", "Admin"]:
        receivers = [
            user
            for user in storage.get_objs(data["to"])
            if not user.deleted and not user.blocked
        ]
    else:
        receivers = []
        for i in ["Admin", "Rider", "Driver"]:
            if storage.get(i, id=data["to"]):
                receivers.append(storage.get(i, id=data["to"]))
                break
    for user in receivers:
        kwargs = {
            "sender_id": user_id,
            "sender_type": "Admin",
            "receiver_id": user.id,
            "receiver_type": user.__class__.__name__,
            "message": data["message"],
            "notification_type": data["notification_type"],
        }
        try:
            notification = Notification(**kwargs)
            notification.save()
        except:
            logger.exception("An internal error")
            abort(500)
    return jsonify({"admin": "sent"}), 200
