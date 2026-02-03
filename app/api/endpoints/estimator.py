from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas import yield_schema
from app.models.inference import model_engine
import uuid

router = APIRouter()

@router.post("/estimate", response_model=yield_schema.YieldResponse)
async def create_yield_estimate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validar formato de archivo
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen JPG o PNG")

    try:
        # 2. Leer bytes de la imagen
        image_bytes = await file.read()
        
        # 3. Ejecutar Inferencia de ONNX
        # Nuestra clase AppleInference ya devuelve un diccionario con el conteo
        detection_results = model_engine.run_inference(image_bytes)
        
        healthy = detection_results.get("apple", 0)
        damaged = detection_results.get("damaged_apple", 0)
        total = healthy + damaged
        
        # 4. Calcular Health Index
        # Prevenimos división por cero si no se detecta nada
        health_idx = (healthy / total * 100) if total > 0 else 0.0
        
        # 5. Crear el registro para la Base de Datos
        # Usamos un UUID o el nombre original para el filename
        new_record = models.YieldRecord(
            filename=f"{uuid.uuid4()}_{file.filename}",
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=round(health_idx, 2)
        )
        
        # 6. Guardar en PostgreSQL
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return new_record

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")