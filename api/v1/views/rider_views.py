from api.v1.views import rider_bp
from flask import jsonify, request
from auth import authentication
from auth.authentication import _hash_password
from models import storage
from api.v1.middleware import token_required, admin_required
from models.trip import Trip
from models.trip_rider import TripRider

Auth = authentication.Auth()

rider_key = ['username', 'first_name',
             'last_name', 'email',
             'phone_number', 'password_hash']
cls = 'Rider'


#Registation And Authentication
@rider_bp.route('/register', methods=['POST'], strict_slashes=False)
def register():
    user_data = request.get_json()
    
    for k in rider_key:
        if k not in user_data.keys():
            return jsonify({'Error': f'{k} missing'})

    user = Auth.register_user(cls, **user_data)
    message, status = user
        
    if status:
        return jsonify({'User': message})
    return jsonify({'Error': message})


@rider_bp.route('/login', methods=['POST'], strict_slashes=False)
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

    return jsonify({'User': message})


@rider_bp.route('/logout', methods=['POST'], strict_slashes=False)
@token_required
def logout():
    return jsonify({'User': 'Logged out'})


#Profile Management
@rider_bp.route('/forget-password', methods=['POST'], strict_slashes=False)
def forget_password():
    user_data = request.get_json()
    if 'email' in user_data:
        user = storage.get(cls, email=user_data['email'])
        if user:
            reset_token = Auth.create_reset_token(cls, user_data['email'])
            update_password = Auth.update_password(cls, reset_token, 'password')
            if update_password:
                return jsonify({'Update': 'Successful'})
            else:
                return jsonify({'Update': 'Failed'})
        else:
            return jsonify({'User': 'Not found'})
    else:
        return jsonify({'Error': 'email not given'})
    

@rider_bp.route('/profile', methods=['GET'], strict_slashes=False)
@token_required
def get_profile():
    user_id = request.user_id
    user = storage.get_in_dict(cls, id=user_id)
    if user:
        return jsonify({'User': user})
    return jsonify({'Error': 'User not found'})

@rider_bp.route('/profile', methods=['PUT'], strict_slashes=False)
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



#Ride Booking
@rider_bp.route('/available-rides', methods=['GET'], strict_slashes=False)
@token_required
def available_rides():
    trips = storage.get_all(Trip, is_available=True)
    for trip in trips:
        trips[trip] = trips[trip].to_dict()
    if trips:
        return jsonify({'Trips': trips})
    return jsonify({'Error': 'no trips found'})

@rider_bp.route('/book-ride', methods=['POST'], strict_slashes=False)
@token_required
def book_ride():
    '''book a ride by provideing trip id'''
    rider_id = request.user_id
    ride_data = request.get_json()
    trip_id = ride_data['trip_id']
    trip = storage.get("Trip", id=trip_id)
    
    if rider_id in [rider.id for rider in trip.riders]:
        return jsonify({'Error': 'you have already booked a ride'})

    vehicles = trip.drivers.vehicle
    for vehicle in vehicles:
        seating_capacity = vehicle.seating_capacity
    number_of_passengers = 0
    
    for _ in trip.riders:
        number_of_passengers += 1

    if number_of_passengers >= seating_capacity:
        return jsonify({'Error': 'maximam seat capacity'})
    
    kwargs = {'trip_id': trip_id, 'rider_id': rider_id}
    try:
        book_ride = TripRider(**kwargs)
        book_ride.save()
    except:
        return jsonify({'Error': 'Unable to book'})

    return jsonify({'Ride': 'you have booked a ride'})
    

@rider_bp.route('/ride-estimate', methods=['GET'], strict_slashes=False)
@token_required
def ride_estimate():
    '''estmated fare, time, need to create google maps javascript api'''
    pass

@rider_bp.route('/booked-ride', methods=['GET'], strict_slashes=False)
@token_required
def booked_ride():
    '''show all booked-rides for the future'''
    rider_id = request.user_id
    rides = storage.get_objs('TripRider', rider_id=rider_id)
    
    trips = [ride.trip for ride in rides if not ride.is_past]

    rides_dict = {}

    for trip in trips:
        rides_dict[trip.id] = trip.to_dict()

    return jsonify({'Ride': rides_dict})

@rider_bp.route('/current-ride/<tripride_id>', methods=['GET'], strict_slashes=False)
@token_required
def current_ride(tripride_id):
    '''show current ride details'''

    trip = storage.get('TripRider', id=tripride_id).trip.to_dict()
    trip['pickup_location_id'] = next(iter(storage.get_in_dict('Location', id=trip['pickup_location_id']).values()))
    trip['dropoff_location_id'] = next(iter(storage.get_in_dict('Location', id=trip['dropoff_location_id']).values()))
    trip['driver_id'] = storage.get_in_dict('Driver', id=trip['driver_id'])

    return jsonify({'Ride': trip})


@rider_bp.route('/ride-status/<tripride_id>', methods=['GET'], strict_slashes=False)
@token_required
def ride_status(tripride_id):
    '''check details of ride request'''
    rider_id = request.user_id
    trip = storage.get('TripRider', id=tripride_id).trip
    vehicles = trip.drivers.vehicle
    number_of_passengers = 0
    for vehicle in vehicles:
        seating_capacity = vehicle.seating_capacity

    for _ in trip.riders:
        number_of_passengers += 1

    trip = trip.to_dict()

    pickup_location = next(iter(storage.get_in_dict('Location', id=trip['pickup_location_id']).values()))
    dropoff_location = next(iter(storage.get_in_dict('Location', id=trip['dropoff_location_id']).values()))
    seats_left = seating_capacity - number_of_passengers

    ride_status = {
            'pickup_location': pickup_location,
            'dropoff_location': dropoff_location,
            'pickup_time': trip['pickup_time'],
            'status': trip['status'],
            'seats_left': seats_left,
            'distance': trip['distance'],
            'fare': trip['fare']
        }

    return jsonify({'Ride': ride_status})



#Ride History And Management
@rider_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    '''get past trips'''
    rider_id = request.user_id
    rides = [ride.trip for ride in storage.get_objs('TripRider', rider_id=rider_id) if ride.trip.status in ['Completed', 'Canceled', 'Payment_Failed', 'Refunded', 'No Show']]
    
    ride_dict = {}

    for ride in rides:
        ride_dict[ride.id] = ride.to_dict()

    return jsonify({'Ride': ride_dict})


@rider_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''to cancel a ride'''
    trip_id = request.get_json()['trip_id']
    
    triprider = storage.get('TripRider', trip_id=trip_id)

    if triprider.rider_id == request.user_id:
        update_triprider = storage.update('TripRider', id=triprider.id, is_past=True)
        update_dict = {'status': 'Canceled'} # 'status_by': 'Canceled'}
        update_trip = storage.update('Trip', id=trip_id, **update_dict)

        return jsonify({'Trip': 'Canceled'})
    return jsonify({'Error': 'not found'})

#Payment
@rider_bp.route('/add-payment-method', methods=['POST'], strict_slashes=False)
@token_required
def add_payment_method():
    '''add payment methods'''
    pass

@rider_bp.route('/pay-ride', methods=['POST'], strict_slashes=False)
@token_required
def pay_ride():
    '''make payment for a completed trip'''
    pass

#Ratings And Feedback
@rider_bp.route('/rate-driver', methods=['POST'], strict_slashes=False)
@token_required
def rate_driver():
    pass

@rider_bp.route('/report-issue', methods=['POST'], strict_slashes=False)
@token_required
def report_issue():
    pass