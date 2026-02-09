from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import time
import os

from app.db.session import get_db
from app.db.models import farming as models
from app.db.models.users import User, UserRole
from app.models.inference import model_engine
from app.utils.image_processing import draw_cyberpunk_detections
from app.schemas import yield_schema
from app.api import deps
from fastapi.responses import Response


router = APIRouter()


def validate_orchard_and_tree(
    orchard_id: Optional[int],
    tree_id: Optional[int],
    current_user: User,
    db: Session
) -> tuple[Optional[models.Orchard], Optional[models.Tree]]:
    """
    Valida que el orchard y tree existen y pertenecen al usuario.
    
    Args:
        orchard_id: ID del orchard (opcional para guest mode)
        tree_id: ID del árbol (opcional)
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        tuple: (orchard, tree) validados o (None, None) si no aplica
        
    Raises:
        HTTPException 400: Si faltan datos requeridos
        HTTPException 404: Si orchard/tree no existen
        HTTPException 403: Si no tiene permisos
    """
    # Si no hay orchard_id, modo guest/simple (no validar nada)
    if orchard_id is None:
        return None, None
    
    # Si hay orchard_id, validar que existe
    orchard = db.query(models.Orchard).filter(
        models.Orchard.id == orchard_id
    ).first()
    
    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} not found"
        )
    
    # Validar ownership del orchard (excepto ADMIN)
    if current_user.role != UserRole.ADMIN:
        if orchard.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to orchards that you own"
            )
    
    # Si no hay tree_id, retornar solo orchard validado
    if tree_id is None:
        return orchard, None
    
    # Si hay tree_id, validar que existe y pertenece al orchard
    tree = db.query(models.Tree).filter(
        models.Tree.id == tree_id,
        models.Tree.orchard_id == orchard_id
    ).first()
    
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_id} not found in orchard {orchard_id}"
        )
    
    return orchard, tree


def validate_image_file(file: UploadFile):
    """
    Valida que el archivo sea una imagen válida.
    
    Args:
        file: Archivo subido
        
    Raises:
        HTTPException 400: Si el formato no es válido
    """
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_types)}"
        )


# ============================================
# ENDPOINT PRINCIPAL
# ============================================

