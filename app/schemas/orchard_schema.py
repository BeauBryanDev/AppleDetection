from pydantic import BaseModel
from typing import Optional
from app.db.models.users import UserRole


# Shared Properties for Orchard Base Schema
class OrchardBase(BaseModel):
    
    name: str
    location: Optional[str] = None
    n_trees: int    

# Schema to create a new Orchard
class OrchardCreate(OrchardBase):
    """carefull with name change fro mthis class, it might break admin panel registration form, it needs to be consistent with the form fields in frontEnd. """
    name: str
    location: Optional[str] = None
    n_trees: int
    pass

# General Orchard Schema (Response)
class Orchard(OrchardBase):
    
    id: int
    user_id: int

# Critical for database Integration .
    class Config:
        from_attributes = True
