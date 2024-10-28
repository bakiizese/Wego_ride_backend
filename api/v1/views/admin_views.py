from models import storage
from api.v1.middleware import admin_required, superadmin_required
from api.v1.views import admin_bp
from flask import jsonify, request
from auth import authentication
from models.rider import Rider
from models.driver import Driver
from models.trip import Trip
from collections import OrderedDict


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
    user_data = request.get_json()

    for k in admin_key:
        if k not in user_data.keys():
            return jsonify({'Error': f'{k} missing'})

    user = Auth.register_user(cls, **user_data)
    message, status = user

    if status:
        return jsonify({'User': message})
    return jsonify({'Error': message})


@admin_bp.route('/login', methods=['POST'], strict_slashes=False)
def login():
    user_data = request.get_json()

    if 'email' not in user_data:
        return jsonify({'Error': 'email missing'})
    if 'password_hash' not in user_data:
        return jsonify({'Error': 'password missing'})
    
    user = Auth.verify_login(cls, user_data['email'], user_data['password_hash'])
    message, status = user

    if status:
        return jsonify({'User': status})
    
    return jsonify({'Error': message})

@admin_bp.route('/logout', methods=['POST'], strict_slashes=False)
@admin_required
def logout():
    return jsonify({'Admin':'Logged out'})

#Rider And Driver Management
@admin_bp.route('/riders', methods=['GET'], strict_slashes=False)
@admin_required
def get_riders():
    riders = {k : v.to_dict() for k, v in storage.get_all("Rider").items() if v['deleted'] and v['blocked']}
    if riders:
        return jsonify({'Riders': riders})
    return jsonify({'Error': "riders not found"})

@admin_bp.route('/drivers', methods=['GET'], strict_slashes=False)
@admin_required
def get_drivers():
    drivers = {k : v.to_dict() for k, v in storage.get_all("Driver").items() if v['deleted'] and v['blocked']}
    if drivers:
        return jsonify({'Riders': drivers})
    return jsonify({'drivers': "drivers not found"})

@admin_bp.route('/block-user/:user_id', methods=['PUT'], strict_slashes=False)
@admin_required
def block_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def unblock_admin():
                        storage.update(cls, user_id, blocked=True)
                    unblock_admin()
                else:
                    storage.update(cls, user_id, blocked=True)
                cls_ = cls
                break
            except:
                return jsonify({'Error': f'Unable to block {cls}'})
        else:
            return jsonify({'User': f'{cls} already blocked'})

    return jsonify({'User': f'{cls_} blocked'})

@admin_bp.route('/unblock-user/:user_id', methods=['PUT'], strict_slashes=False)
@admin_required
def unblock_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def unblock_admin():
                        storage.update(cls, user_id, blocked=False)
                    unblock_admin()
                else:
                    storage.update(cls, user_id, blocked=False)
                cls_ = cls
                break
            except:
                return jsonify({'Error': f'Unable to unblock {cls}'})
        else:
            return jsonify({'User': f'{cls} already unblocked'})

    return jsonify({'User': f'{cls_} unblocked'})

