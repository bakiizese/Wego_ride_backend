import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, DateTime, VARCHAR, String, Float, ForeignKey

class Payment(BaseModel, Base):
    __tablename__ = 'payments'
    trip_id = Column(String(128), ForeignKey('trips.id'))
    payment_method = Column(VARCHAR(128), nullable=False)
    payment_time = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    payment_status = Column(VARCHAR(128), nullable=False)