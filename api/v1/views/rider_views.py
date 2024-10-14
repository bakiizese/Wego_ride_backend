from api.v1.views import rider_bp
from flask import jsonify, request
from auth import authentication
from auth.authentication import _hash_password
from models import storage
from api.v1.middleware import token_required, admin_required

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
@rider_bp.route('/book-ride', methods=['POST'], strict_slashes=False)
@token_required
def book_ride():
    '''book a ride by provideing pickup and dropoff location'''
    pass

@rider_bp.route('/ride-estimate', methods=['GET'], strict_slashes=False)
@token_required
def ride_estimate():
    '''estmated fare, time'''
    pass

@rider_bp.route('/current-ride', methods=['GET'], strict_slashes=False)
@token_required
def current_ride():
    '''show current ride  details'''
    pass

@rider_bp.route('/available-rides', methods=['GET'], strict_slashes=False)
@token_required
def available_rides():
    '''show all available rides includeing pickup, dropoff location and time and fare'''
    pass

@rider_bp.route('/ride-status', methods=['GET'], strict_slashes=False)
@token_required
def ride_status():
    '''check details of ride request'''
    pass

#Ride History And Management
@rider_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    '''get past trips'''
    pass

@rider_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''to cancel a ride'''
    pass

#Payment
@rider_bp.route('/add-payment-method', methods=['POST'], strict_slashes=False)
@token_required
def add_payment_method():
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