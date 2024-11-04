from api.v1.views import rider_bp
from flask import jsonify, request, abort
from auth import authentication
from auth.authentication import _hash_password, clean
from models import storage
from api.v1.middleware import token_required, admin_required
from models.trip import Trip
from models.trip_rider import TripRider
from models.payment import Payment
from datetime import datetime

Auth = authentication.Auth()

rider_key = ['username', 'first_name',
             'last_name', 'email',
             'phone_number', 'password_hash',
             'payment_method']
cls = 'Rider'


#Registation And Authentication
@rider_bp.route('/register', methods=['POST'], strict_slashes=False)
def register():
    try:
        user_data = request.get_json()
    except:
        return abort(415)

    for k in rider_key:
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
        return abort(500)
        
    if status:
        return jsonify({'user': message}), 201
    return jsonify({'error': message}), 400


@rider_bp.route('/login', methods=['POST'], strict_slashes=False)
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


@rider_bp.route('/logout', methods=['POST'], strict_slashes=False)
@token_required
def logout():
    return jsonify({'User': 'Logged out'})


#Profile Management
@rider_bp.route('/reset-token', methods=['POST'], strict_slashes=False)
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

@rider_bp.route('/forget-password', methods=['POST'], strict_slashes=False)
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
            return jsonify({'error': 'incorrect token'}), 400       
    else:
        return jsonify({'error': 'reset token not provided'}), 400

@rider_bp.route('/profile', methods=['GET'], strict_slashes=False)
@token_required
def get_profile():
    try:
        user_id = request.user_id
    except:
        abort(500)
    user = storage.get(cls, id=user_id).to_dict()
    user = clean(user)
    if user:
        return jsonify({'user': user}), 200
    return abort(404)

@rider_bp.route('/profile', methods=['PUT'], strict_slashes=False)
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
                    return jsonify({'error': 'password incorrect'}), 400
            else:
                return jsonify({'error': 'old_password missing'}), 400 
        else:
                return jsonify({'error': 'password_hash missing'}), 400 
        try:
            storage.update(cls, id=user_id, **updates)
        except:
            return jsonify({'error': 'update Failed'}), 500
    return jsonify({'user': 'Updated Successfuly'}), 200



#Ride Booking
@rider_bp.route('/available-rides', methods=['GET'], strict_slashes=False)
@token_required
def available_rides():
    trips = storage.get_objs('Trip', is_available=True)
    if not trips:
        abort(404)
    trips_dict = {}
    for trip in trips:
        try:
            vehicle = storage.get('Driver', id=trip.driver_id).vehicle
            riders = [rider.rider for rider in storage.get_objs('TripRider', trip_id=trip.id, is_past=False)]
            available_seats = vehicle.seating_capacity - len(riders)
            trips_dict['Trip.' + trip.id] = clean(trip.to_dict())
            trips_dict['Trip.' + trip.id]['vehicle_holds'] = vehicle.seating_capacity
            trips_dict['Trip.' + trip.id]['available_seats'] = available_seats

            trips_dict['Trip.' + trip.id]['driver_id'] = clean(storage.get('Driver', id=trips_dict['Trip.' + trip.id]['driver_id']).to_dict())
            trips_dict['Trip.' + trip.id]['pickup_location_id'] = clean(storage.get('Location', id=trips_dict['Trip.' + trip.id]['pickup_location_id']).to_dict())
            trips_dict['Trip.' + trip.id]['dropoff_location_id'] = clean(storage.get('Location', id=trips_dict['Trip.' + trip.id]['dropoff_location_id']).to_dict())
            
            del trips_dict['Trip.' + trip.id]['status']
        except:
            abort(500)
    if trips:
        return jsonify({'trips': trips_dict})
    abort(404)

@rider_bp.route('/book-ride', methods=['POST'], strict_slashes=False)
@token_required
def book_ride():
    '''book a ride by provideing trip id'''
    try:
        rider_id = request.user_id
    except:
        abort(500)
    try:
        ride_data = request.get_json()
    except:
        abort(415)

    if 'trip_id' not in ride_data:
        return jsonify({'error': 'trip_id missing'}), 400
    
    trip_id = ride_data['trip_id']

    trip = storage.get("Trip", id=trip_id)
    
    if not trip:
        abort(404)

    riders = []
    for rider in trip.riders:
        if rider.is_past == False:
            riders.append(rider.rider_id)
    
    if rider_id in riders:
        return jsonify({'error': 'you have already booked a ride'}), 200
    

    vehicle = trip.drivers.vehicle
    seating_capacity = vehicle.seating_capacity
    number_of_passengers = 0
    
    for _ in trip.riders:
        if _.status != 'Canceled':
            number_of_passengers += 1

    if number_of_passengers >= seating_capacity:
        return jsonify({'error': 'maximam seat capacity'}), 409
    
    riders_canceled = []
    for rider in trip.riders:
        if rider.status == "Canceled":
            riders_canceled.append(rider.rider_id)
    
    if rider_id in riders_canceled:
        trip_rider_id = storage.get('TripRider', trip_id=trip_id, rider_id=rider_id)
        if not trip_rider_id:
            abort(404)
        trip_rider_id = trip_rider_id.id
        try:
            storage.update('TripRider', trip_rider_id, is_past=False, status='booked')
        except:
            abort(500)
        return jsonify({'ride': 'you have booked a ride'}), 201

    kwargs = {'trip_id': trip_id, 'rider_id': rider_id}
    try:
        book_ride = TripRider(**kwargs)
        book_ride.save()
    except:
        abort(500)

    return jsonify({'ride': 'you have booked a ride'}), 201
    

