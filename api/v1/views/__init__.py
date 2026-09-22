#!/usr/bin/python
from flask import Blueprint

admin_bp = Blueprint("admin_bp", __name__)
driver_bp = Blueprint("driver_bp", __name__)
rider_bp = Blueprint("rider_bp", __name__)
webhook_bp = Blueprint("webhook_bp", __name__)

from api.v1.views.admin_views import *  # noqa: E402, F403
from api.v1.views.driver_views import *  # noqa: E402, F403
from api.v1.views.rider_views import *  # noqa: E402, F403
from api.v1.views.webhook_views import *  # noqa: E402, F403
