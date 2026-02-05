from pydantic import BaseModel, EmailStr,  Field
from datetime import datetime
from typing import Dict, List, Optional



# Esquema base con los datos comunes
class YieldBase(BaseModel):
    filename: str = Field(..., example="tree_01.jpg")
    healthy_count: int = Field(..., ge=0, example=12)
    damaged_count: int = Field(..., ge=0, example=3)
    total_count: int = Field(..., ge=0, example=15)
    health_index: float = Field(..., ge=0, le=100, example=80.0)

# Esquema para la creación de un registro (Input para la DB)
class YieldCreate(YieldBase):
    pass

# Esquema para la respuesta al usuario (Output de la API)
class YieldResponse(YieldBase):
    id: int
    created_at: datetime

    class Config:
        # Esto permite que Pydantic lea los datos de modelos de SQLAlchemy (objetos)
        # y no solo de diccionarios. Es vital para la integración con la DB.
        from_attributes = True

# Esquema específico para el análisis rápido (Dashboard de React)
class YieldAnalytics(BaseModel):
    total_detected: int
    healthy_count: int
    damaged_count: int = 0
    average_health_index: float = 0.0
    records_count: int = 0
    
    
class DetectionBase(BaseModel):
    class_label: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int

class PredictionResponse(BaseModel):
    total_apples: int
    good_apples: int
    damaged_apples: int
    healthy_percentage: float
    detections: List[DetectionBase]

    class Config:
        orm_mode = True