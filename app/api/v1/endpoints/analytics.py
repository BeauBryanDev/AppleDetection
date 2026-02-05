from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db import models

router = APIRouter()

@router.get("/dashboard/{orchard_id}")
async def get_orchard_dashboard(orchard_id: int, db: Session = Depends(get_db)):
    # Calculamos métricas globales del huerto
    stats = db.query(
        func.count(models.Prediction.id).label("total_images"),
        func.sum(models.Prediction.total_apples).label("sum_apples"),
        func.avg(models.Prediction.healthy_percentage).label("avg_health")
    ).join(models.Image).join(models.Tree).filter(models.Tree.orchard_id == orchard_id).first()

    # Obtener los últimos 5 registros para una tabla rápida
    recent_activity = db.query(models.Prediction).join(models.Image).join(models.Tree)\
        .filter(models.Tree.orchard_id == orchard_id)\
        .order_by(models.Prediction.id.desc()).limit(5).all()

    return {
        "orchard_id": orchard_id,
        "summary": {
            "images_processed": stats.total_images or 0,
            "total_apples_found": stats.sum_apples or 0,
            "health_score_avg": round(stats.avg_health or 0, 2)
        },
        "recent_detections": [
            {
                "id": p.id,
                "health": p.healthy_percentage,
                "total": p.total_apples,
                "timestamp": p.image.uploaded_at # Aquí verás la hora corregida
            } for p in recent_activity
        ]
    }