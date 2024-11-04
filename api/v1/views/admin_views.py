from models import storage
from api.v1.middleware import admin_required, superadmin_required
from api.v1.views import admin_bp
from flask import jsonify, request, abort
from auth import authentication
from auth.authentication import clean
from models.rider import Rider
from models.driver import Driver
from models.trip import Trip
from models.location import Location
from datetime import datetime
from models.notification import Notification

Auth = authentication.Auth()
cls = 'Admin'
admin_key = [
            'email', 'username', 'first_name',
            'last_name', 'phone_number', 'password_hash',
            'admin_level'
            ]


#Admin Authentication
@admin_bp.route('/admin-register', methods=['POST'], strict_slashes=False)
@superadmin_required
def register():
    try:
        user_data = request.get_json()
    except:
        abort(415)

    for k in admin_key:
        if k not in user_data.keys():
            return jsonify({'error': f'{k} missing'}), 400
    try:
        int(user_data['phone_number'])
    except:
        return jsonify({'error': 'phone_number must be number'}), 400
    try:
        user = Auth.register_user(cls, **user_data)
        message, status = user
    except:
        abort(500)
    if status:
        return jsonify({'user': message}), 201
    return jsonify({'error': message}), 400


@admin_bp.route('/login', methods=['POST'], strict_slashes=False)
def login():
    try:
        user_data = request.get_json()
    except:
        abort(415)

    if 'email' not in user_data:
        return jsonify({'error': 'email missing'}), 400
    if 'password_hash' not in user_data:
        return jsonify({'error': 'password missing'}), 400
    try:
        user = Auth.verify_login(cls, user_data['email'], user_data['password_hash'])
        message, status = user
    except:
        abort(500)

    if status:
        return jsonify({'user': status}), 200
    
    return jsonify({'error': message}), 400

@admin_bp.route('/logout', methods=['POST'], strict_slashes=False)
@admin_required
def logout():
    return jsonify({'admin':'Logged out'})

#Rider And Driver Management
@admin_bp.route('/riders', methods=['GET'], strict_slashes=False)
@admin_required
def get_riders():
    riders = [clean(v.to_dict()) for v in storage.get_objs("Rider") if not v.deleted and not v.blocked]
    return jsonify({'riders': riders}), 200

@admin_bp.route('/drivers', methods=['GET'], strict_slashes=False)
@admin_required
def get_drivers():
    drivers = [clean(v.to_dict()) for v in storage.get_objs("Driver") if not v.deleted and not v.blocked]
    return jsonify({'drivers': drivers}), 200

