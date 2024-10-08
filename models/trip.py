import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, VARCHAR, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

class Trip(BaseModel, Base):
    __tablename__ = 'trips'
    rider_id = Column(String(128), ForeignKey('riders.id'))
    driver_id = Column(String(128), ForeignKey('drivers.id'))
    pickup_location_id = Column(String(128), ForeignKey('locations.id'))
    dropoff_location_id = Column(String(128), ForeignKey('locations.id'))
    pickup_time = Column(DateTime)
    dropoff_time = Column(DateTime)
    fare = Column(Float, nullable=False)
    distance = Column(Float)
    status = Column(VARCHAR(128), nullable=False)
    payment = relationship("Payment",
                           backref="trips",
                           cascade="all, delete, delete-orphan")