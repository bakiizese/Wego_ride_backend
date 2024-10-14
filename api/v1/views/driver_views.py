from api.v1.views import driver_bp
from flask import jsonify, request
from auth import authentication
from api.v1.middleware import token_required, admin_required
from models import storage

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
    return jsonify({'User': 'Update user profile'})

#Availabilty
@driver_bp.route('/availability', methods=['POST'], strict_slashes=False)
@token_required
def availability():
    '''driver's availability online/offline'''
    pass

@driver_bp.route('/current-status', methods=['GET'], strict_slashes=False)
@token_required
def current_status():
    '''current status of a driver usualy related to trips'''
    pass

#Ride Management
@driver_bp.route('/ride-requests', methods=['GET'], strict_slashes=False)
@token_required
def ride_requests():
    '''view all incoming ride requests and currently onboard'''
    pass

@driver_bp.route('/accept-ride', methods=['POST'], strict_slashes=False)
@token_required
def accept_ride():
    '''accept all ride request if space possible'''
    pass

@driver_bp.route('/start-ride', methods=['POST'], strict_slashes=False)
@token_required
def start_ride():
    '''mark start ride after pickup'''
    pass

@driver_bp.route('/end-ride', methods=['POST'], strict_slashes=False)
@token_required
def end_ride():
    '''mark ride as complete'''
    pass

@driver_bp.route('/cancel-ride', methods=['POST'], strict_slashes=False)
@token_required
def cancel_ride():
    '''if needed'''
    pass

#Ride History And Earning
@driver_bp.route('/ride-history', methods=['GET'], strict_slashes=False)
@token_required
def ride_history():
    pass

@driver_bp.route('/earnings', methods=['GET'], strict_slashes=False)
@token_required
def earnings():
    '''show driver's earning daily, weekly, monthly'''
    pass
