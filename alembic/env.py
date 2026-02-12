import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Impport my own settings from FastAPI app
from app.core.config import settings

# Import Base class from models to get metadata for Alembic
from app.db.base import Base

# Import models to ensure they are registered with Base.metadata
from app.db.models.users import User
from app.db.models.farming import (
    Orchard, Tree, Image, Prediction, Detection, YieldRecord
)

config = context.config

# Set the SQLAlchemy URL from FastAPI settings
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# CLOGGING CONFIG 
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Migrations directory
migrations_dir = os.path.join(os.path.dirname(__file__), "versions")

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    
    run_migrations_offline()
    
else:
    
    run_migrations_online()