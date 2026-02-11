from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Default to SQLite for local development/testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# If DATABASE_URL has environment variable placeholders, build it from individual vars
if "${" in DATABASE_URL or not DATABASE_URL.startswith("sqlite"):
    
    pg_user = os.getenv('POSTGRES_USER')
    pg_password = os.getenv('POSTGRES_PASSWORD')
    pg_host = os.getenv('DB_HOST', 'localhost')
    pg_port = os.getenv('DB_PORT', '5432')
    pg_db = os.getenv('POSTGRES_DB')
    
    if pg_user and pg_password and pg_db:
        
        DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        print(f"Using PostgreSQL: {pg_host}:{pg_port}/{pg_db}")
        
    else:
        
        print("PostgreSQL variables not set, falling back to SQLite")
        DATABASE_URL = "sqlite:///./app_test_db.db"


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL,echo=os.getenv("ENV") == "development")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

#  Deps , FastAPI EndPoints Need Session Opens

def get_db():
    """
    FastAPI dependency to provide a database session.

    Yields a session and ensures it's closed after the request.
    Usage in endpoints: def endpoint(db: Session = Depends(get_db))
    """
    
    db = SessionLocal()
    
    try:
        
        yield db
        
    finally:
        
        db.close()