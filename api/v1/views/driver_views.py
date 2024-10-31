from api.v1.views import driver_bp
from flask import jsonify, request, abort
from auth import authentication
from auth.authentication import _hash_password, clean
from api.v1.middleware import token_required
from models import storage
from collections import OrderedDict


Auth = authentication.Auth()

driver_key = ['username', 'first_name',
             'last_name', 'email',
             'phone_number', 'password_hash',
             'payment_method']
cls = 'Driver'


#Registration And Authentication
@driver_bp.route('/register', methods=['POST'], strict_slashes=False)
def register():
    try:
        user_data = request.get_json()
    except:
        abort(415)

    for k in driver_key:
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


@driver_bp.route('/login', methods=['POST'], strict_slashes=False)
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


@driver_bp.route('/logout', methods=['POST'], strict_slashes=False)
@token_required
def logout():
    return jsonify({'User': 'Logged out'})

#Profile Management
@driver_bp.route('/reset-token', methods=['POST'], strict_slashes=False)
def get_reset_token():
    '''token is sent to phone number or email'''
    try:
        user_data = request.get_json()
    except:
        abort(415)
    
    if 'email' in user_data:
        user = storage.get(cls, email=user_data['email'])
        if user:
            reset_token = Auth.create_reset_token(cls, user_data['email'])
            return jsonify({'reset_token': reset_token}), 201
        else:
            abort(404)
    else:
        return jsonify({'error': 'email not given'}), 400

@driver_bp.route('/forget-password', methods=['POST'], strict_slashes=False)
def forget_password():
    '''update password using reset token'''
    try:
        user_data = request.get_json()
    except:
        abort(415)

    if 'password_hash' not in user_data:
        return jsonify({'error': 'password not provided'}), 400
    if 'reset_token' in user_data:
        try:
            update_password = Auth.update_password(cls, user_data['reset_token'], user_data['password_hash'])
        except:
            abort(500)

        if update_password:
            return jsonify({'update': 'Successful'}), 200
        else:
            return jsonify({'update': 'incorrect token'}), 400
    else:
        return jsonify({'error': 'reset token not provided'}), 400


@driver_bp.route('/profile', methods=['GET'], strict_slashes=False)
@token_required
def get_profile():
    try:
        user_id = request.user_id
    except:
        abort(500)
    user = clean(storage.get(cls, id=user_id).to_dict())
    if user:
        return jsonify({'user': user}), 200
    abort(404)

@driver_bp.route('/profile', methods=['PUT'], strict_slashes=False)
@token_required
def put_profile():
    '''updates profile and password'''
    try:
        user_id = request.user_id
    except:
        abort(500)
    
    try:
        user_data = request.get_json()
    except:
        abort(415)

    unmutables_by_user = ['email', 'phone_number', 'reset_token']
    user = storage.get_in_dict(cls, id=user_id)
    updates = {}
    if user:
        for k in user_data.keys():
            if k not in unmutables_by_user:
                updates[k] = user_data[k]

        if 'password_hash' in updates:
            if 'old_password' in updates:
                user_password = storage.get(cls, id=user_id)
                if not user_password:
                    abort(404)
                check_password = Auth.verify_password(updates['old_password'], user_password)
                if check_password:
                    updates['password_hash'] = _hash_password(updates['password_hash'])
                    del updates['old_password']
                else:
                    return jsonify({'error': 'old password incorrect'}), 400
            else:
                return jsonify({'error': 'old_password missing'}), 400
        else:
            return jsonify({'error': 'password_hash missing'}), 400   
        try:
            storage.update(cls, id=user_id, **updates)
        except:
            return jsonify({'error': 'Update Failed'}), 500
    else:
        abort(404)
    return jsonify({'user': 'updated Successfuly'}), 200

#Ride Management
@driver_bp.route('/availability', methods=['GET'], strict_slashes=False)
@token_required
def availability():
    '''driver's availability online/offline'''
    try:
        user_id = request.user_id
    except:
        abort(500)
    
    availability = clean(storage.get('Availability', driver_id=user_id).to_dict())
    
    if availability:
        return jsonify({'availability': availability}), 200
    abort(404)

@driver_bp.route('/ride-plans', methods=['GET'], strict_slashes=False)
@token_required
def ride_pans():
    '''current status of a driver usualy related to trips'''
    try:
        driver_id = request.user_id
    except:
        abort(500)
    driver_trips = []

    trips = storage.get_objs('Trip', driver_id=driver_id, is_available=True)
    
    if not trips:
        abort(404)

    sorted_trips = sorted(trips, key=lambda trip: trip.updated_at)
    
    for sorted_trip in sorted_trips:
        driver_trips.append(clean(sorted_trip.to_dict()))

    return jsonify({'rides': driver_trips}), 200


