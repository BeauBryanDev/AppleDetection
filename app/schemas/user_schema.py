from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.db.models.users import UserRole

# Shared base properties for all users
class UserBase(BaseModel):
    
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    role: Optional[UserRole] = UserRole.GUEST

# Properties to receive via API on creation from admin panel, it includes role field.
class UserCreateAdmin(UserBase):
    """ carefull with name change fro mthis class, it might break admin panel registration form, it needs to be consistent with the form fields in frontEnd. """
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
# Properties allowed on user update (all optional)
class UserUpdate(BaseModel):
    
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None


# Properties to return to client
class UserResponse(UserBase):
    
    id: int
    created_at: datetime

    class Config:
        
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
