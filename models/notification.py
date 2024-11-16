#!/usr/bin/python
import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, VARCHAR


class Notification(BaseModel, Base):
    __tablename__ = "notifications"
    sender_id = Column(String(128))
    sender_type = Column(String(60))
    receiver_id = Column(String(128))
    receiver_type = Column(String(60))
    message = Column(VARCHAR(1024))
    notification_type = Column(VARCHAR(128))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(128))