@admin_bp.route('/block-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def block_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def unblock_admin():
                        try:
                            storage.update(cls, user_id, blocked=True)
                        except:
                            abort(500)
                    unblock_admin()
                else:
                    try:
                        storage.update(cls, user_id, blocked=True)
                    except:
                        abort(500)
                cls_ = cls
                break
            except:
                return jsonify({'error': f'Unable to block {cls}'}), 400
        else:
            return jsonify({'user': f'{cls} already blocked'}), 200
    if not cls_:
        return jsonify({'user': 'user not found'}), 404
    return jsonify({'user': f'{cls_} blocked'}), 200

@admin_bp.route('/unblock-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def unblock_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id):
            continue
        if storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def unblock_admin():
                        try:
                            storage.update(cls, user_id, blocked=False)
                        except:
                            abort(500)
                    unblock_admin()
                else:
                    try:
                        storage.update(cls, user_id, blocked=False)
                    except:
                        abort(500)
                cls_ = cls
                break
            except:
                return jsonify({'error': f'Unable to unblock {cls}'}), 400
        else:
            return jsonify({'user': f'{cls} already unblocked'}), 200
    if not cls_:
        return jsonify({'user': 'user not found'}), 404
    return jsonify({'user': f'{cls_} unblocked'}), 200

@admin_bp.route('/delete-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def delete_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def delete_admin():
                        try:
                            storage.update(cls, user_id, deleted=True)
                        except:
                            abort(500)
                    delete_admin()
                else:
                    try:
                        storage.update(cls, user_id, deleted=True)
                    except:
                        abort(500)
                cls_ = cls
                break
            except:
                return jsonify({'error': f'Unable to delete {cls}'}), 400
        else:
            return jsonify({'user': f'{cls} already deleted'}), 200
    if not cls_:
        return jsonify({'user': 'user not found'}), 404
    return jsonify({'user': f'{cls_} deleted'}), 200

@admin_bp.route('/revalidate-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def revalidate_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id):
            continue
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def delete_admin():
                        try:
                            storage.update(cls, user_id, deleted=False)
                        except:
                            abort(500)
                    delete_admin()
                else:
                    try:
                        storage.update(cls, user_id, deleted=False)
                    except:
                        abort(500)
                cls_ = cls
                break
            except:
                return jsonify({'error': f'Unable to revalidate {cls}'}), 400
        else:
            return jsonify({'user': f'{cls} already revalidated'}), 200
    if not cls_:
        return jsonify({'user': 'user not found'}), 404
    return jsonify({'user': f'{cls_} revalidated'}), 200

@admin_bp.route('/deleted-users/<user_type>', methods=['GET'], strict_slashes=False)
@admin_required
def deleted_users(user_type):
    users = [clean(v.to_dict()) for v in storage.get_objs(user_type) if v.deleted]
    return jsonify({'users': users}), 200 

@admin_bp.route('/blocked-users/<user_type>', methods=['GET'], strict_slashes=False)
@admin_required
def blocked_users(user_type):
    users = [clean(v.to_dict()) for v in storage.get_objs(user_type) if v.blocked]
    return jsonify({'users': users}), 200

@admin_bp.route('/user-profile/<user_id>', methods=['GET'], strict_slashes=False)
@admin_required
def user_profile(user_id):
    user = ''
    for i in ['Rider', 'Driver', 'Admin']:
        if storage.get(i, id=user_id):
            user = clean(storage.get(i, id=user_id).to_dict())
    if user:
        return jsonify({'user': user}), 200
    return jsonify({'error': 'user not found'}), 404

#Ride Management
@admin_bp.route('/get-rides', methods=['GET'], strict_slashes=False)
@admin_required
def get_rides():
    trips = storage.get_objs('Trip')
    if not trips:
        return jsonify({'error': 'trip found'}), 404
    trips_dict = {}
    try:
        for trip in trips:
            vehicle = storage.get('Driver', id=trip.driver_id).vehicle
            riders = [rider.rider for rider in storage.get_objs('TripRider', trip_id=trip.id, is_past=False)]
            available_seats = vehicle.seating_capacity - len(riders)
            trips_dict['Trip.' + trip.id] = clean(trip.to_dict())
            trips_dict['Trip.' + trip.id]['vehicle_holds'] = vehicle.seating_capacity
            trips_dict['Trip.' + trip.id]['available_seats'] = available_seats

            trips_dict['Trip.' + trip.id]['driver_id'] = clean(storage.get('Driver', id=trips_dict['Trip.' + trip.id]['driver_id']).to_dict())
            trips_dict['Trip.' + trip.id]['pickup_location_id'] = clean(storage.get('Location', id=trips_dict['Trip.' + trip.id]['pickup_location_id']).to_dict())
            trips_dict['Trip.' + trip.id]['dropoff_location_id'] = clean(storage.get('Location', id=trips_dict['Trip.' + trip.id]['dropoff_location_id']).to_dict())
            trips_dict['Trip.' + trip.id]['vehicle'] = clean(storage.get('Vehicle', driver_id=trip.driver_id).to_dict())
            
            del trips_dict['Trip.' + trip.id]['status']
    except:
        abort(500)

    return jsonify({'trips': trips_dict}), 200
   

@admin_bp.route('/get-ride/<ride_id>', methods=['GET'], strict_slashes=False)
@admin_required
def get_ride(ride_id):
    booked_riders = []
    canceled_riders = []
    payment = None

    try:
        ride = clean(storage.get('Trip', id=ride_id).to_dict())
        if not ride:
            abort(404)
        try:
            booked_riders = [clean(rider.rider.to_dict()) for rider in storage.get_objs('TripRider', trip_id=ride_id) if rider.status == 'booked']
        except:
            booked_riders = None
        try:
            canceled_riders = [clean(rider.rider.to_dict()) for rider in storage.get_objs('TripRider', trip_id=ride_id) if rider.status == 'Canceled']
        except:
            canceled_riders = None
        try:
            payment = clean(storage.get("Payment", trip_id=ride_id).to_dict())
        except:
            payment = None
    except:
        return jsonify({'ride': 'ride not found'}), 404
    ride["riders"] = {'booked': booked_riders,
                      'canceled': canceled_riders}
    ride["payment"] = payment

    return jsonify({'ride': ride}), 200

@admin_bp.route('/delete-ride/<ride_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def delete_ride(ride_id):
    try:
        storage.update('Trip', ride_id, is_available=False)
    except:
        abort(500)
    return jsonify({'admin': 'Ride deleted'}), 200


@admin_bp.route('/set-location', methods=['POST'], strict_slashes=False)
@admin_required
def set_location():
    try:
        location_data = request.get_json()
    except:
        abort(415)
    for i in ['latitude', 'longitude', 'address']:
        if i not in location_data:
            return jsonify({'error': f'{i} missing'}), 400
    kwargs = {
        'latitude': location_data['latitude'],
        'longitude': location_data['longitude'],
        'address': location_data['address'],    
    }
    try:
        location = Location(**kwargs)
        location.save()
    except:
        abort(500)
    return jsonify({'location': 'location created'}), 200

@admin_bp.route('/get-locations', methods=['GET'], strict_slashes=False)
@admin_required
def get_locations():
    locations = [clean(location.to_dict()) for location in storage.get_objs('Location')]
    if not locations:
        return jsonify({'error': 'location not found'}), 404
    return jsonify({'locations': locations}), 200

@admin_bp.route('/set-ride', methods=['POST'], strict_slashes=False)
@admin_required
def set_ride():
    '''create a ride'''
    try:
        ride_data = request.get_json()
    except:
        abort(415)
    args = ['driver_id', 'pickup_location_id', 'dropoff_location_id',
            'pickup_time', 'dropoff_time', 'fare', 'distance', 'status',
            'is_available']
    for i in args:
        if i not in ride_data:
            return jsonify({'error': f'{i} missing'}), 400
    
    kwargs = {
        "driver_id": ride_data['driver_id'],
        "pickup_location_id": ride_data['pickup_location_id'],
        "dropoff_location_id": ride_data['dropoff_location_id'],
        "pickup_time": ride_data['pickup_time'],
        "dropoff_time": ride_data['dropoff_time'],
        "fare": ride_data['fare'],
        "distance": ride_data['distance'],
        "status": ride_data['status'],
        "is_available": ride_data['is_available']
    }
    try:
        trip = Trip(**kwargs)
        trip.save()
    except:
        abort(500)
    
    return jsonify({'ride': 'ride created'}), 200


#Payment Management
@admin_bp.route('/transactions', methods=['GET'], strict_slashes=False)
@admin_required
def get_transactions():
    try:
        transactions = sorted([clean(transaction.to_dict()) for transaction in storage.get_objs('Payment')], key=lambda transaction: transaction['payment_time'], reverse=True)
    except:
        abort(500)
    if transactions:
        return jsonify({'admin': transactions}), 200
    return jsonify({'admin': "Transactions not found"}), 404

@admin_bp.route('/payment-detail/<ride_id>', methods=['GET'], strict_slashes=False)
@admin_required
def get_payment_detail(ride_id):
    trip = storage.get("Trip", id=ride_id)
    if not trip:
        return jsonify({'error': 'ride not found'}), 404

    trip_dict = clean(trip.to_dict())
    total_amount = 0
    try:
        riders = [rider.rider for rider in storage.get("Trip", id=ride_id).riders]
    except:
        abort(500)

    for py in riders:
        if py.payment:
            total_amount += py.payment[0].amount
    
    riders_dict = [clean(ride.to_dict()) for ride in riders]
    for ride in riders_dict:
        if ride['payment']:
            ride['payment'] = clean(ride['payment'][0].to_dict())
    try:
        payment_status = [payment.payment_status for payment in storage.get("Trip", id=ride_id).payment]
        number_of_riders = len([rider for rider in storage.get("Trip", id=ride_id).riders])
    except:
        abort(500)

    payment_dict = {
        "trip": trip_dict,
        "total_paid_amount": total_amount,
        "payment_status": payment_status,
        "number_of_riders": number_of_riders,
        "riders": riders_dict
    }
 

    return jsonify({'payment': payment_dict}), 200


# @admin_bp.route('/refund/<ride_id>', methods=['POST'], strict_slashes=False)
# @admin_required
# def refund(ride_id):
#     return jsonify({'Admin': 'Issue a refund to a rider'})

#Reports And Analytics
@admin_bp.route('/reports/earnings', methods=['GET'], strict_slashes=False)
@admin_required
def get_earnings():
    return jsonify({'Admin': 'Return earnings of the drivers and the platform'})

@admin_bp.route('/reports/ride-activity', methods=['GET'], strict_slashes=False)
@admin_required
def get_ride_activity():
    return jsonify({'Admin': 'Return ride activity(number of rides, cancellations...)'})

@admin_bp.route('/reports/issues', methods=['GET'], strict_slashes=False)
@admin_required
def get_issues():
    return jsonify({'Admin': 'Return report of issues reported by riders and drivers'})

#System Configuration
# @admin_bp.route('/set-pricing', methods=['PUT'], strict_slashes=False)
# @admin_required
# def set_pricing():
#     return jsonify({'Admin': 'Update ride pricing and fare structure'})

@admin_bp.route('/set-commission', methods=['POST'], strict_slashes=False)
@admin_required
def set_commission():
    return jsonify({'Admin': 'Set commission percentage for drivers'})

@admin_bp.route('/notification', methods=['POST'], strict_slashes=False)
@admin_required
def notification():
    return jsonify({'Admin': 'send notification or announcements to all riders and drivers'})