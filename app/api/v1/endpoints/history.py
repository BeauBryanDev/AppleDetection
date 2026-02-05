from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas import yield_schema
from typing import List

router = APIRouter()

@router.get("/", response_model=List[yield_schema.YieldResponse])
async def get_all_estimates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener todas las estimaciones con paginación.
    """
    records = db.query(models.YieldRecord)\
        .order_by(models.YieldRecord.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return records

@router.get("/{record_id}", response_model=yield_schema.YieldResponse)
async def get_yield_estimate(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener datos de una estimación previa por ID.
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

@router.delete("/{record_id}")
async def delete_estimate(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para eliminar una estimación por su ID.
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