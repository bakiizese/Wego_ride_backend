from functools import wraps
from flask import jsonify, request
import jwt

SECRET_KEY = 'wego_rider_service_secret_key'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'Error': 'Token is missing'}), 403
        
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user_id = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'Error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'Error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, 'role', None) != 'Admin':
            return jsonify({'Error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated