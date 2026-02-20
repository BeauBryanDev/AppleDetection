from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Main App Config /Global Settings/.
    
    Priority: Env vars > .env file > default values
    """
    
    # Application metadata
    APP_NAME: str = "Apple Yield Estimator API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "API For Apple Estimator using YOLOv8"
    
    DEBUG: bool = Field(default=False, json_schema_extra={"env": "DEBUG"})
    LOG_LEVEL: str = Field(default="INFO", json_schema_extra={"env": "LOG_LEVEL"})
    
    # SERVER Configuration - Uvicorn/Gunicorn
    HOST: str = Field(default="0.0.0.0", json_schema_extra={"env": "HOST"})
    PORT: int = Field(default=8000, json_schema_extra={"env": "PORT"})
    WORKERS: int = Field(default=1, json_schema_extra={"env": "WORKERS"})
    
    # Security and JWT
    SECRET_KEY: str = Field(..., json_schema_extra={"env": "SECRET_KEY"})
    ALGORITHM: str = Field(default="HS256", json_schema_extra={"env": "ALGORITHM"})
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        json_schema_extra={"env": "ACCESS_TOKEN_EXPIRE_MINUTES"}
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """SECRET KEY must no be sent to Production."""
        if not v:
            raise ValueError(
                "[X] CRITICAL: SECRET_KEY is required! "
                "Set it in your .env file or environment variables."
            )
        
        # Advertencia si se está usando una clave débil
        if len(v) < 32:
            print(
                "[!] WARNING: SECRET_KEY should be at least 32 characters long. "
                "Generate a strong key with: openssl rand -hex 32"
            )
        
        return v
    
    # ============================================
    # CORS
    # ============================================
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",     # React dev
            "http://localhost:5173",     # Vite dev
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        json_schema_extra={"env": "BACKEND_CORS_ORIGINS"}
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Comma Separate String -> List"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # DATABASE (PostgreSQL)
    POSTGRES_SERVER: str = Field(default="localhost", json_schema_extra={"env": "POSTGRES_SERVER"})
    POSTGRES_USER: str = Field(default="postgres", json_schema_extra={"env": "POSTGRES_USER"})
    POSTGRES_PASSWORD: str = Field(default="postgres", json_schema_extra={"env": "POSTGRES_PASSWORD"})
    POSTGRES_DB: str = Field(default="yield_estimator", json_schema_extra={"env": "POSTGRES_DB"})
    POSTGRES_PORT: int = Field(default=5432, json_schema_extra={"env": "POSTGRES_PORT"})
    
    # Auto-generated DB URI (PostgreSQL)
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        """Build the database connection URI if not explicitly set."""
        if isinstance(v, str) and v:
            return v
        
        # In Pydantic v2, access data through info.data
        data = info.data if hasattr(info, 'data') else {}
        
        return (
            f"postgresql://{data.get('POSTGRES_USER', 'postgres')}:"
            f"{data.get('POSTGRES_PASSWORD', 'postgres')}@"
            f"{data.get('POSTGRES_SERVER', 'localhost')}:"
            f"{data.get('POSTGRES_PORT', 5432)}/"
            f"{data.get('POSTGRES_DB', 'yield_estimator')}"
        )
    
    # DB CONNECTION POOL
    DB_POOL_SIZE: int = Field(default=5, json_schema_extra={"env": "DB_POOL_SIZE"})
    DB_MAX_OVERFLOW: int = Field(default=10, json_schema_extra={"env": "DB_MAX_OVERFLOW"})
    DB_POOL_TIMEOUT: int = Field(default=30, json_schema_extra={"env": "DB_POOL_TIMEOUT"})
    
    # ML Model configuration
    MODEL_PATH: str = Field(
        default="app/models/weights/best_model.onnx",
        json_schema_extra={"env": "MODEL_PATH"}
    )
    
    MODEL_VERSION: str = Field(
        default="YOLOv8s-Cyberpunk-v1",
        json_schema_extra={"env": "MODEL_VERSION"}
    )
    
    MODEL_INPUT_SIZE: int = Field(default=640, json_schema_extra={"env": "MODEL_INPUT_SIZE"})
    
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.45, 
        json_schema_extra={"env": "CONFIDENCE_THRESHOLD"}
    )
    
    NMS_THRESHOLD: float = Field(default=0.45, json_schema_extra={"env": "NMS_THRESHOLD"})
    
    # Model Classes, Now they are three (apple, damaged_apple)
    MODEL_CLASSES: List[str] = Field(
        default=["apple", "damaged_apple"],
        json_schema_extra={"env": "MODEL_CLASSES"}
    )
    
    MAX_FILE_SIZE_MB: int = Field(default=10, json_schema_extra={"env": "MAX_FILE_SIZE_MB"})
    
    ALLOWED_IMAGE_FORMATS: List[str] = Field(
        default=["image/jpeg", "image/png", "image/jpg"],
        json_schema_extra={"env": "ALLOWED_IMAGE_FORMATS"}
    )
    
    # Directorio de uploads
    UPLOAD_DIR: str = Field(default="uploads", json_schema_extra={"env": "UPLOAD_DIR"})
    
    # CACHE FOR REDIS _OPT
    REDIS_HOST: str = Field(default="localhost", json_schema_extra={"env": "REDIS_HOST"})
    REDIS_PORT: int = Field(default=6379, json_schema_extra={"env": "REDIS_PORT"})
    REDIS_DB: int = Field(default=0, json_schema_extra={"env": "REDIS_DB"})
    REDIS_PASSWORD: Optional[str] = Field(default=None, json_schema_extra={"env": "REDIS_PASSWORD"})
    
    CACHE_ENABLED: bool = Field(default=False, json_schema_extra={"env": "CACHE_ENABLED"})
    CACHE_TTL: int = Field(default=3600, json_schema_extra={"env": "CACHE_TTL"})  # 1 hora
    
    # STORAGE (S3/Local)
    STORAGE_TYPE: str = Field(default="local", json_schema_extra={"env": "STORAGE_TYPE"})  # "local" o "s3"
    
    # AWS S3 (si STORAGE_TYPE=s3)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, json_schema_extra={"env": "AWS_ACCESS_KEY_ID"})
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, json_schema_extra={"env": "AWS_SECRET_ACCESS_KEY"})
    AWS_REGION: str = Field(default="us-east-1", json_schema_extra={"env": "AWS_REGION"})
    S3_BUCKET_NAME: Optional[str] = Field(default=None, json_schema_extra={"env": "S3_BUCKET_NAME"})
    
    # MONITORING
    SENTRY_DSN: Optional[str] = Field(default=None, json_schema_extra={"env": "SENTRY_DSN"})
    ANALYTICS_ENABLED: bool = Field(default=True, json_schema_extra={"env": "ANALYTICS_ENABLED"})
    
    # RATE LIMITING
    RATE_LIMIT_ENABLED: bool = Field(default=False, json_schema_extra={"env": "RATE_LIMIT_ENABLED"})
    RATE_LIMIT_PER_MINUTE: int = Field(default=10, json_schema_extra={"env": "RATE_LIMIT_PER_MINUTE"})
    
    # TIMEZONE
    TIMEZONE: str = Field(default="America/Bogota", json_schema_extra={"env": "TIMEZONE"})
    TIMEZONE_OFFSET_HOURS: int = Field(default=-5, json_schema_extra={"env": "TIMEZONE_OFFSET_HOURS"})
    
    # PYDANTIC SETTINGS
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignorar variables extra en .env
    )


# Global settings instance
settings = Settings()


# HELPERS 

def get_settings() -> Settings:
    """Returns the global settings instance."""
    return settings


def print_settings():
    """
    Imprime la configuración actual (sin valores sensibles).
    
    Útil para debugging al iniciar la aplicación.
    """
    print("\n" + "="*70)
    print("⚙️  APPLICATION CONFIGURATION")
    print("="*70)
    print(f"App Name:           {settings.APP_NAME}")
    print(f"Version:            {settings.APP_VERSION}")
    print(f"Debug:              {settings.DEBUG}")
    print(f"Log Level:          {settings.LOG_LEVEL}")
    print(f"Host:               {settings.HOST}:{settings.PORT}")
    print(f"Workers:            {settings.WORKERS}")
    print("-"*70)
    print("🔐 SECURITY")
    print("-"*70)
    print(f"Algorithm:          {settings.ALGORITHM}")
    print(f"Token Expiration:   {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"Secret Key:         {'*' * 32} (hidden)")
    print("-"*70)
    print("🗄️  DATABASE")
    print("-"*70)
    print(f"Database:           {settings.POSTGRES_DB}")
    print(f"Server:             {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    print(f"User:               {settings.POSTGRES_USER}")
    print(f"Pool Size:          {settings.DB_POOL_SIZE}")
    print(f"Max Overflow:       {settings.DB_MAX_OVERFLOW}")
    print("-"*70)
    print("🤖 ML MODEL")
    print("-"*70)
    print(f"Model Path:         {settings.MODEL_PATH}")
    print(f"Model Version:      {settings.MODEL_VERSION}")
    print(f"Input Size:         {settings.MODEL_INPUT_SIZE}")
    print(f"Confidence Thresh:  {settings.CONFIDENCE_THRESHOLD}")
    print(f"NMS Threshold:      {settings.NMS_THRESHOLD}")
    print(f"Classes:            {', '.join(settings.MODEL_CLASSES)}")
    print("-"*70)
    print("🌐 CORS")
    print("-"*70)
    print(f"Allowed Origins:    {len(settings.BACKEND_CORS_ORIGINS)} origins")
    for origin in settings.BACKEND_CORS_ORIGINS:
        print(f"  - {origin}")
    print("-"*70)
    print("📁 STORAGE")
    print("-"*70)
    print(f"Upload Directory:   {settings.UPLOAD_DIR}")
    print(f"Max File Size:      {settings.MAX_FILE_SIZE_MB} MB")
    print(f"Storage Type:       {settings.STORAGE_TYPE}")
    print("-"*70)
    print("🚀 FEATURES")
    print("-"*70)
    print(f"Cache Enabled:      {settings.CACHE_ENABLED}")
    print(f"Rate Limiting:      {settings.RATE_LIMIT_ENABLED}")
    print(f"Analytics:          {settings.ANALYTICS_ENABLED}")
    print(f"Timezone:           {settings.TIMEZONE} (UTC{settings.TIMEZONE_OFFSET_HOURS})")
    print("="*70 + "\n")


def validate_settings():
    """
    Validate configuration before app startup.

    Raises:
        ValueError: If any critical settings are invalid
        FileNotFoundError: If model file doesn't exist

    Example usage in main.py:
        @app.on_event("startup")
        async def startup():
            validate_settings()
    """
    errors = []
    
    # Check model exists
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        errors.append(f"❌ Model not found: {settings.MODEL_PATH}")
    
    # Validate thresholds
    if not 0 < settings.CONFIDENCE_THRESHOLD < 1:
        errors.append("❌ CONFIDENCE_THRESHOLD must be between 0 and 1")
    
    if not 0 < settings.NMS_THRESHOLD < 1:
        errors.append("❌ NMS_THRESHOLD must be between 0 and 1")
    
    # Ensure upload dir exists
    upload_dir = Path(settings.UPLOAD_DIR)
    if not upload_dir.exists():
        print(f"⚠️  Upload directory '{settings.UPLOAD_DIR}' does not exist. Creating...")
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created upload directory: {settings.UPLOAD_DIR}")
    
    ## Warn on weak SECRET_KEY in production
    if not settings.DEBUG and len(settings.SECRET_KEY) < 32:
        errors.append(
            "⚠️  WARNING: SECRET_KEY should be at least 32 characters in production. "
            "Generate with: openssl rand -hex 32"
        )
    
    # Si hay errores, lanzar excepción
    if errors:
        error_msg = "\n".join(errors)
        raise ValueError(f"\n\n{'='*70}\n⛔ CONFIGURATION ERRORS:\n{'='*70}\n{error_msg}\n{'='*70}\n")
    
    print("✅ Configuration validated successfully\n")


def get_db_uri() -> str:
    """
    Obtiene la URI de conexión a la base de datos.
    
    Returns:
        str: URI de conexión PostgreSQL
    """
    return settings.SQLALCHEMY_DATABASE_URI


def is_production() -> bool:
    """
    Determina si la aplicación está en modo producción.
    
    Returns:
        bool: True si está en producción
    """
    return not settings.DEBUG


def get_cors_origins() -> List[str]:
    """
    Obtiene la lista de orígenes permitidos para CORS.
    
    Returns:
        List[str]: Lista de orígenes
    """
    return settings.BACKEND_CORS_ORIGINS