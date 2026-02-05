from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole

class OrchardBase(BaseModel):
    name: str
    location: Optional[str] = None
    n_trees: int    
    user_id: int

class Create(OrchardBase):
    user_id: int

class Orchard(OrchardBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
