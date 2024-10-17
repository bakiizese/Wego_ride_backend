from models.base_model import BaseModel, Base
from sqlalchemy import Column, VARCHAR, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import models

class Vehicle(BaseModel):
    __tablename__ = 'vehicles'
    driver_id = Column(String(128), ForeignKey('drivers.id'))
    type = Column(VARCHAR(60))
    model = Column(VARCHAR(60))
    color = Column(String(60), nullable=False)
    seating_capacity = Column(Integer, nullable=False)
    