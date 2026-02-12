from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.endpoints import estimator, history, analytics, users, farming, auth
from app.db.session import engine, Base
from app.core.config import settings
from app.db.base import Base  # Import Base to register models
from app.db import models  # Import models package to register all models
from app.core.logging import configure_logging, RequestContextMiddleware
import uvicorn
import logging

logger = logging.getLogger(__name__)

from app.core.logging import logger  # Import the configured logger

# Try to create tables, but don't fail if DB is unavailable
try:
    
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created successfully")
    
except Exception as e:
    
    logger.warning(f"Could not create database tables at startup: {e}")
    

# Create FastAPI app instance
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else "/redoc",
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    "http://frontend-domain.com",
    "http://127.0.0.1:5173",  # for vite development server
    "http://localhost:5173",  # for vite development server
    'http://localhost:3000', # React default port
    'http://127.0.0.1:3000', # React default port
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[  #  Headers que el frontend puede leer
        "X-Healthy-Count",
        "X-Damaged-Count",
        "X-Total-Count",
        "X-Health-Index",
        "X-Record-ID",
        "X-Prediction-ID",
        "X-Inference-Time-Ms",
        "X-Mode",
        "X-Orchard-ID",
        "X-Tree-ID"
    ]
)

if not os.path.exists("uploads"):

    os.mkdir("uploads")
    
    
# Serve static files (uploads directory)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=UPLOAD_DIR), name="outputs")
    
# Include routers
api_prefix = "/api/v1"


@app.get("/", tags=["Health"])
async def root():
    """Basic welcome endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "healthy",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled in production"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers / monitoring."""
    return {
        "status": "healthy",
        "service": "yield-estimator-api",
        "version": settings.APP_VERSION
    }


@app.on_event("startup")
async def startup_event():
    """Tasks to run when the application starts."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.warning(f"Could not create/verify database tables on startup: {e}")

    configure_logging()
    logger.info(
        "Application startup complete",
        version=settings.APP_VERSION,
        debug_mode=settings.DEBUG,
        environment="development" if settings.DEBUG else "production"
    )

app.add_middleware(RequestContextMiddleware)


app.include_router(
    estimator.router, 
    prefix="/api/v1/estimator", 
    tags=["Estimator"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Auth"]
)

app.include_router(
    history.router,
    prefix="/api/v1/history", 
    tags=["History"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    farming.router,
    prefix="/api/v1/farming",
    tags=["Farming"]
)


@app.on_event("shutdown")
async def shutdown_event():
    """Tasks to run when the application shuts down."""
    print("[X] Cerrando Apple Yield Estimator API...")
    logger.info("Application shutdown initiated")
    


#app.include_router(history.router, prefix="/api/history", tags=["history"])

app.add_middleware(RequestContextMiddleware)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        workers=1,  # Increase in production if needed
    )