@admin_bp.route('/delete-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def delete_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if not storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def delete_admin():
                        storage.update(cls, user_id, deleted=True)
                    delete_admin()
                else:
                    storage.update(cls, user_id, deleted=True)
                cls_ = cls
                break
            except:
                return jsonify({'Error': f'Unable to delete {cls}'})
        else:
            return jsonify({'User': f'{cls} already deleted'})

    return jsonify({'User': f'{cls_} deleted'})

@admin_bp.route('/revalidate-user/<user_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def revalidate_user(user_id):
    cls_ = ''
    for cls in ['Driver', 'Rider', 'Admin']:
        if storage.get(cls, id=user_id).blocked:
            try:
                if cls == 'admin':
                    @superadmin_required
                    def delete_admin():
                        storage.update(cls, user_id, deleted=False)
                    delete_admin()
                else:
                    storage.update(cls, user_id, deleted=False)
                cls_ = cls
                break
            except:
                return jsonify({'Error': f'Unable to delete {cls}'})
        else:
            return jsonify({'User': f'{cls} already deleted'})

    return jsonify({'User': f'{cls_} deleted'})

@admin_bp.route('/deleted-users/<user_type>', methods=['GET'], strict_slashes=False)
def deleted_users(user_type):
    users = {k : v.to_dict() for k, v in storage.get_all(user_type).items() if not v['deleted']}
    if users:
        return jsonify({'Users': users})
    return jsonify({'Users': "Deleted users not found"})

@admin_bp.route('/blocked-users/<user_type>', methods=['GET'], strict_slashes=False)
def blocked_users(user_type):
    users = {k : v.to_dict() for k, v in storage.get_all(user_type).items() if not v['blocked']}
    if users:
        return jsonify({'Users': users})
    return jsonify({'users': "Deleted users not found"})


@admin_bp.route('/user-profile/<user_id>', methods=['GET'], strict_slashes=False)
@admin_required
def user_profile(user_id):
    user = ''
    for i in ['Rider', 'Driver', 'Admin']:
        if storage.get(i, id=user_id):
            user = storage.get(i, id=user_id).to_dict()
    if user:
        return jsonify({'User': user})
    return jsonify({'Error': 'user not found'})

#Ride Management
@admin_bp.route('/rides', methods=['GET'], strict_slashes=False)
@admin_required
def get_rides():
    rides = sorted([ride.to_dict() for ride in storage.get_objs("Trip")], key=lambda ride: ride['updated_at'], reverse=True)
    
    if rides: 
        return jsonify({'Rides': rides})
    return jsonify({'Error': 'rides not found'})

@admin_bp.route('/ride/<ride_id>', methods=['GET'], strict_slashes=False)
@admin_required
def get_ride(ride_id):
    try:
        ride = storage.get('Trip', id=ride_id).to_dict()
        try:
            booked_riders = [rider.rider.to_dict() for rider in storage.get_objs('TripRider', trip_id=ride_id) if rider.rider.status == 'booked']
        except:
            riders = None
        try:
            canceled_riders = [rider.rider.to_dict() for rider in storage.get_objs('TripRider', trip_id=ride_id) if rider.rider.status == 'canceled']
        except:
            riders = None
        try:
            payment = storage.get("Payment", trip_id=ride_id)
        except:
            payment = None
    except:
        return jsonify({'ride': 'ride not found'})
    ride["riders"] = {'booked': booked_riders,
                      'canceled': canceled_riders}
    ride["payment"] = payment
    return jsonify({'Ride': ride})

@admin_bp.route('/ride/<ride_id>', methods=['PUT'], strict_slashes=False)
@admin_required
def delete_ride(ride_id):
    try:
        storage.update('Trip', ride_id, is_available=False)
    except:
        return jsonify({'Error': 'Unable to delete ride'})
    return jsonify({'Admin': 'Ride deleted'})

@admin_bp.route('/set-ride', methods=['POST'], strict_slashes=False)
@admin_required
def set_ride():
    '''create a ride'''
    pass

#Payment Management
@admin_bp.route('/transactions', methods=['GET'], strict_slashes=False)
@admin_required
def get_transactions():
    transactions = sorted([transaction.to_dict() for transaction in storage.get_objs('Payment')], key=lambda transaction: transaction['payment_time'], reverse=True)
    if transactions:
        return jsonify({'Admin': transactions})
    return jsonify({'Admin': "Transactions not found"})

@admin_bp.route('/payment-detail/<ride_id>', methods=['GET'], strict_slashes=False)
@admin_required
def get_payment_detail(ride_id):
    trip = storage.get("Trip", id=ride_id)

    if not trip:
        return jsonify({'Error': 'ride not found'})

    trip_dict = trip.to_dict()
    total_amount = 0
    total_amount = [rider.rider.payment for rider in storage.get("Trip", id=ride_id).riders]
    # for _ in ride_amount:
    #     total_amount += _.amount
    
    payment_status = [payment.payment_status for payment in storage.get("Trip", id=ride_id).payment]
    number_of_riders = len([rider for rider in storage.get("Trip", id=ride_id).riders])
    riders = [rider.rider.to_dict() for rider in storage.get("Trip", id=ride_id).riders]
    
    payment_dict = {
        "trip": trip_dict,
        "total_paid_amount": total_amount,
        "payment_status": payment_status,
        "number_of_riders": number_of_riders,
        "riders": riders
    }
    # for i in total_amount[0]:
    #     print(i)
    print(type(total_amount[0]))

    return jsonify({'Payment': "payment_dict"})


@admin_bp.route('/refund/<ride_id>', methods=['POST'], strict_slashes=False)
@admin_required
def refund(ride_id):
    return jsonify({'Admin': 'Issue a refund to a rider'})

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
@admin_bp.route('/set-pricing', methods=['POST'], strict_slashes=False)
@admin_required
def set_pricing():
    return jsonify({'Admin': 'Update ride pricing and fare structure'})

@admin_bp.route('/set-commission', methods=['POST'], strict_slashes=False)
@admin_required
def set_commission():
    return jsonify({'Admin': 'Set commission percentage for drivers'})

@admin_bp.route('/notification', methods=['POST'], strict_slashes=False)
@admin_required
def notification():
    return jsonify({'Admin': 'send notification or announcements to all riders and drivers'})
