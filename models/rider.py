import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Integer, VARCHAR
from sqlalchemy.orm import relationship

class Rider(BaseModel, Base):
    __tablename__ = 'riders'
    username = Column(String(128), nullable=False, unique=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    phone_number = Column(Integer, nullable=False, unique=True)
    password_hash = Column(String(250), nullable=False)
    reset_token = Column(String(250), nullable=True)
    payment_method = Column(VARCHAR(128), nullable=False)

    # 0e5dec68-f978-4c89-a32c-4478bed8efb0
    trips = relationship("TripRider", back_populates="rider")
    
    notification = relationship("Notification",
                                backref="riders",
                                cascade="all, delete, delete-orphan")