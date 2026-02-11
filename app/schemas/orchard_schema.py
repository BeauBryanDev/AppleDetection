from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole


# Shared Properties for Orchard Base Schema
class OrchardBase(BaseModel):
    name: str
    location: Optional[str] = None
    n_trees: int    

# Schema to create a new Orchard
class Create(OrchardBase):
    pass

# General Orchard Schema (Response)
class Orchard(OrchardBase):
    id: int
    user_id: int

# Critical for database Integration .
    class Config:
        from_attributes = True
