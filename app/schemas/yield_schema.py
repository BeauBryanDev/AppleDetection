from pydantic import BaseModel, EmailStr,  Field
from datetime import datetime
from typing import Dict, List, Optional


# Basic  Schema for common datos without logging first.
class YieldBase(BaseModel):
    
    filename: str = Field(..., example="tree_01.jpg")
    healthy_count: int = Field(..., ge=0, example=12)
    damaged_count: int = Field(..., ge=0, example=3)
    total_count: int = Field(..., ge=0, example=15)
    health_index: float = Field(..., ge=0, le=100, example=80.0)

# Schema to create a new log into database
class YieldCreate(YieldBase):
    
    pass

# Schema for user response API Output
class YieldResponse(YieldBase):
    
    id: int
    created_at: datetime

    class Config:
        # It allows Pydantic to read the models 
        # Critical for databsee Integration 
        from_attributes = True

# Rightfull Schema for quick  Analyissi , critical for React Dashboard in frontEnd.
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


class SaveDetectionRequest(BaseModel):
    """Schema for saving detection after user review"""

    image_path: str = Field(..., description="Path to the processed image file")
    healthy_count: int = Field(..., ge=0)
    damaged_count: int = Field(..., ge=0)
    total_count: int = Field(..., ge=0)
    health_index: float = Field(..., ge=0, le=100)
    user_notes: Optional[str] = None
    orchard_id: Optional[int] = None
    tree_id: Optional[int] = None
    inference_time_ms: float = Field(default=0.0, ge=0, description="Inference time in milliseconds")
    

    class Config:
        json_schema_extra = {
            "example": {
                "image_path": "uploads/abc123_image.jpg",
                "healthy_count": 10,
                "damaged_count": 2,
                "total_count": 12,
                "health_index": 83.33,
                "inference_time_ms": 150.5,
                "user_notes": "Tree looks healthy, minor pest damage on 2 apples",
                "orchard_id": 1,
                "tree_id": 5
            }
        }