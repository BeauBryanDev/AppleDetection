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
    Validate that the orchard and tree exist and belong to the user.

    Args:
        orchard_id: Orchard ID (optional for guest mode)
        tree_id: Tree ID (optional)
        current_user: Authenticated user
        db: Database session

    Returns:
        tuple: (orchard, tree) if validated, or (None, None) if not applicable

    Raises:
        HTTPException 400: If required data is missing
        HTTPException 404: If orchard/tree not found
        HTTPException 403: If no permissions
    """
    # if not orchard_id , return None for guest ussage. 
    if orchard_id is None:
        
        return None, None
    
    # Validate orchard exists
    orchard = db.query(models.Orchard).filter(
        models.Orchard.id == orchard_id
    ).first()
    
    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} not found"
        )
    
    # Validate orchard ownership
    if current_user.role != UserRole.ADMIN:
        if orchard.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to orchards that you own"
            )
    
    # If not tree return only valid orchard id 
    if tree_id is None:
        return orchard, None
    
    # if not tree id , return only existing rochard tree. 
    tree = db.query(models.Tree).filter(
        models.Tree.id == tree_id,
        models.Tree.orchard_id == orchard_id
    ).first()
    # If no tree_id, return validated orchard only
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_id} not found in orchard {orchard_id}"
        )
    
    return orchard, tree


def validate_image_file(file: UploadFile):
    """
    Validate that the uploaded file is a valid image.

    Args:
        file: Uploaded file

    Raises:
        HTTPException 400: If format is invalid
    """
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_types)}"
        )

# MAIN ENDPOINT FOR ESTIMATOR.

@router.post("/estimate")
async def create_yield_estimate(
    file: UploadFile = File(...),
    orchard_id: Optional[int] = None,
    tree_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional)
) :
    """
    Run apple detection on an uploaded image.

    OPERATION MODES:
    1. GUEST MODE (no authentication):
       - orchard_id and tree_id are optional/ignored
       - No DB save; returns inference results only
    2. AUTHENTICATED MODE:
       - orchard_id required for traceability
       - tree_id optional
       - Saves to DB: Image, Prediction, Detections, YieldRecord

    Args:
        file: Image file to process
        orchard_id: Orchard ID (required for auth mode)
        tree_id: Tree ID (optional)
        db: Database session
        current_user: Optional authenticated user

    Returns:
        YieldEstimateResponse: Yield counts, health index, processed image (JPEG)

    Raises:
        HTTPException: On validation or processing errors
    """

    validate_image_file(file)
    

    is_guest_mode = current_user is None
    
    #   Guest mode: no orchard_id/tree_id
    if is_guest_mode and (orchard_id is not None or tree_id is not None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest users cannot specify orchard_id or tree_id. Please login first."
        )
    
    # Validate orchard and tree if in auth mode
    orchard = None
    tree = None
    if not is_guest_mode and orchard_id is not None:
        orchard, tree = validate_orchard_and_tree(
            orchard_id, 
            tree_id, 
            current_user, 
            db
        )
    

    # Read image bytes for inference
    try:
        start_time = time.time()
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # Run inference

        detection_results = model_engine.run_inference(image_bytes)
        print(f"\n{'='*60}")
        print(f"Archivo: {file.filename}")
        print(f"Resultados: {detection_results}")
        print(f"{'='*60}\n")
        
        #   Logging for debugging
        print(f"\n{'='*60}")
        print(f" File: {file.filename}")
        print(f" User: {current_user.name if current_user else 'GUEST'}")
        print(f" Orchard: {orchard_id or 'None'}")
        print(f" Tree: {tree_id or 'None'}")
        print(f" Results: {detection_results['counts']}")
        print(f"{'='*60}\n")
        
        #   Extract results
        counts = detection_results["counts"]
        detections_data = detection_results["detections"]
        red_apples = counts["red_apple"] 
        green_apple = counts["green_apple"]
        healthy = red_apples + green_apple
        damaged = counts["damaged_apple"]
        total = counts["total"]
        
        
        health_idx = round((healthy / total * 100) if total > 0 else 0.0, 2)
        inference_time = round((time.time() - start_time) * 1000, 2)
        
  
        #   Save to DB (GUEST vs AUTHENTICATED)
        
        #   Generate unique filename for storage and record
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        image_save_path = f"uploads/{unique_filename}"
        
        # Always save to YieldRecord (global history)
        new_record = models.YieldRecord(
            filename=unique_filename,
            healthy_count=healthy,
            damaged_count=damaged,
            total_count=total,
            health_index=health_idx,
            user_id=current_user.id if current_user else None
        )
        db.add(new_record)
        db.flush() 
        
        # Initialize prediction_id (will be set if authenticated and saving to DB)
        prediction_id = None
        print(f" Record saved with ID: {new_record.id}")
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
            print(f" Prediction saved with ID: {new_prediction.id}")
            prediction_id = new_prediction.id
            print(f" Prediction ID: {prediction_id}")
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
    Get the user's estimation history.

    Shows only the authenticated user's records (admin separate endpoint possible).

    Args:
        skip: Number of records to skip (pagination)
        limit: Max records to return

    Returns:
        list[YieldRecord]: Estimation history
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
    Get global user statistics.

    Returns:
        dict: User detection stats
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
    Delete an estimation record.

    Only the owner (or ADMIN) can delete.

    Args:
        record_id: Record ID to delete

    Returns:
        dict: Confirmation message

    Raises:
        404: If record not found
        403: If no permissions
    """
    record = db.query(models.YieldRecord).filter(
        models.YieldRecord.id == record_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} not found"
        )
    
    # Validate ownership (unless admin)
    if current_user.role != UserRole.ADMIN:
        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own records"
            )
    
    # Delete physical file if exists
    if os.path.exists(f"uploads/{record.filename}"):
        os.remove(f"uploads/{record.filename}")
    
    db.delete(record)
    db.commit()
    
    return {
        "message": "Record deleted successfully",
        "record_id": record_id
    }