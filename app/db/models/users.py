from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timedelta, timezone
from enum import Enum as PyEnum

def get_bogota_time():
    return datetime.now(timezone(timedelta(hours=-5)))


class UserRole(str, PyEnum):
    ADMIN = "admin"
    FARMER = "farmer"
    GUEST = "guest"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GUEST)
    created_at = Column(DateTime, default=get_bogota_time)
    
    # Relación: Un usuario tiene muchos huertos
    orchards = relationship("Orchard", back_populates="owner")
