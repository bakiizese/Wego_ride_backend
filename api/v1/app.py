#!/usr/bin/python
from flask import Flask, jsonify
from flasgger import Swagger
import logging
from flask_cors import CORS
import redis

from config import settings
from api.v1.extensions import limiter, socketio

logging.basicConfig(
    # filename="./logs/error.log",
    level=logging.WARNING,
    format="%(asctime)s:%(name)s:%(levelname)s:%(message)s",
)


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length_mb * 1024 * 1024
    # Flask-SocketIO's per-connection session support (used to remember a
    # socket's authenticated user_id/role between the `connect` and `join`
    # events) is built on Flask's own signed session, so it needs a key
    # even though nothing else in the app uses cookie-based sessions.
    app.config["SECRET_KEY"] = settings.secret_key
    CORS(app, origins=settings.cors_origin_list)

    # without an explicit openapi version in config, flasgger's own
    # DEFAULT_CONFIG injects "swagger": "2.0" into the served spec before
    # merging in the template - since dict.update() doesn't drop keys the
    # template doesn't mention, that stray key survives alongside our
    # template's "openapi": "3.0.3" and swagger-ui refuses to render the
    # result ("swagger and openapi fields cannot be present together").
    # merge=True is required too - passing `config` without it replaces
    # flasgger's whole DEFAULT_CONFIG (losing "specs"/"specs_route"/etc)
    # instead of layering our one override on top of it.
    Swagger(
        app,
        template_file="./swagger/main.yaml",
        config={"openapi": "3.0.3"},
        merge=True,
    )

    redis_instance = redis.StrictRedis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        ssl=settings.redis_ssl,
        db=0,
        decode_responses=True,
    )
    app.extensions["redis"] = redis_instance

    app.config["RATELIMIT_STORAGE_URI"] = settings.redis_url
    # must be set before init_app() - Limiter caches "enabled" at init time
    app.config["RATELIMIT_ENABLED"] = settings.flask_env != "testing"
    limiter.init_app(app)

    # message_queue makes this horizontally-scalable from day one - any
    # number of app instances can share ride-status broadcasts through
    # the same Redis instance already required for the JWT blacklist.
    # Skipped in testing: flask-socketio's test client talks to the
    # server object directly and doesn't need a real queue backing it,
    # and it lets the test suite run without a live Redis pub/sub round
    # trip on every emit.
    is_testing = settings.flask_env == "testing"
    socketio.init_app(
        app,
        cors_allowed_origins=settings.cors_origin_list,
        message_queue=None if is_testing else settings.redis_url,
        # eventlet matches the Dockerfile's gunicorn -k eventlet worker in
        # production/dev; "threading" in tests avoids eventlet spinning
        # up its own hub on every one of the hundred-plus per-test Flask
        # app instances the suite creates, which was tripling the runtime
        # for no real benefit (nothing in the test suite runs under an
        # actual eventlet-served WSGI server anyway)
        async_mode="threading" if is_testing else "eventlet",
    )

    from api.v1.views import admin_bp, rider_bp, driver_bp, webhook_bp
    import api.v1.sockets  # noqa: F401 - registers the socket event handlers

    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(driver_bp, url_prefix="/api/v1/driver")
    app.register_blueprint(rider_bp, url_prefix="/api/v1/rider")
    app.register_blueprint(webhook_bp, url_prefix="/api/v1/webhooks")

    register_error_handlers(app)

    @app.teardown_appcontext
    def _release_db_session(exception=None):
        # DBStorage's session is never explicitly committed/closed after
        # read-only queries, so a request that only does SELECTs leaves an
        # open transaction sitting on the pooled connection indefinitely.
        # Roll it back at the end of every request to release it.
        from models import storage

        storage.rollback()

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify(
                {"error": "Requirement missing, incorrect format or incorrect attribute"}
            ),
            400,
        )

    @app.errorhandler(405)
    def method_error(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(415)
    def unsupported(error):
        return jsonify({"error": "Unsupported media type"}), 415

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "An internal error occurred"}), 500

    @app.errorhandler(502)
    def upstream_error(error):
        return jsonify({"error": "An upstream service is unavailable"}), 502

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized to access"}), 401

    @app.errorhandler(403)
    def admin_resource(error):
        return jsonify({"error": "access not allowed"}), 403


if __name__ == "__main__":
    app = create_app()
    # socketio.run() instead of app.run() - a bare Werkzeug dev server
    # doesn't support real WebSocket upgrades, only the eventlet-backed
    # server this starts does (matches the Dockerfile's gunicorn -k
    # eventlet worker in production).
    socketio.run(
        app, debug=(settings.flask_env == "development"), host="0.0.0.0", port=5000
    )
