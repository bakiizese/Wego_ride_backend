from models import storage
from api.v1.middleware import admin_required
from api.v1.views import admin_bp
from flask import jsonify, request


#Admin Authentication
@admin_bp.route('/login', methods=['POST'], strict_slashes=False)
@admin_required
def login():
    return jsonify({'Admin': 'Logged in'})

@admin_bp.route('/logout', methods=['POST'], strict_slashes=False)
@admin_required
def logout():
    return jsonify({'Admin':'Logged out'})

#Rider And Driver Management
@admin_bp.route('/riders', methods=['GET'], strict_slashes=False)
@admin_required
def get_riders():
    return jsonify({'Admin': 'Return all riders'})

@admin_bp.route('/drivers', methods=['GET'], strict_slashes=False)
@admin_required
def get_drivers():
    return jsonify({'Admin': 'Return all drivers'})

@admin_bp.route('/block-user/:user_id', methods=['PUT'], strict_slashes=False)
@admin_required
def block_user(user_id):
    return jsonify({'Admin': 'Block user by user id'})

@admin_bp.route('/unblock-user/:user_id', methods=['PUT'], strict_slashes=False)
@admin_required
def unblock_user(user_id):
    return jsonify({'Admin': 'Unblock user by user id'})

@admin_bp.route('/delete-user/:user_id', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_user(user_id):
    return jsonify({'Admin': 'Delete user'})

@admin_bp.route('/user-profile/:user_id', methods=['GET'], strict_slashes=False)
@admin_required
def user_profile(user_id):
    return jsonify({'Admin': 'Get user profile'})

#Ride Management
@admin_bp.route('/rides', methods=['GET'], strict_slashes=False)
@admin_required
def get_rides():
    return jsonify({'Admin': 'Return all rides'})

@admin_bp.route('/ride/:ride_id', methods=['GET'], strict_slashes=False)
@admin_required
def get_ride(ride_id):
    return jsonify({'Admin': 'Return ride by ride id'})

@admin_bp.route('/ride/:ride_id', methods=['DELETE'], strict_slashes=False)
@admin_required
def delete_ride(ride_id):
    return jsonify({'Admin': 'Delete or flag a ride by ride id'})

#Payment Management
@admin_bp.route('/transactions', methods=['GET'], strict_slashes=False)
@admin_required
def get_transactions():
    return jsonify({'Admin': 'Return all transactions'})

@admin_bp.route('/payment-status/:ride_id', methods=['GET'], strict_slashes=False)
@admin_required
def get_payment_status(ride_id):
    return jsonify({'Admin': 'Return payment status for specific ride'})

@admin_bp.route('/refund/:ride_id', methods=['POST'], strict_slashes=False)
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
