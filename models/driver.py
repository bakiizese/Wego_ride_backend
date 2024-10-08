import models
from models.base_model import BaseModel, Base
from sqlalchemy.orm import relationship
from sqlalchemy import String, Column, Integer

class Driver(BaseModel, Base):
    __tablename__ = 'drivers'
    username = Column(String(128), nullable=False, unique=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    phone_number = Column(Integer, nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    vehicle = relationship("Vehicle", 
                           backref="drivers",
                           cascade="all, delete, delete-orphan"
                           )
    notification = relationship("Notification",
                                backref="drivers",
                                cascade="all, delete, delete-orphan")
    trip = relationship("Trip",
                        backref="drivers",
                        cascade="all, delete, delete-orphan")
    availability = relationship("Availability",
                                backref="drivers",
                                cascade="all, delete, delete-orphan")