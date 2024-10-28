from api.v1.views import driver_bp
from flask import jsonify, request
from auth import authentication
from auth.authentication import _hash_password
from api.v1.middleware import token_required
from models import storage
from collections import OrderedDict


Auth = authentication.Auth()

driver_key = ['username', 'first_name',
             'last_name', 'email',
             'phone_number', 'password_hash']
cls = 'Driver'


#Registration And Authentication
@driver_bp.route('/register', methods=['POST'], strict_slashes=False)
def register():
    user_data = request.get_json()

    for k in driver_key:
        if k not in user_data.keys():
            return jsonify({'Error': f'{k} missing'})
    
    user = Auth.register_user(cls, **user_data)
    message, status = user

    if status:
        return jsonify({'User': message})
    return jsonify({'Error': message})


@driver_bp.route('/login', methods=['POST'], strict_slashes=False)
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


@driver_bp.route('/logout', methods=['POST'], strict_slashes=False)
@token_required
def logout():
    return jsonify({'User': 'Logged out'})

#Profile Management
@driver_bp.route('/reset-token', methods=['POST'], strict_slashes=False)
def get_reset_token():
    '''token is sent to phone number or email'''
    user_data = request.get_json()
    if 'email' in user_data:
        user = storage.get(cls, email=user_data['email'])
        if user:
            reset_token = Auth.create_reset_token(cls, user_data['email'])
            return jsonify({'reset_token': reset_token})
        else:
            return jsonify({'User': 'Not found'})
    else:
        return jsonify({'Error': 'email not given'})

@driver_bp.route('/forget-password', methods=['POST'], strict_slashes=False)
def forget_password():
    '''update password using reset token'''
    user_data = request.get_json()
    if 'password_hash' not in user_data:
        return jsonify({'Error': 'password not provided'})
    if 'reset_token' in user_data:
        update_password = Auth.update_password(cls, user_data['reset_token'], user_data['password_hash'])
        if update_password:
            return jsonify({'Update': 'Successful'})
        else:
            return jsonify({'Update': 'Failed'})
    else:
        return jsonify({'Error': 'reset token not provided'})


@driver_bp.route('/profile', methods=['GET'], strict_slashes=False)
@token_required
def get_profile():
    user_id = request.user_id
    user = storage.get_in_dict(cls, id=user_id)
    if user:
        return jsonify({'User': user})
    return jsonify({'Error': 'User not found'})

@driver_bp.route('/profile', methods=['PUT'], strict_slashes=False)
@token_required
def put_profile():
    '''updates profile and password'''
    user_id = request.user_id
    user_data = request.get_json()

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
                check_password = Auth.verify_password(updates['old_password'], user_password)
                if check_password:
                    updates['password_hash'] = _hash_password(updates['password_hash'])
                    del updates['old_password']
                else:
                    return jsonify({'Error': 'password incorrect'})
            else:
                return jsonify({'Error': 'old_password missing'})       
        try:
            user_update = storage.update(cls, id=user_id, **updates)
        except Exception:
            return jsonify({'Error': 'Update Failed'})
        if user_update == False:
            return jsonify({'Error': 'username already exists or key not found'})

    return jsonify({'User': 'Updated Successfuly'})

#Ride Management
@driver_bp.route('/availability', methods=['GET'], strict_slashes=False)
@token_required
def availability():
    '''driver's availability online/offline'''
    user_id = request.user_id
    availability = storage.get_in_dict('Availability', driver_id=user_id)
    
    if availability:
        return jsonify({'Availability': availability})
    return jsonify({'Availability': 'availability not found'})

@driver_bp.route('/ride-plans', methods=['GET'], strict_slashes=False)
@token_required
def ride_pans():
    '''current status of a driver usualy related to trips'''
    driver_id =request.user_id
    driver_trips = []

    trips = storage.get_objs('Trip', driver_id=driver_id, is_available=True)
    
    if not trips:
        return jsonify({'Rides': 'no rides foung'})

    sorted_trips = sorted(trips, key=lambda trip: trip.updated_at)
    
    for sorted_trip in sorted_trips:
        driver_trips.append(sorted_trip.to_dict())

    return jsonify({'Rides': driver_trips})