@router.post("/estimate")
async def create_yield_estimate(
    file: UploadFile = File(...),
    orchard_id: Optional[int] = None,
    tree_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional)
):
    """
    Ejecuta detección de manzanas en una imagen.
    
    MODO DE OPERACIÓN:
    1. GUEST MODE (sin autenticación):
       - orchard_id y tree_id deben ser None
       - Solo guarda en YieldRecord
       - user_id = None
       
    2. AUTHENTICATED MODE (con token):
       - Puede enviar orchard_id y tree_id (opcional)
       - Si envía orchard_id, valida ownership
       - Guarda en YieldRecord + estructura completa
       - user_id asignado automáticamente
    
    Args:
        file: Imagen a procesar (JPG/PNG)
        orchard_id: ID del orchard (opcional)
        tree_id: ID del árbol (opcional)
        
    Returns:
        Response: Imagen procesada con detecciones dibujadas
        
    Headers de respuesta:
        X-Healthy-Count: Número de manzanas sanas
        X-Damaged-Count: Número de manzanas dañadas
        X-Total-Count: Total de manzanas detectadas
        X-Health-Index: Índice de salud (%)
        X-Record-ID: ID del registro en YieldRecord
        X-Prediction-ID: ID de la predicción (solo en modo authenticated)
        X-Mode: "guest" o "authenticated"
        
    Raises:
        400: Formato de imagen inválido o datos faltantes
        403: Intento de acceder a orchard/tree de otro usuario
        404: Orchard o tree no encontrado
        500: Error en el servidor
    """
    # 1. VALIDACIONES INICIALES - NO MODIFICAR
    validate_image_file(file)
    
    # Determinar modo de operación
    is_guest_mode = current_user is None
    
    # En modo guest, no se permite orchard_id/tree_id
    if is_guest_mode and (orchard_id is not None or tree_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest users cannot specify orchard_id or tree_id. Please login first."
        )
    
    # En modo authenticated, validar orchard y tree si se proporcionan
    orchard = None
    tree = None
    if not is_guest_mode and orchard_id is not None:
        orchard, tree = validate_orchard_and_tree(
            orchard_id, 
            tree_id, 
            current_user, 
            db
        )
    

    # 2. LEER Y VALIDAR IMAGEN

    
    try:
        start_time = time.time()
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # 3. EJECUTAR INFERENCIA DEL MODELO

        detection_results = model_engine.run_inference(image_bytes)
        print(f"\n{'='*60}")
        print(f"Archivo: {file.filename}")
        print(f"Resultados: {detection_results}")
        print(f"{'='*60}\n")
        
        # Logging para debugging
        print(f"\n{'='*60}")
        print(f" File: {file.filename}")
        print(f" User: {current_user.name if current_user else 'GUEST'}")
        print(f" Orchard: {orchard_id or 'None'}")
        print(f" Tree: {tree_id or 'None'}")
        print(f" Results: {detection_results['counts']}")
        print(f"{'='*60}\n")
        
        # Extraer resultados
        counts = detection_results["counts"]
        detections_data = detection_results["detections"]
        
        total = counts["total"]
        healthy = counts["apple"]
        damaged = counts["damaged_apple"]
        health_idx = round((healthy / total * 100) if total > 0 else 0.0, 2)
        inference_time = round((time.time() - start_time) * 1000, 2)
        
  
        # 4. PERSISTENCIA DUAL (GUEST vs AUTHENTICATED)
        
        # Generar filename único
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        image_save_path = f"uploads/{unique_filename}"
        
        # --- PASO 1: SIEMPRE guardar en YieldRecord (historial global) ---
        new_record = models.YieldRecord(
            filename=unique_filename,
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=health_idx,
            user_id=current_user.id if current_user else None
        )
        db.add(new_record)
        db.flush()  # Para obtener el ID
        
        # --- PASO 2: SI MODO AUTHENTICATED + orchard_id → Guardar estructura completa ---
        prediction_id = None
        
        if not is_guest_mode and orchard_id is not None:
            # 2.1 Guardar Image
            new_image = models.Image(
                user_id=current_user.id,
                orchard_id=orchard_id,
                tree_id=tree_id,  # Puede ser None si no se especificó
                image_path=image_save_path
            )
            db.add(new_image)
            db.flush()
            
            # 2.2 Guardar Prediction vinculada
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
            
            # 2.3 Guardar Detections (Bulk insert)
            if len(detections_data["boxes"]) > 0:
                new_detections = [
                    models.Detection(
                        prediction_id=prediction_id,
                        class_label="apple" if class_id == 0 else "damaged_apple",
                        confidence=conf,
                        x_min=box[0], 
                        y_min=box[1],
                        x_max=box[0] + box[2], 
                        y_max=box[1] + box[3]
                    )
                    for box, class_id, conf in zip(
                        detections_data["boxes"],
                        detections_data["class_ids"],
                        detections_data["confidences"]
                    )
                ]
                db.bulk_save_objects(new_detections)
        
        # Commit de todo
        db.commit()
        

        # 5. GENERAR IMAGEN CON DETECCIONES (CYBERPUNK STYLE)

        
        processed_image = draw_cyberpunk_detections(image_bytes, detections_data)
        
        # 6. GUARDAR IMAGEN PROCESADA EN DISCO
        
        # Asegurar que el directorio uploads existe
        os.makedirs("uploads", exist_ok=True)
        
        with open(image_save_path, "wb") as f:
            f.write(processed_image)
        
        print(f" Image saved: {image_save_path}")
        print(f" YieldRecord ID: {new_record.id}")
        if prediction_id:
            print(f" Prediction ID: {prediction_id}")
        
        # ============================================
        # 7. RETORNAR RESPUESTA
        # ============================================
        
        return Response(
            content=processed_image,
            media_type="image/jpeg",
            headers={
                "X-Healthy-Count": str(healthy),
                "X-Damaged-Count": str(damaged),
                "X-Total-Count": str(total),
                "X-Health-Index": str(health_idx),
                "X-Inference-Time-Ms": str(inference_time),
                "X-Record-ID": str(new_record.id),
                "X-Prediction-ID": str(prediction_id) if prediction_id else "None",
                "X-Mode": "guest" if is_guest_mode else "authenticated",
                "X-Orchard-ID": str(orchard_id) if orchard_id else "None",
                "X-Tree-ID": str(tree_id) if tree_id else "None"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validaciones)
        raise
        
    except Exception as e:
        # Rollback en caso de error
        db.rollback()
        
        print(f"[X  ERROR] Error en estimación: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/history")
async def get_estimation_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene el historial de estimaciones del usuario actual.
    
    Solo muestra registros del usuario autenticado.
    ADMIN puede ver todo con un endpoint separado.
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        
    Returns:
        List[YieldRecord]: Historial de estimaciones
    """
    records = db.query(models.YieldRecord).filter(
        models.YieldRecord.user_id == current_user.id
    ).order_by(
        models.YieldRecord.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return records


@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene estadísticas globales del usuario.
    
    Returns:
        dict: Estadísticas de detecciones del usuario
    """
    from sqlalchemy import func
    
    stats = db.query(
        func.count(models.YieldRecord.id).label("total_estimations"),
        func.sum(models.YieldRecord.total_count).label("total_apples"),
        func.avg(models.YieldRecord.health_index).label("avg_health_index")
    ).filter(
        models.YieldRecord.user_id == current_user.id
    ).first()
    
    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "total_estimations": stats.total_estimations or 0,
        "total_apples_detected": stats.total_apples or 0,
        "average_health_index": round(stats.avg_health_index or 0, 2)
    }


@router.delete("/record/{record_id}")
async def delete_estimation_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Elimina un registro de estimación.
    
    Solo el dueño (o ADMIN) puede eliminar.
    
    Args:
        record_id: ID del registro a eliminar
        
    Returns:
        dict: Mensaje de confirmación
        
    Raises:
        404: Si el registro no existe
        403: Si no tiene permisos
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} not found"
        )
    
    # Validar ownership (excepto ADMIN)
    if current_user.role != UserRole.ADMIN:
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own records"
            )
    
    # Eliminar archivo físico si existe
    if os.path.exists(f"uploads/{record.filename}"):
        os.remove(f"uploads/{record.filename}")
    
    db.delete(record)
    db.commit()
    
    return {
        "message": "Record deleted successfully",
        "record_id": record_id
    }