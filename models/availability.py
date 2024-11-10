import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey


class Availability(BaseModel, Base):
    __tablename__ = "availabilities"
    driver_id = Column(String(128), ForeignKey("drivers.id"))
    location_id = Column(String(128), ForeignKey("locations.id"))
    is_available = Column(Boolean, default=True)
    last_active_time = Column(DateTime)
