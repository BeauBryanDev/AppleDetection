from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime, timedelta, timezone
from enum import Enum as PyEnum

def get_bogota_time():
    """Return current time in Bogotá timezone (UTC-5)."""
    return datetime.now(timezone(timedelta(hours=-5)))


class UserRole(str, PyEnum):
    
    """Users Roles Available""" 
    ADMIN = "admin"
    FARMER = "farmer"
    GUEST = "guest"


class User(Base):
    """User model depicting system accounts."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    address = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GUEST, nullable=False)
    created_at = Column(DateTime, default=get_bogota_time, nullable=False)
    updated_at = Column(DateTime, default=get_bogota_time, onupdate=get_bogota_time, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_premium = Column(Boolean, default=False)  # For future subscription features
    is_active = Column(Boolean, default=True)  # For future account suspension
    avatar_url = Column(String, nullable=True)  # For future profile pictures
    
    # Relación: Un usuario tiene muchos huertos
    orchards = relationship("Orchard", back_populates="owner")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role='{self.role}', created_at='{self.created_at}', updated_at='{self.updated_at}')>"