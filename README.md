# Wego_ride_backend
# --Wego Ride--

Welcome to **Wego Ride**, a ride-hailing service platform that allows users to request rides, track drivers, manage payments, and more. The platform provides essential features such as authentication, ride management, and secure data handling. Built with **Flask**, this backend service supports multiple user roles, real-time ride updates, and integrates with various modules for a seamless experience.

## Table of Contents

- [Project Overview](#project-overview)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup-installation)
- [API Documentation](#api-documentation)

## Project Overview

--Wego Ride-- provides a platform for riders, drivers, and admins to interact. Key features include:

- **User Authentication**: Secure registration and login for riders, drivers, and admins.
- **Role-Based Access**: Differentiated access control based on user roles (Driver, Rider, Admin).
- **Password Management**: Users can securely reset their passwords using a reset token.
- **Real-Time Notifications**: Ride updates and status notifications.
- **Ride Management**: Booking, updating, and tracking rides.
- **Payment Processing**: Riders make payments, and drivers receive payouts for completed rides.
- **Location Tracking**: Real-time location updates for drivers and riders.

## Technologies Used

- **Backend**: Flask, SQLAlchemy
- **Authentication**: JWT, bcrypt for password hashing
- **Database**: MySQL, Redis
- **Utilities**: UUID for token generation
- **Other**: Python, DateTime

## Project Structure
   ```bash
   /Wego_ride_backend
   │
   ├── api/                        # Contains the core logic of the Flask API
   │   ├── __init__.py             # Initializes the api package
   │   └── v1/                     # API versioning directory
   │       ├── swagger/            # API documentation (Swagger definition)
   │       │   └── main.yaml       # API definition in YAML format (Swagger)
   │       ├── views/              # Views (Controllers) for Admin, Driver, and Rider
   │       │   ├── __init__.py     # Initializes the views package
   │       │   ├── admin_views.py  # Routes for Admin functionalities
   │       │   ├── driver_views.py # Routes for Driver functionalities
   │       │   ├── rider_views.py  # Routes for Rider functionalities
   │       ├── __init__.py         # Initializes the api/v1 package
   │       ├── app.py              # Main Flask app entry point
   │       └── middleware.py       # Middleware for authentication, error handling
   │
   ├── auth/                       # Authentication module
   │   ├── __init__.py             # Initializes the auth package
   │   └── authentication.py       # Logic for user authentication and JWT handling
   │
   ├── models/                     # Database models (SQLAlchemy models)
   │   ├── engine/                 # Contains database engine and storage logic
   │   │   ├── db_storage.py       # Logic for managing DB operations (CRUD)
   │   │   └── __init__.py         # Initializes the engine package
   │   ├── __init__.py             # Initializes the models package
   │   ├── admin.py                # Admin model
   │   ├── availability.py         # Availability model
   │   ├── base_model.py           # Base model for shared functionality
   │   ├── driver.py               # Driver model
   │   ├── location.py             # Location model
   │   ├── notification.py         # Notification model
   │   ├── payment.py              # Payment model
   │   ├── rider.py                # Rider model
   │   ├── total_payment.py        # Total Payment model
   │   ├── trip_rider.py           # Trip Rider model
   │   ├── trip.py                 # Trip model
   │   └── vehicle.py              # Vehicle model
   │
   ├── test/                       # Unit tests for the project
   │   ├── __init__.py             # Initializes the test package
   │   ├── test_api/...            # Tests for Flask api
   │   ├── test_auth/...           # Tests for authentication
   │   ├── test_models/...         # Tests for engine and models (e.g., CRUD operations)
   │   └── ...                     # Other test files
   │
   ├── console.py                  # Command-line interface for interacting with the app
   ├── README.md                   # Project documentation (this file)
   ├── requirements.txt            # Python dependencies for the project
   ├── setup_mysql_dev.sql         # MySQL setup script for development environment
   └── wego_dump.sql               # SQL dump for initializing the database


## Setup & Installation

### Prerequisites

Before you begin, ensure you have the following software installed:

- **Python 3.7+**: The backend service is built with Python.
- **MySQL**: Used for storing user and ride data.
- **pip**: For installing Python dependencies.

### Install Dependencies

1. **Clone the repository**:
   Clone the `Wego Ride` repository to your local machine:

   ```bash
   git clone https://github.com/bakiizese/Wego_ride_backend.git
   cd Wego_ride_backend

2. **Install the required  Python Packages**
   ```bash
   pip install -r requirements.txt

3. **Set up the MySQL database**
   ```bash
   cat setup_mysql_dev.sql | mysql -u root -p 
   mysql -u username -p database_name < dump.sql

4. **Running the app**
   ```bash
   python -m api/v1/app.py

The application will be running at http://localhost:5000


## API Documentation

### Wego Ride Backend Endpoints

# Admin Endpoints
    Admin Authentication:
        POST /admin/admin-register: Register admin
        POST /admin/login: Admin login
        POST /admin/logout: Admin logout
    Rider  and Driver Management:
        GET /admin/riders: Returns all riders
        GET /admin/driver: Returns all drivers
        PUT /admin/block-user/:user_id: Blocks user
        PUT /admin/unblock-user/:user_id: Unblocks user
        PUT /admin/delete-user/:user_id: Deletes user
        PUT /admin/revalidate-user/user_id: Revalidate user
        GET /admin/deleted-users/user_type: Returns deleted users by user_type
        GET /admin/blocked-users/user_type: Returns blocked users by user_type
        GET /admin/user-profile/:user_id: Returns user profile
    Ride Management:
        POST /admin/set-ride: Creates new ride
        GET /admin/get-rides: Returns all rides
        GET /admin/get-ride/:ride_id: Returns ride(trip) details 
        PUT /admin/delete-ride/:ride_id: Deletes ride
        POST /admin/set-location: Creates new location
        GET /admin/get-location: Returns all locations
    Payment Management:
        GET /admin/transactions: Returns all transactions
        GET /admin/payment/ride_id: Returns all payment by ride_id
        GET /admin/payment-detail/:ride_id: Returns payment detail
    Reports And Analytics
        GET /admin/reports/earnings/date: Returns earnings report, by date(optional)
        GET /admin/reports/ride-activity: Returns rides activity
        GET /admin/reports/issues: Returns issues reported
        GET /admin/reports/issues/issue_id: Returns reported issue
    System Configuration
        POST /admin/notification: Sends notification or an announcement 

# Driver Endpoints
    Registration And Authentication
        POST /driver/register: Registers Driver
        POST /driver/login: Driver login
        POST /driver/logout: Driver logout
    Profile Management
        POST /driver/reset-token: Generates reset-token
        POST /driver/forget-password: Change password
        GET /driver/profile: Returns profile
        PUT /driver/profile: Updates profile
    Ride Management
        GET /driver/availability: Returns driver’s availability
        GET /driver/ride-plans: Returns all ride plans assigned to this driver
        GET /driver/current-ride: Returns current ride’s details
        GET /driver/ride-requests: Returns all ride requests
        POST /driver/start-ride: Marks start ride
        POST /driver/end-ride: Marks end ride
        POST /driver/cancel_ride: Cancel ride
    Ride History And Earning
        GET /driver/ride-history: Returns all driver’s ride history
        GET /driver/earnings/date: Returns daily, monthly.. earnings, by date(optional)

# Rider Endpoints
    Registration And Authentication
        POST /rider/register: Register Rider
        POST /rider/login: Rider login
        POST /rider.logout: Rider logout
    Profile Management
        POST /rider/reset-token: Generates reset-token
        POST /rider/forget-password: Change password
        GET /rider/profile: Returns profile
        PUT /rider/profile:  Updates profile
    Ride Booking
        GET /rider/available-rides: Returns available rides
        POST /rider/book-ride:  Books a ride
        GET rider//ride-estimate: Returns estimates of a ride
        GET rider/booked-ride: Returns booked rides
        GET rider/current-ride/:tripride_id: Returns ride details
        GET rider/ride-status/:tripride_id: Returns status of ride
    Ride History And Management
        GET /rider/ride-history: Returns rider’s ride history
        POST rider/cancel-ride: Cancels a ride
    Payment
        POST /rider/pay-ride: Make payment
    Rating And Feedback
        POST /rider/report-issue: Reports issue
