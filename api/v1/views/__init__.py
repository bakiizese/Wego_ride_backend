from flask import Blueprint

admin_bp = Blueprint('admin_bp', __name__)
driver_bp = Blueprint('driver_bp', __name__)
rider_bp = Blueprint('rider_bp', __name__)

from api.v1.views.admin_views import *
from api.v1.views.driver_views import *
from api.v1.views.rider_views import *