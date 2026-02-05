from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db import models

router = APIRouter()

@router.get("/summary/{orchard_id}")
async def get_orchard_summary(orchard_id: int, db: Session = Depends(get_db)):
    # 1. Total de manzanas detectadas en el huerto
    stats = db.query(
        func.sum(models.Prediction.total_apples).label("total"),
        func.avg(models.Prediction.healthy_percentage).label("avg_health"),
        func.count(models.Prediction.id).label("total_images")
    ).join(models.Image).join(models.Tree).filter(models.Tree.orchard_id == orchard_id).first()

    # 2. Conteo de árboles en este huerto
    tree_count = db.query(models.Tree).filter(models.Tree.orchard_id == orchard_id).count()

    return {
        "orchard_id": orchard_id,
        "total_apples_detected": stats.total or 0,
        "average_health_index": round(stats.avg_health or 0, 2),
        "images_analyzed": stats.total_images,
        "trees_registered": tree_count,
        "status": "Optimal" if (stats.avg_health or 0) > 80 else "Attention Required"
    }