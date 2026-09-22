#!/usr/bin/python
from sqlalchemy import String, Column
from models.base_model import Base, BaseModel


class Image(BaseModel, Base):
    __tablename__ = "images"
    path = Column(String(250), nullable=False, unique=True)
    user_type = Column(String(60), nullable=False)
    user_id = Column(String(128), nullable=False)
