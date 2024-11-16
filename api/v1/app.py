#!/usr/bin/python
from flask import Flask, jsonify
from flasgger import Swagger
from api.v1.views import admin_bp, rider_bp, driver_bp
import logging
from flask_cors import CORS

app = Flask(__name__)
app.json.sort_keys = False
CORS(app)

swagger = Swagger(app, template_file="./swagger/main.yaml")

app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
app.register_blueprint(driver_bp, url_prefix="/api/v1/driver")
app.register_blueprint(rider_bp, url_prefix="/api/v1/rider")

logging.basicConfig(
    # filename="./logs/error.log",
    level=logging.WARNING,
    format="%(asctime)s:%(name)s:%(levelname)s:%(message)s",
)


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


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized to access"}), 401


@app.errorhandler(403)
def admin_resource(error):
    return jsonify({"error": "access not allowed"}), 403


if __name__ == "__main__":
    app.run(debug=1)
