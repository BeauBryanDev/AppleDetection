from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import estimator, history
from app.db.session import engine, Base
import uvicorn
import logging

logger = logging.getLogger(__name__)

# Try to create tables, but don't fail if DB is unavailable
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables at startup: {e}")

# Create FastAPI app instance
app = FastAPI(
    title="Yield Estimator API",
    description="API for crop yield estimation using computer vision",
    version="1.0.0"
)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(estimator.router, prefix="/api/estimator", tags=["estimator"])
#app.include_router(history.router, prefix="/api/history", tags=["history"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "Yield Estimator API is running",
        "docs"   : "/docs",    
        "status"  : "healthy"   
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