@driver_bp.route('/current-ride/<trip_id>', methods=['GET'], strict_slashes=False)
@token_required
def current_ride(trip_id):
    try:
        request.user_id
    except:
        abort(500)
    try:
        trip = clean(storage.get('Trip', id=trip_id).to_dict())
    except:
        abort(404)

    if not trip: 
        abort(404)

    if trip['driver_id'] != request.user_id:
        abort(400)

    tripriders = storage.get_objs('TripRider', trip_id=trip['id'], is_past=False)
    
    count = 0
    for _ in tripriders:
        count += 1

    trip['pickup_location_id'] = clean(storage.get('Location', id=trip['pickup_location_id']).to_dict())
    trip['dropoff_location_id'] = clean(storage.get('Location', id=trip['dropoff_location_id']).to_dict())
    del trip['driver_id']
    trip['number_of_passengers'] = count


    return jsonify({'ride': trip}), 200


@driver_bp.route('/ride-requests', methods=['GET'], strict_slashes=False)
@token_required
def ride_requests():
    '''view all incoming ride requests and currently onboard'''
    try:
        driver_id = request.user_id
    except:
        abort(500)
    
    riders = {}
    trips = storage.get_objs('Trip', driver_id=driver_id, is_available=True)
    trip_dict = {}

    if not trips:
        return jsonify({'rider': 'no requests found'}), 404

    for trip in trips:
        tripriders = storage.get_objs('TripRider', trip_id=trip.id, is_past=False)
        if not tripriders:
            abort(404)
        for triprider in tripriders:
            riders['Rider.' + triprider.rider.id] = clean(triprider.rider.to_dict())
            trip_dict['Trip.' + trip.id] =  riders
        riders = {}
 
    return jsonify({'riders': trip_dict}), 200


@driver_bp.route('/accept-ride', methods=['POST'], strict_slashes=False)
@token_required
def accept_ride():
    '''accept all ride from admin'''
    pass


@driver_bp.route('/start-ride', methods=['POST'], strict_slashes=False)
@token_required
def start_ride():
    '''mark start ride after pickup'''
    try:
        trip_id = request.get_json()
    except:
        abort(415)

    if ['trip_id'] not in trip_id:
        return jsonify({'error': 'trip_id missing'}), 400
    trip_id = trip_id['trip_id']
    try:
        storage.update('Trip', trip_id, status="Started")
    except:
        abort(500)
    
    return jsonify({'ride': 'Started'}), 200


@driver_bp.route('/end-ride', methods=['POST'], strict_slashes=False)
@token_required
def end_ride():
    '''mark ride as complete'''
    try:
        trip_id = request.get_json()
    except:
        abort(415)
    if ['trip_id'] not in trip_id:
        return jsonify({'error': 'trip_id missing'}), 400
    trip_id = trip_id['trip_id']

    tripriders = storage.get_objs('TripRider', trip_id=trip_id, is_past=False)
    if not tripriders:
        abort(404)
    for triprider in tripriders:
         try:
            storage.update('TripRider', triprider.id, status="Completed", status_by="Completed", is_past=True)
         except:
             abort(500)
    try:
        storage.update('Trip', trip_id, status="Completed", is_available=False)
    except:
        abort(500)
    return jsonify({'ride': 'Completed'}), 200

@driver_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''if needed'''
    try:
        trip_id = request.get_json()
    except:
        abort(415)
    if 'trip_id' not in trip_id:
        return jsonify({'error': 'trip_id missing'}), 400
    trip_id = trip_id['trip_id']

    tripriders = storage.get_objs('TripRider', trip_id=trip_id, is_past=False)
    trips = [trips for trips in tripriders]

    if not trips:
        abort(404)

    if not storage.get('Trip', id=trip_id):
        abort(404)
    for triprider in tripriders:
         try:
            storage.update('TripRider', triprider.id, status="Canceled", status_by="Driver", is_past=True)
         except:
             abort(500)
    try:
        storage.update('Trip', trip_id, status="Canceled", is_available=False)
    except:
        abort(500)
    
    return jsonify({'ride': 'Canceled'}), 200


#Ride History And Earning
@driver_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    trips = storage.get_objs('Trip', driver_id=request.user_id, is_available=False)
    
    trips_dict = {}
    
    for trip in trips:
        trips_dict['Trip.' + trip.id] = clean(trip.to_dict())

    return jsonify({'rides': trips_dict}), 200

@driver_bp.route('/earnings', methods=['GET'], strict_slashes=False)
@token_required
def earnings():
    '''show driver's earning daily, weekly, monthly'''
    pass
