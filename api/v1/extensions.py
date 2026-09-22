#!/usr/bin/python
"""Flask extension instances shared across blueprints. Created here
(uninitialized) so view modules can import + decorate with them, then
wired to the app inside create_app()."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    # if Redis is briefly unreachable, degrade to in-memory limits rather
    # than taking every endpoint down with it
    in_memory_fallback_enabled=True,
)

socketio = SocketIO()
