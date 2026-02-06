from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import farming as models
from app.db.models.users import User, UserRole
from app.api import deps


router = APIRouter()

# ============================================
# ENDPOINTS ADICIONALES (OPCIONAL)
# ============================================

def validate_orchard_access(
    orchard_id: int,
    current_user: User,
    db: Session
) -> models.Orchard:
    """
    Valida que el usuario tiene acceso al orchard.
    
    Args:
        orchard_id: ID del orchard
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        Orchard: El orchard validado
        
    Raises:
        HTTPException 404: Si el orchard no existe
        HTTPException 403: Si el usuario no tiene permisos
    """
    orchard = db.query(models.Orchard).filter(
        models.Orchard.id == orchard_id
    ).first()
    
    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} not found"
        )
    
    # Si es ADMIN, puede acceder a cualquier orchard
    if current_user.role == UserRole.ADMIN:
        return orchard
    
    # Si no es ADMIN, debe ser el dueño
    if orchard.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access analytics for orchards that you own"
        )
    
    return orchard


@router.get("/dashboard/{orchard_id}")
async def get_orchard_dashboard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene el dashboard completo de un orchard con métricas y actividad reciente.
    
    SEGURIDAD:
    - Solo el dueño del orchard (o ADMIN) puede ver sus métricas
    
    Métricas incluidas:
    - Número de árboles
    - Imágenes procesadas
    - Total de manzanas detectadas
    - Promedio de índice de salud
    - Últimas 5 detecciones
    
    Args:
        orchard_id: ID del orchard
        
    Returns:
        dict: Dashboard con métricas y detecciones recientes
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    #  Validar que el usuario tiene acceso al orchard
    orchard = validate_orchard_access(orchard_id, current_user, db)
    
    # Calcular métricas globales del huerto
    stats = db.query(
        func.count(models.Prediction.id).label("total_images"),
        func.sum(models.Prediction.total_apples).label("sum_apples"),
        func.avg(models.Prediction.healthy_percentage).label("avg_health")
    ).join(models.Image).join(models.Tree).filter(
        models.Tree.orchard_id == orchard_id
    ).first()

    # Obtener los últimos 5 registros para una tabla rápida
    recent_activity = db.query(models.Prediction)\
        .join(models.Image)\
        .join(models.Tree)\
        .filter(models.Tree.orchard_id == orchard_id)\
        .order_by(models.Prediction.id.desc())\
        .limit(5)\
        .all()

    return {
        "orchard_id": orchard.id,
        "orchard_name": orchard.name,
        "summary": {
            "n_trees": db.query(models.Tree.id).filter(
                models.Tree.orchard_id == orchard_id
            ).count(),
            "images_processed": stats.total_images or 0,
            "total_apples_found": stats.sum_apples or 0,
            "health_score_avg": round(stats.avg_health or 0, 2)
        },
        "recent_detections": [
            {
                "prediction_id": p.id,
                "image_id": p.image.id,
                "image_path": p.image.image_path,
                "healthy_apples": p.good_apples,
                "damaged_apples": p.damaged_apples,
                "total_apples": p.total_apples,
                "health_index": p.healthy_percentage,
                "orchard_name": p.image.orchard.name,
                "tree_id": p.image.tree_id,
                "tree_code": p.image.tree.tree_code,
                "timestamp": p.image.uploaded_at
            } for p in recent_activity
        ]
    }


