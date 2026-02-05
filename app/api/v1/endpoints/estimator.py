from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import time
from app.db.session import get_db
from app.db import models
from app.models.inference import model_engine
from fastapi.responses import Response
from app.utils.image_processing import draw_cyberpunk_detections
from app.schemas import yield_schema


router = APIRouter()

@router.post("/estimate")
async def create_yield_estimate(
    file: UploadFile = File(...),
    orchard_id: Optional[int] = None, # Ahora es opcional
    tree_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen JPG o PNG")

    try:
        start_time = time.time()
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="La imagen está vacía")
        
        # 1. Ejecutar inferencia
        detection_results = model_engine.run_inference(image_bytes)
        
        print(f"\n{'='*60}")
        print(f"Archivo: {file.filename}")
        print(f"Resultados: {detection_results}")
        print(f"{'='*60}\n")
        
        counts = detection_results["counts"]
        detections_data = detection_results["detections"]
        
        total = counts["total"]
        healthy = counts["apple"]
        damaged = counts["damaged_apple"]
        health_idx = round((healthy / total * 100) if total > 0 else 0.0, 2)
        inference_time = round((time.time() - start_time) * 1000, 2)

        # ---------------------------------------------------------
        # LÓGICA DE PERSISTENCIA DUAL
        # ---------------------------------------------------------
        
        # SIEMPRE guardamos en YieldRecord (Para histórico global/Guest mode)
        new_record = models.YieldRecord(
            filename=f"{uuid.uuid4()}_{file.filename}",
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=health_idx
        )
        db.add(new_record)
        
        # SI hay un orchard_id, guardamos en la estructura compleja (MVP)
        prediction_id = None
        if orchard_id:
            # 1. Guardar Imagen
            new_image = models.Image(
                tree_id=tree_id,
                image_path=f"uploads/{new_record.filename}"
            )
            db.add(new_image)
            db.flush() 

            # 2. Guardar Predicción vinculada
            new_prediction = models.Prediction(
                image_id=new_image.id,
                model_version="YOLOv8s-Cyberpunk-v1",
                total_apples=total,
                good_apples=healthy,
                damaged_apples=damaged,
                healthy_percentage=health_idx,
                inference_time_ms=inference_time
            )
            db.add(new_prediction)
            db.flush()
            prediction_id = new_prediction.id

            # 3. Guardar Detecciones (Bulk)
            new_detections = [
                models.Detection(
                    prediction_id=prediction_id,
                    class_label="apple" if class_id == 0 else "damaged_apple",
                    confidence=conf,
                    x_min=box[0], y_min=box[1],
                    x_max=box[0] + box[2], y_max=box[1] + box[3]
                )
                for box, class_id, conf in zip(
                    detections_data["boxes"], 
                    detections_data["class_ids"], 
                    detections_data["confidences"]
                )
            ]
            db.bulk_save_objects(new_detections)

        db.commit()
        # ---------------------------------------------------------

        # Generar imagen visual
        processed_image = draw_cyberpunk_detections(image_bytes, detections_data)
        
        return Response(
            content=processed_image,
            media_type="image/jpeg",
            headers={
                "X-Healthy-Count": str(healthy),
                "X-Damaged-Count": str(damaged),
                "X-Health-Index": str(health_idx),
                "X-Record-ID": str(new_record.id),
                "X-Prediction-ID": str(prediction_id) if prediction_id else "None"
            }
        )
        
    except Exception as e:
        
        db.rollback()
        
        print(f"Error: {str(e)}")
        
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/estimate/{record_id}", response_model=yield_schema.YieldResponse)

async def get_yield_estimate(
    
    record_id: int,
    db: Session = Depends(get_db)
    
):
    """
    Obtener datos de una estimación previa por ID.
    Args:
        record_id: ID del registro en la base de datos
        
    Returns:
        YieldResponse: Datos completos de la estimación
    
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró el registro con ID {record_id}"
        )
    
    return record

@router.get("/estimates", response_model=list[yield_schema.YieldResponse])

async def get_all_estimates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener todas las estimaciones con paginación.
    
    Args:
        skip: Número de registros a saltar (default: 0)
        limit: Número máximo de registros a retornar (default: 100)
        
    Returns:
        List[YieldResponse]: Lista de todas las estimaciones
    """
    records = db.query(models.YieldRecord)\
        .order_by(models.YieldRecord.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return records


@router.delete("/estimate/{record_id}")

async def delete_estimate(
    
    record_id: int,
    db: Session = Depends(get_db)
    
):
    """
    Endpoint para eliminar una estimación por su ID.
    
    Args:
        record_id: ID del registro a eliminar
        
    Returns:
        dict: Mensaje de confirmación
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró el registro con ID {record_id}"
        )
    
    db.delete(record)
    db.commit()
    
    return {
        "message": f"Registro {record_id} eliminado exitosamente",
        "deleted_id": record_id
    }






