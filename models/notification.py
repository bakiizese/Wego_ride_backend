import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, VARCHAR

class Notification(BaseModel, Base):
    __tablename__ = 'notifications'
    driver_id = Column(String(128), ForeignKey('drivers.id'))
    rider_id = Column(String(128), ForeignKey('riders.id'))
    message = Column(VARCHAR(1024))
    notification_type = Column(VARCHAR(128))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(128))