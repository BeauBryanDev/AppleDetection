from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole
from datetime import datetime


class ImageBase(BaseModel):
    
    user_id: int
    orchard_id: int
    tree_id: int
    image_path: str


class ImageResponse(BaseModel):
    id: int
    image_path: str
    uploaded_at: datetime
    orchard_id: int
    tree_id: int

    class Config:
        from_attributes = True  
