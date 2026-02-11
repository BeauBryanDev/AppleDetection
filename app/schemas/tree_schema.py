from pydantic import BaseModel
from typing import Optional

# Shared properties
class TreeBase(BaseModel):
    tree_code: str
    tree_type: Optional[str] = None

# Properties to receive on creation
class TreeCreate(TreeBase):
    pass

# Properties to receive on update
class TreeUpdate(BaseModel):
    tree_code: Optional[str] = None
    tree_type: Optional[str] = None

# Properties returned to client
class Tree(TreeBase):
    id: int
    orchard_id: int
    user_id: int

    class Config:
        from_attributes = True