@router.get("/orchard/{orchard_id}/trees-summary")
async def get_trees_summary(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene un resumen de métricas por árbol dentro de un orchard.
    
    Útil para identificar qué árboles tienen mejor/peor salud.
    
    Args:
        orchard_id: ID del orchard
        
    Returns:
        dict: Resumen de métricas por árbol
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    # Validar acceso
    orchard = validate_orchard_access(orchard_id, current_user, db)
    
    # Obtener métricas por árbol
    trees_data = db.query(
        models.Tree.id,
        models.Tree.tree_code,
        models.Tree.tree_type,
        func.count(models.Image.id).label("total_images"),
        func.sum(models.Prediction.total_apples).label("total_apples"),
        func.avg(models.Prediction.healthy_percentage).label("avg_health")
    ).outerjoin(models.Image, models.Tree.id == models.Image.tree_id)\
     .outerjoin(models.Prediction, models.Image.id == models.Prediction.image_id)\
     .filter(models.Tree.orchard_id == orchard_id)\
     .group_by(models.Tree.id, models.Tree.tree_code, models.Tree.tree_type)\
     .all()
    
    return {
        "orchard_id": orchard.id,
        "orchard_name": orchard.name,
        "trees": [
            {
                "tree_id": tree.id,
                "tree_code": tree.tree_code,
                "tree_type": tree.tree_type,
                "total_images": tree.total_images or 0,
                "total_apples_detected": tree.total_apples or 0,
                "avg_health_index": round(tree.avg_health or 0, 2)
            } for tree in trees_data
        ]
    }


@router.get("/user-summary")
async def get_user_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene un resumen global de todos los orchards del usuario.
    
    FARMER: Ve solo sus orchards
    ADMIN: Ve todos los orchards del sistema
    
    Returns:
        dict: Resumen global de orchards y métricas
    """
    # Determinar qué orchards puede ver
    if current_user.role == UserRole.ADMIN:
        orchards = db.query(models.Orchard).all()
    else:
        orchards = db.query(models.Orchard).filter(
            models.Orchard.user_id == current_user.id
        ).all()
    
    # Calcular métricas globales
    total_orchards = len(orchards)
    total_trees = 0
    total_images = 0
    total_apples = 0
    
    orchards_summary = []
    
    for orchard in orchards:
        # Contar árboles
        n_trees = db.query(models.Tree).filter(
            models.Tree.orchard_id == orchard.id
        ).count()
        
        # Estadísticas del orchard
        stats = db.query(
            func.count(models.Prediction.id).label("n_images"),
            func.sum(models.Prediction.total_apples).label("n_apples"),
            func.avg(models.Prediction.healthy_percentage).label("avg_health")
        ).join(models.Image).join(models.Tree).filter(
            models.Tree.orchard_id == orchard.id
        ).first()
        
        n_images = stats.n_images or 0
        n_apples = stats.n_apples or 0
        avg_health = stats.avg_health or 0
        
        total_trees += n_trees
        total_images += n_images
        total_apples += n_apples
        
        orchards_summary.append({
            "orchard_id": orchard.id,
            "orchard_name": orchard.name,
            "location": orchard.location,
            "n_trees": n_trees,
            "images_processed": n_images,
            "apples_detected": n_apples,
            "avg_health": round(avg_health, 2)
        })
    
    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_role": current_user.role.value,
        "global_summary": {
            "total_orchards": total_orchards,
            "total_trees": total_trees,
            "total_images_processed": total_images,
            "total_apples_detected": total_apples
        },
        "orchards": orchards_summary
    }


@router.get("/orchard/{orchard_id}/health-trend")
async def get_health_trend(
    orchard_id: int,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene la tendencia del índice de salud del orchard en el tiempo.
    
    Útil para gráficos de línea mostrando evolución.
    
    Args:
        orchard_id: ID del orchard
        limit: Número de registros a retornar (default: 30)
        
    Returns:
        dict: Serie temporal del health index
    """
    # Validar acceso
    orchard = validate_orchard_access(orchard_id, current_user, db)
    
    # Obtener predicciones ordenadas por fecha
    predictions = db.query(
        models.Prediction.id,
        models.Prediction.healthy_percentage,
        models.Image.uploaded_at
    ).join(models.Image)\
     .join(models.Tree)\
     .filter(models.Tree.orchard_id == orchard_id)\
     .order_by(models.Image.uploaded_at.desc())\
     .limit(limit)\
     .all()
    
    return {
        "orchard_id": orchard.id,
        "orchard_name": orchard.name,
        "data_points": len(predictions),
        "trend": [
            {
                "timestamp": pred.uploaded_at.isoformat(),
                "health_index": pred.healthy_percentage
            } for pred in reversed(predictions)  # Ordenar cronológicamente
        ]
    }