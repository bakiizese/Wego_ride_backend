import models
from models.base_model import BaseModel, Base
from sqlalchemy import VARCHAR, Column, Float
from sqlalchemy.orm import relationship

class Location(BaseModel, Base):
    __tablename__ = 'locations'
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(VARCHAR(128))
    availability = relationship("Availability",
                                backref="locations",
                                cascade="all, delete, delete-orphan")
    pickup_location = relationship("Trip",
                                   foreign_keys="Trip.pickup_location_id",
                                   backref="pickup_locations",
                                   cascade="all, delete, delete-orphan")
    dropoff_location = relationship("Trip",
                                    foreign_keys="Trip.dropoff_location_id",
                                    backref="dropoff_locations",
                                    cascade="all, delete, delete-orphan")