@driver_bp.route('/current-ride/<trip_id>', methods=['GET'], strict_slashes=False)
@token_required
def current_ride(trip_id):
    trip = storage.get('Trip', id=trip_id).to_dict()

    if not trip or trip['driver_id'] != request.user_id:
        return jsonify({'Error': "trip not found"})
        
    tripriders = storage.get_objs('TripRider', trip_id=trip['id'], is_past=False)
    
    count = 0
    for triprider in tripriders:
        count += 1

    trip['pickup_location_id'] = storage.get('Location', id=trip['pickup_location_id']).to_dict()
    trip['dropoff_location_id'] = storage.get('Location', id=trip['dropoff_location_id']).to_dict()
    del trip['driver_id']
    trip['number_of_passengers'] = count


    return jsonify({'Ride': trip})


@driver_bp.route('/ride-requests', methods=['GET'], strict_slashes=False)
@token_required
def ride_requests():
    '''view all incoming ride requests and currently onboard'''
    driver_id =request.user_id
    riders = {}
    trips = storage.get_objs('Trip', driver_id=driver_id, is_available=True)
    trip_dict = {}

    if not trips:
        return jsonify({'Rider': 'no rider\'s request'})

    for trip in trips:
        tripriders = storage.get_objs('TripRider', trip_id=trip.id, is_past=False)
        for triprider in tripriders:
            riders['Rider.' + triprider.rider.id] = triprider.rider.to_dict()
            trip_dict['Trip.' + trip.id] =  riders
        riders = {}
 
    return jsonify({'Riders': trip_dict})


@driver_bp.route('/accept-ride', methods=['POST'], strict_slashes=False)
@token_required
def accept_ride():
    '''accept all ride from admin'''
    pass


@driver_bp.route('/start-ride', methods=['POST'], strict_slashes=False)
@token_required
def start_ride():
    '''mark start ride after pickup'''
    trip_id = request.get_json()
    if ['trip_id'] not in trip_id:
        return jsonify({'Error': 'trip_id missing'})
    trip_id = trip_id['trip_id']
    storage.update('Trip', trip_id, status="Started")
    
    return jsonify({'Ride': 'Started'})


@driver_bp.route('/end-ride', methods=['POST'], strict_slashes=False)
@token_required
def end_ride():
    '''mark ride as complete'''
    trip_id = request.get_json()
    if ['trip_id'] not in trip_id:
        return jsonify({'Error': 'trip_id missing'})
    trip_id = trip_id['trip_id']

    tripriders = storage.get_objs('TripRider', trip_id=trip_id, is_past=False)
    for triprider in tripriders:
         storage.update('TripRider', triprider.id, status="Completed", status_by="Completed", is_past=True)
    storage.update('Trip', trip_id, status="Completed", is_available=False)
    
    return jsonify({'Ride': 'Completed'})

@driver_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''if needed'''
    trip_id = request.get_json()
    if ['trip_id'] not in trip_id:
        return jsonify({'Error': 'trip_id missing'})
    trip_id = trip_id['trip_id']

    tripriders = storage.get_objs('TripRider', trip_id=trip_id, is_past=False)
    for triprider in tripriders:
         storage.update('TripRider', triprider.id, status="Canceled", status_by="Driver", is_past=True)
    storage.update('Trip', trip_id, status="Canceled", is_available=False)
    
    return jsonify({'Ride': 'Canceled'})


#Ride History And Earning
@driver_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    trips = storage.get_objs('Trip', driver_id=request.user_id, is_available=False)
    trips_dict = {}
    
    for trip in trips:
        trips_dict['Trip.' + trip.id] = trip.to_dict()

    return jsonify({'Rides': trips_dict})

@driver_bp.route('/earnings', methods=['GET'], strict_slashes=False)
@token_required
def earnings():
    '''show driver's earning daily, weekly, monthly'''
    pass
