from functools import wraps
from flask import jsonify, request, abort
import jwt
from models import storage
from datetime import datetime

SECRET_KEY = 'wego_rider_service_secret_key'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return abort(400)
        
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            if data['role'] == 'Admin':
                user = storage.get(data['role'], id=data['sub'])
                if user:
                    if user.blocked or user.deleted:
                        abort(403)
    
            if data['role'] in ['Rider', 'Driver']:
                user = storage.get(data['role'], id=data['sub'])
                if not user:
                    abort(404)
                if user.deleted:
                    abort(403)
                if user.blocked:
                    if request.endpoint.split('.')[1] not in ['get_profile', 'put_profile', 'ride_history']:
                        abort(403)
                
            request.user_id = data['sub']
            request.role = data['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        if data['role'] == 'Driver':
            availability = storage.get('Availability', driver_id=data['sub']).id
            storage.update('Availability', availability, last_active_time=datetime.utcnow())

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, 'role', None) != 'Admin':
            g = getattr(request, 'role', None)
            return jsonify({'Error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def superadmin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'Error': 'Token is missing'}), 400
        
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            if data['role'] == "Admin":
                user_id = data['sub']
                user = storage.get('Admin', id=user_id)
                if not user.admin_level == "superadmin":
                    return jsonify({'Error': 'only superadmin allowed'}), 403
            else:
                return jsonify({'Error': 'only admin allowed'}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'Error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'Error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated