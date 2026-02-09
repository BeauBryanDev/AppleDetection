from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole


# Shared Properties for Orchard Base Schema
class OrchardBase(BaseModel):
    name: str
    location: Optional[str] = None
    n_trees: int    
    user_id: int

# Schema to create a new Orchard with User register
class Create(OrchardBase):
    user_id: int

# General Orchard Schema 
class Orchard(OrchardBase):
    id: int
    user_id: int

# Critical for database Integration .
    class Config:
        from_attributes = True
