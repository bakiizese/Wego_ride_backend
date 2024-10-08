import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

class Rider(BaseModel, Base):
    __tablename__ = 'riders'
    username = Column(String(128), nullable=False, unique=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    phone_number = Column(Integer, nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    trip = relationship("Trip",
                        backref="riders",
                        cascade="all, delete, delete-orphan")
    notification = relationship("Notification",
                                backref="riders",
                                cascade="all, delete, delete-orphan")