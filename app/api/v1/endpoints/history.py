from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db import models
from app.schemas import yield_schema
from typing import List
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/records", response_model=List[yield_schema.YieldResponse])
async def get_all_records(
    
    skip: int = Query(0, ge=0, description="Max logs to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max logs to return"),
    db: Session = Depends(get_db)
    
):
    """
    Obtiene todos los registros de estimaciones de rendimiento.
    
    Parámetros:
    - skip: número de registros a saltar (para paginación)
    - limit: número máximo de registros a devolver
    """
    records = db.query(models.YieldRecord).order_by(
        
        desc(models.YieldRecord.created_at)
        
    ).offset(skip).limit(limit).all()
    
    return records


@router.get("/records/{record_id}", response_model=yield_schema.YieldResponse)
async def get_record_by_id(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un registro específico por su ID"""
    record = db.query(models.YieldRecord).filter(
        
        models.YieldRecord.id == record_id
        
    ).first()
    
    if not record:
        
        raise HTTPException(status_code=404, detail=f"Registro con ID {record_id} no encontrado")
    
    return record


@router.get("/analytics", response_model=yield_schema.YieldAnalytics)
async def get_analytics(
    
    days: int = Query(7, ge=1, description="Número de días a analizar"),
    db: Session = Depends(get_db)
    
):
    """
    Obtiene estadísticas agregadas de los últimos N días.
    
    Parámetros:
    - days: número de días a incluir en el análisis
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    records = db.query(models.YieldRecord).filter(
        
        models.YieldRecord.created_at >= cutoff_date
        
    ).all()
    
    if not records:
        return yield_schema.YieldAnalytics(
            total_detected=0,
            healthy_count=0,
            damaged_count=0,
            average_health_index=0.0,
            records_count=0
        )
    
    total_healthy = sum(r.healthy_count for r in records)
    total_damaged = sum(r.damaged_count for r in records)
    average_health = sum(r.health_index for r in records) / len(records)
    
    return yield_schema.YieldAnalytics(
        total_detected=total_healthy + total_damaged,
        healthy_count=total_healthy,
        damaged_count=total_damaged,
        average_health_index=round(average_health, 2),
        records_count=len(records)
    )


@router.get("/records/by-date-range")
async def get_records_by_date_range(
    start_date: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene registros dentro de un rango de fechas específico.
    
    Formato de fechas: YYYY-MM-DD (ej: 2026-02-01)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        # Añadir 1 día al final para incluir todo el día final
        end = end + timedelta(days=1)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    records = db.query(models.YieldRecord).filter(
        models.YieldRecord.created_at >= start,
        models.YieldRecord.created_at < end
    ).order_by(desc(models.YieldRecord.created_at)).all()
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "count": len(records),
        "records": records
    }


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un registro específico por su ID"""
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail=f"Registro con ID {record_id} no encontrado")
    
    db.delete(record)
    db.commit()
    
    return {"message": f"Registro {record_id} eliminado exitosamente"}


@router.get("/stats/health-distribution")
async def get_health_distribution(
    db: Session = Depends(get_db)
):
    """
    Obtiene la distribución de salud de todos los registros.
    Agrupa los registros por rangos de índice de salud.
    """
    records = db.query(models.YieldRecord).all()
    
    # Crear rangos de salud
    ranges = {
        "excellent": 0,      # 90-100
        "good": 0,           # 75-89
        "fair": 0,           # 50-74
        "poor": 0            # 0-49
    }
    
    for record in records:
        health = record.health_index
        if health >= 90:
            ranges["excellent"] += 1
        elif health >= 75:
            ranges["good"] += 1
        elif health >= 50:
            ranges["fair"] += 1
        else:
            ranges["poor"] += 1
    
    total = len(records)
    
    return {
        "total_records": total,
        "distribution": ranges,
        "percentages": {
            "excellent": round((ranges["excellent"] / total * 100), 2) if total > 0 else 0,
            "good": round((ranges["good"] / total * 100), 2) if total > 0 else 0,
            "fair": round((ranges["fair"] / total * 100), 2) if total > 0 else 0,
            "poor": round((ranges["poor"] / total * 100), 2) if total > 0 else 0
        }
    }


@router.get("/stats/top-performers")
async def get_top_performers(
    limit: int = Query(5, ge=1, le=20, description="Número de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene los registros con el mejor índice de salud (top performers).
    """
    records = db.query(models.YieldRecord).order_by(
        desc(models.YieldRecord.health_index)
    ).limit(limit).all()
    
    return {
        "count": len(records),
        "records": records
    }


@router.get("/stats/worst-performers")
async def get_worst_performers(
    limit: int = Query(5, ge=1, le=20, description="Número de registros a devolver"),
    db: Session = Depends(get_db)
):
    """
    Obtiene los registros con el peor índice de salud (worst performers).
    """
    records = db.query(models.YieldRecord).order_by(
        models.YieldRecord.health_index
    ).limit(limit).all()
    
    return {
        "count": len(records),
        "records": records
    }
