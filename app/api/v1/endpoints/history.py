from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.api import deps
from app.db.models.users import User, UserRole
from app.schemas import yield_schema
from typing import List

router = APIRouter()

@router.get("/", response_model=List[yield_schema.YieldResponse])
async def get_all_estimates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Endpoint para obtener todas las estimaciones con paginación.
    FARMER: Solo ve sus propios registros.
    ADMIN: Ve todos los registros del sistema.
    """
    query = db.query(models.YieldRecord)
    
    # Filter by user if not admin
    if current_user.role != UserRole.ADMIN:
        query = query.filter(models.YieldRecord.user_id == current_user.id)
        
    records = query.order_by(models.YieldRecord.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return records

@router.get("/{record_id}", response_model=yield_schema.YieldResponse)
async def get_yield_estimate(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtener datos de una estimación previa por ID.
    Valida que el registro pertenezca al usuario o sea admin.
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No se encontró el registro con ID {record_id}"
        )
    
    # Check ownership
    if current_user.role != UserRole.ADMIN and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este registro"
        )
    
    return record

@router.delete("/{record_id}")
async def delete_estimate(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Endpoint para eliminar una estimación por su ID.
    Valida que el registro pertenezca al usuario o sea admin.
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No se encontró el registro con ID {record_id}"
        )
    
    # Check ownership
    if current_user.role != UserRole.ADMIN and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este registro"
        )
    
    db.delete(record)
    db.commit()
    
    return {
        "message": f"Registro {record_id} eliminado exitosamente",
        "deleted_id": record_id
    }