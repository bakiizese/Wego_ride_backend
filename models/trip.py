import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, VARCHAR, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models.trip_rider import TripRider

class Trip(BaseModel, Base):
    __tablename__ = 'trips'
    driver_id = Column(String(128), ForeignKey('drivers.id'))
    pickup_location_id = Column(String(128), ForeignKey('locations.id'))
    dropoff_location_id = Column(String(128), ForeignKey('locations.id'))
    pickup_time = Column(DateTime)
    dropoff_time = Column(DateTime)
    fare = Column(Float, nullable=False)
    distance = Column(Float)
    status = Column(VARCHAR(128), nullable=False)
    # status_by = Column(VARCHAR(128))
    is_available = Column(Boolean, default=True) #shouldn't be 



    riders = relationship("TripRider", back_populates="trip")
    
    payment = relationship("Payment", 
                           backref="trips",
                           cascade="all, delete, delete-orphan")
    