@rider_bp.route('/ride-estimate', methods=['GET'], strict_slashes=False)
@token_required
def ride_estimate():
    '''estmated fare, time, need to create google maps javascript api'''
    pass

@rider_bp.route('/booked-ride', methods=['GET'], strict_slashes=False)
@token_required
def booked_ride():
    '''show all booked-rides for the future'''
    try:
        rider_id = request.user_id
    except:
        abort(500)
    rides = storage.get_objs('TripRider', rider_id=rider_id)
    
    if not rides:
        abort(404)

    trips = [ride for ride in rides if not ride.is_past]

    rides_dict = {}

    for trip in trips:
        rides_dict['Trip.' + trip.trip.id] = clean(trip.trip.to_dict())
        rides_dict['Trip.' + trip.trip.id]['trip_ride_id'] = trip.id

    return jsonify({'ride': rides_dict}), 200

@rider_bp.route('/current-ride/<tripride_id>', methods=['GET'], strict_slashes=False)
@token_required
def current_ride(tripride_id):
    '''show current ride details'''
    try:
        trip = clean(storage.get('TripRider', id=tripride_id, is_past=False).trip.to_dict())
    except:
        abort(404)

    if not trip:
        abort(404)

    trip['pickup_location_id'] = clean(next(iter(storage.get_in_dict('Location', id=trip['pickup_location_id']).values())))
    trip['dropoff_location_id'] = clean(next(iter(storage.get_in_dict('Location', id=trip['dropoff_location_id']).values())))
    trip['driver_id'] = clean(storage.get('Driver', id=trip['driver_id']).to_dict())

    return jsonify({'ride': trip}), 200

@rider_bp.route('/ride-status/<tripride_id>', methods=['GET'], strict_slashes=False)
@token_required
def ride_status(tripride_id):
    '''check details of ride request'''
    try:
        trip = storage.get('TripRider', id=tripride_id, is_past=False).trip
        vehicle = trip.drivers.vehicle
        seating_capacity = vehicle.seating_capacity
    except:
        abort(500)
    
    number_of_passengers = 0
    for _ in trip.riders:
        number_of_passengers += 1

    trip = trip.to_dict()

    pickup_location = clean(next(iter(storage.get_in_dict('Location', id=trip['pickup_location_id']).values())))
    dropoff_location = clean(next(iter(storage.get_in_dict('Location', id=trip['dropoff_location_id']).values())))
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

    return jsonify({'ride': ride_status}), 200

#Ride History And Management
@rider_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    '''get past trips'''
    try:
        rider_id = request.user_id
    except:
        abort(500)
    try:
        rides = [ride.trip for ride in storage.get_objs('TripRider', rider_id=rider_id, is_past=True) if ride.trip.status in ['Completed', 'Canceled', 'Payment_Failed', 'Refunded', 'No Show']]
    except:
        abort(404)
    ride_dict = {}

    for ride in rides:
        ride_dict['Trip.' + ride.id] = clean(ride.to_dict())

    return jsonify({'ride': ride_dict}), 200

@rider_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''to cancel a ride'''
    try:
        request.get_json()
    except:
        abort(415)

    if 'trip_id' not in request.get_json():
        abort(400)
    
    trip_id = request.get_json()['trip_id']
    triprider = storage.get('TripRider', trip_id=trip_id, rider_id=request.user_id)
    if not triprider:
        abort(404)
    triprider = triprider.id
    
    try:
        storage.update('TripRider', id=triprider, is_past=True, status="Canceled", status_by="rider")
    except:
        abort(500)

    return jsonify({'trip': 'Canceled'}), 200

#Payment
@rider_bp.route('/pay-ride', methods=['POST'], strict_slashes=False)
@token_required
def pay_ride():
    '''make payment for a completed trip'''
    try:
        request.get_json()
    except:
        abort(415)

    try:
        user_id = request.user_id
    except:
        abort(500)
    
    for i in ['amount', 'status', 'trip_id', 'payment_method']:
        if i not in request.get_json():
            abort(400)
    
    amount = request.get_json()['amount']
    trip_id = request.get_json()['trip_id']

    trip = storage.get('Trip', id=trip_id)
    if not trip:
        abort(404)
    if amount != trip.fare:
        return jsonify({'error': 'not the right amount'}), 400

    kwargs = {
        "trip_id": trip_id,
        "rider_id": user_id,
        "payment_method": request.get_json()['payment_method'],
        "payment_time": datetime.utcnow(),
        "amount": amount,
        "payment_status":  request.get_json()['status']
    }

    try:
        rider_payment = Payment(**kwargs)
        rider_payment.save()
    except:
        abort(500)
    
    return jsonify({'payment': 'paid'}), 201
        

#Ratings And Feedback
@rider_bp.route('/rate-driver', methods=['POST'], strict_slashes=False)
@token_required
def rate_driver():
    pass

@rider_bp.route('/report-issue', methods=['POST'], strict_slashes=False)
@token_required
def report_issue():
    pass