from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Naming convention ( std Key for Alembic )
# Standard naming convention for constraints/indexes (
    # # It is recommended to use the same naming convention as the database engine for foreign key constraints.
    # fk_<table name>_<column name>_<referred table name>
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
# using naming conventions prevents Alembic from generating ugly random names.
metadata = MetaData(naming_convention=naming_convention)
# Global metadata with naming convention applied
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    All model classes should inherit from this.
    Provides consistent table/constraint naming and a useful __repr__.
    """
    metadata = metadata

    def to_dict(self):
        
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    
    def __repr__(self):
        
        return f"<{self.__class__.__name__}({self.id})>"
    
    
