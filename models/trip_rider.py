from sqlalchemy import Column, ForeignKey, String, Boolean, VARCHAR
from models.base_model import Base, BaseModel
from sqlalchemy.orm import relationship


class TripRider(BaseModel, Base):
    __tablename__ = 'trip_riders'
    trip_id = Column(String(128), ForeignKey('trips.id'), primary_key=True)
    rider_id = Column(String(128), ForeignKey('riders.id'), primary_key=True)
    is_past = Column(Boolean, default=False)
    status = Column(VARCHAR(128), default='booked')
    status_by = Column(VARCHAR(128), default='rider')
    
    trip = relationship("Trip", back_populates="riders")
    rider = relationship("Rider", back_populates="trips")