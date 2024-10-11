from flask import Flask
from api.v1.views import admin_bp, rider_bp, driver_bp
from flask_cors import CORS

app = Flask(__name__)

app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
app.register_blueprint(driver_bp, url_prefix='/api/v1/driver')
app.register_blueprint(rider_bp, url_prefix='/api/v1/rider')


if __name__ == '__main__':
    app.run(debug=1)