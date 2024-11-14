import models
from models.base_model import BaseModel, Base
from sqlalchemy.orm import relationship
from sqlalchemy import String, Column, Integer, VARCHAR, Boolean


class Driver(BaseModel, Base):
    __tablename__ = "drivers"
    username = Column(String(128), nullable=False, unique=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    phone_number = Column(String(128), nullable=False, unique=True)
    password_hash = Column(String(250), nullable=False)
    reset_token = Column(String(250), nullable=True)
    payment_method = Column(VARCHAR(128), nullable=False)

    deleted = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)

    vehicle = relationship("Vehicle", uselist=False, back_populates="driver")
    trip = relationship("Trip", backref="drivers", cascade="all, delete, delete-orphan")
    availability = relationship(
        "Availability", backref="drivers", cascade="all, delete, delete-orphan"
    )
