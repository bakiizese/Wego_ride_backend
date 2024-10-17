import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Integer, BINARY, Enum

class Admin(BaseModel, Base):
    __tablename__ = 'admins'
    username = Column(String(128), nullable=False, unique=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    phone_number = Column(Integer, nullable=False, unique=True)
    password_hash = Column(String(250), nullable=False)
    reset_token = Column(String(250), nullable=True)
    admin_level = Column(Enum("superadmin", "moderator"))