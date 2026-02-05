from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole


class TreeBase(BaseModel):
    
    orchard_id: int
    tree_code : str
    tree_type : str


class Create(TreeBase):
    pass

class Update(TreeBase):
    pass

class Response(TreeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

