from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.endpoints import estimator, history, analytics, users, farming
from app.db.session import engine, Base
from app.db import models  # Import models package to register all models
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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    "http://frontend-domain.com",
    "http://127.0.0.1:5173",  # for vite development server
    "http://localhost:5173",  # for vite development server
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],
    allow_origins=["http://localhost:3000"],  # Tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[  #  Headers que el frontend puede leer
        "X-Healthy-Count",
        "X-Damaged-Count",
        "X-Total-Count",
        "X-Health-Index",
        "X-Record-ID",
        "X-Prediction-ID"
    ]
)

if not os.path.exists("uploads"):

    os.mkdir("uploads")
    
    
# Serve static files (uploads directory)

app.mount("/outputs", StaticFiles(directory="uploads"), name="outputs")
    
# Include routers


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Yield Estimator API is running",
        "docs"   : "/docs",    
        "status"  : "healthy"   ,
        "version" : "1.0.0"
            }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "yield_estimator"
            }


@app.on_event("startup")
async def startup_event():
    """
    Tareas a ejecutar al iniciar la aplicación.
    """
    print("Iniciando Apple Yield Estimator API...")
    print("Cargando modelo ONNX...")
    print("API lista para recibir requests")


app.include_router(
    estimator.router, 
    prefix="/api/v1", 
    tags=["Estimator"]
)

app.include_router(
    history.router,
    prefix="/api/v1", 
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
    """
    Tareas a ejecutar al apagar la aplicación.
    """
    print("[X] Cerrando Apple Yield Estimator API...")


#app.include_router(history.router, prefix="/api/history", tags=["history"])



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        
        )
