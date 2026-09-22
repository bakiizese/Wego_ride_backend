#!/usr/bin/python
"""Shared request-body parsing/validation helpers."""

from functools import wraps
from typing import Optional

from flask import abort, jsonify, request
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator


def parse_json_body() -> dict:
    """Parse the request JSON body, aborting with a clean 400 instead of
    crashing when the body is missing/empty/malformed."""
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="request body must be valid JSON")
    return data


def validate_body(schema_cls):
    """Decorator: parse + validate the JSON body against a pydantic schema,
    passing the validated model in as `request.validated`."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = parse_json_body()
            try:
                request.validated = schema_cls.model_validate(data)
            except ValidationError as e:
                errors = [
                    {"field": ".".join(str(p) for p in err["loc"]), "error": err["msg"]}
                    for err in e.errors()
                ]
                return jsonify({"error": "validation failed", "details": errors}), 400
            return f(*args, **kwargs)

        return wrapper

    return decorator


class UserRegisterSchema(BaseModel):
    username: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    phone_number: str = Field(min_length=1)
    password_hash: str = Field(min_length=8)
    payment_method: str = Field(min_length=1)

    @field_validator("phone_number")
    @classmethod
    def phone_number_must_be_numeric(cls, v):
        if not v.isdigit():
            raise ValueError("phone_number must contain digits only")
        return v


class LoginSchema(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password_hash: str


class ProfileUpdateSchema(BaseModel):
    """All fields optional - a caller can update just one field without
    also having to change their password."""

    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    payment_method: Optional[str] = None
    password_hash: Optional[str] = Field(default=None, min_length=8)
    old_password: Optional[str] = None


class BookRideSchema(BaseModel):
    trip_id: str = Field(min_length=1)


class NotificationSchema(BaseModel):
    message: str = Field(min_length=1)


class SetRideSchema(BaseModel):
    driver_id: str
    pickup_location_id: str
    dropoff_location_id: str
    fare: float = Field(gt=0)
    distance: float = Field(gt=0)
    driver_commission: float = Field(ge=0, le=100)


class VehicleRegisterSchema(BaseModel):
    type: str = Field(min_length=1)
    model: str = Field(min_length=1)
    color: str = Field(min_length=1)
    seating_capacity: int = Field(gt=0)
    plate_number: str = Field(min_length=1)
    license_number: Optional[str] = None


class VehicleUpdateSchema(BaseModel):
    """All fields optional - a caller can update just one field."""

    type: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    seating_capacity: Optional[int] = Field(default=None, gt=0)
    plate_number: Optional[str] = None
    license_number: Optional[str] = None


class RatingSchema(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)


class DriverRateRiderSchema(RatingSchema):
    rider_id: str = Field(min_length=1)
