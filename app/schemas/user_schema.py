from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.db.models.users import UserRole

# Shared properties
class UserBase(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    role: Optional[UserRole] = UserRole.GUEST

# Properties to receive via API on creation
class UserCreate(UserBase):
    name: str
    email: EmailStr
    password: str


# Schema for Public Register / Log , it dos nto need role field.
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None

# Schema for Admin with role field.
class UserCreate(UserSignup):
    role: UserRole = UserRole.FARMER

# Properties to receive via API on update
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None


# Properties to return to client
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
