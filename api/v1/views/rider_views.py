from api.v1.views import rider_bp
from flask import jsonify, request
from auth import authentication

Auth = authentication.Auth()

rider_key = ['username', 'first_name',
             'last_name', 'email',
             'phone_number', 'password_hash']
cls = 'Rider'

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
def logout():
    return jsonify({'User': 'Logged out'})

@rider_bp.route('/profile', methods=['GET', 'PUT'], strict_slashes=False)
def get_put_profile():
    return jsonify({'User': 'Profile returned'})


