from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.db import models
from app.schemas import yield_schema
from app.models.inference import model_engine
from fastapi.responses import Response
from app.utils.image_processing import draw_cyberpunk_detections


router = APIRouter()

@router.post("/estimate")  # ← Sin response_model
async def create_yield_estimate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint para procesar imagen y retornar imagen con detecciones dibujadas.
    También guarda los resultados en la base de datos.
    
    Returns:
        Response: Imagen JPEG con bounding boxes dibujados
        
    Headers:
        X-Healthy-Count: Número de manzanas sanas detectadas
        X-Damaged-Count: Número de manzanas dañadas detectadas
        X-Total-Count: Total de manzanas detectadas
        X-Health-Index: Índice de salud (porcentaje de manzanas sanas)
        X-Record-ID: ID del registro guardado en base de datos
        
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        
        raise HTTPException(
            
            status_code=400, 
            detail="El archivo debe ser una imagen JPG o PNG"
            
        )

    try:
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="La imagen está vacía")
        
        # Ejecutar inferencia
        detection_results = model_engine.run_inference(image_bytes)
        
        print(f"\n{'='*60}")
        print(f"Archivo: {file.filename}")
        print(f"Resultados: {detection_results}")
        print(f"{'='*60}\n")
        
        healthy = detection_results.get("counts", {}).get("apple", 0)
        damaged = detection_results.get("counts", {}).get("damaged_apple", 0)
        total = detection_results.get("counts", {}).get("total", 0)
        
        health_idx = (healthy / total * 100) if total > 0 else 0.0
        
        # Guardar en BD
        new_record = models.YieldRecord(
            filename=f"{uuid.uuid4()}_{file.filename}",
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=round(health_idx, 2)
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        print(f" Registro guardado: ID={new_record.id}")
        
        # Dibujar detecciones
        processed_image = draw_cyberpunk_detections(
            
            image_bytes, 
            detection_results["detections"]
            
        )
        
        # : Enviar metadata en headers
        return Response(
            
            content=processed_image, 
            media_type="image/jpeg",
            headers={
                
                "X-Healthy-Count": str(healthy),
                "X-Damaged-Count": str(damaged),
                "X-Total-Count": str(total),
                "X-Health-Index": str(round(health_idx, 2)),
                "X-Record-ID": str(new_record.id)
            }
            
        )
        
    except Exception as e:
        
        db.rollback()
        
        print(f"Fatal! Server error: {str(e)}") 
        
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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






