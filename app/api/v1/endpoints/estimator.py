from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import time
import os
import json

from app.db.session import get_db
from app.db.models import farming as models
from app.db.models.users import User, UserRole
from app.models.inference import model_engine
from app.utils.image_processing import draw_cyberpunk_detections
from app.schemas import yield_schema
from app.api import deps
from fastapi.responses import Response
from app.core.logging import logger

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
start_time = time.perf_counter()

@router.post("/estimate")
async def create_yield_estimate(
    file: UploadFile = File(...),
    orchard_id: Optional[int] = None,
    tree_id: Optional[int] = None,
    confidence_threshold: float = 0.5,
    preview: bool = True,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional)
) :
    """
    Run apple detection on an uploaded image.

    OPERATION MODES:
    1. GUEST MODE (no authentication):
       - orchard_id and tree_id are optional/ignored
       - No DB save; returns inference results only
    2. AUTHENTICATED MODE + PREVIEW:
       - preview=True (default): Process image but don't save to DB (for user review)
       - preview=False: Save to DB immediately
    3. AUTHENTICATED MODE + SAVE:
       - Saves to DB: Image, Prediction, Detections, YieldRecord

    Args:
        file: Image file to process
        orchard_id: Orchard ID (required for auth mode)
        tree_id: Tree ID (optional)
        confidence_threshold: Confidence threshold for detections
        preview: If True, process but don't save to DB (default: True)
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
    
    # Authenticated mode validation for orchard_id and tree_id
    if not is_guest_mode:
        if orchard_id is None and tree_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tree ID cannot be provided without an Orchard ID."
            )
        # Validate orchard and tree if in auth mode and orchard_id is provided
        if orchard_id is not None:
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
        deep_confidence_threshold = 0.64*confidence_threshold
        # Run inference
        detection_results = model_engine.run_inference(image_bytes, deep_confidence_threshold)
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
        
        
        #   Generate unique filename for storage and record
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        image_save_path = f"uploads/{unique_filename}"

        # Initialize prediction_id and record_id
        prediction_id = None
        record_id = None

        # Only save to database if NOT in preview mode
        if not preview:
            # Save to YieldRecord (global history)
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
            record_id = new_record.id
            print(f" Record saved with ID: {new_record.id}")

        if not preview and not is_guest_mode and orchard_id is not None:
            # 2.1 Guardar Image
            new_image = models.Image(
                user_id=current_user.id,
                orchard_id=orchard_id,
                tree_id=tree_id,  # Puede ser None si no se especificó
                image_path=image_save_path
            )
            db.add(new_image)
            db.flush()
            
            
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

        # Commit only if not in preview mode
        if not preview:
            db.commit()
            print(f"✅ Saved to database - Record ID: {record_id}, Prediction ID: {prediction_id}")
        

        processed_image = draw_cyberpunk_detections(
        image_bytes, 
        detections_data, 
        threshold=0.85*confidence_threshold
    )
        
        os.makedirs("uploads", exist_ok=True)
        
        with open(image_save_path, "wb") as f:
            f.write(processed_image)

        if preview:
            print(f"🔍 Preview mode - Image processed but NOT saved to database")
        else:
            print(f"💾 Image saved: {image_save_path}")
            print(f"💾 YieldRecord ID: {record_id}")
            if prediction_id:
                print(f"💾 Prediction ID: {prediction_id}")
        
        # Return Response with processed image and headers
        end_time = time.perf_counter()
        total_time = end_time - start_time
        ms = (end_time - start_time) / 1000
        logger.warning("Model inference slow", inference_time_ms=ms)
        #logger.warning("Model inference slow", extra={"inference_time_ms": ms})
        
        return Response(
            content=processed_image,
            media_type="image/jpeg",
            headers={
                "X-Healthy-Count": str(healthy),
                "X-Damaged-Count": str(damaged),
                "X-Total-Count": str(total),
                "X-Health-Index": str(health_idx),
                "X-Inference-Time-Ms": str(inference_time),
                "X-Record-ID": str(record_id) if record_id else "None",
                "X-Prediction-ID": str(prediction_id) if prediction_id else "None",
                "X-Preview-Mode": str(preview).lower(),
                "X-Mode": "guest" if is_guest_mode else "authenticated",
                "X-Orchard-ID": str(orchard_id) if orchard_id else "None",
                "X-Tree-ID": str(tree_id) if tree_id else "None",
                "X-Confidences": json.dumps(detections_data["confidences"]),
                "X-Image-Path": image_save_path,
                "Access-Control-Expose-Headers": "X-Healthy-Count, X-Damaged-Count, X-Total-Count, X-Health-Index, X-Inference-Time-Ms, X-Record-ID, X-Prediction-ID, X-Confidences, X-Preview-Mode, X-Image-Path"
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
    

@router.post("/save-detection")
async def save_detection_after_review(
    request: yield_schema.SaveDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Save detection results to database after user review.

    This endpoint is called after user reviews the preview and decides to save.

    Args:
        request: Detection data including counts, notes, and orchard/tree IDs
        db: Database session
        current_user: Authenticated user

    Returns:
        dict: Success message with record and prediction IDs
    """
    try:
        # Extract filename from path
        filename = request.image_path.split('/')[-1] if '/' in request.image_path else request.image_path

        # Validate orchard ownership if provided
        orchard = None
        tree = None
        if request.orchard_id:
            orchard, tree = validate_orchard_and_tree(
                request.orchard_id,
                request.tree_id,
                current_user,
                db
            )

        # Save to YieldRecord
        new_record = models.YieldRecord(
            filename=filename,
            healthy_count=request.healthy_count,
            damaged_count=request.damaged_count,
            total_count=request.total_count,
            health_index=request.health_index,
            user_id=current_user.id
        )
        db.add(new_record)
        db.flush()

        prediction_id = None

        # Save detailed prediction ONLY if both orchard_id AND tree_id are provided
        # (Images table requires tree_id to be non-null)
        if request.orchard_id and request.tree_id:
            # Create image record with full traceability
            new_image = models.Image(
                user_id=current_user.id,
                orchard_id=request.orchard_id,
                tree_id=request.tree_id,
                image_path=request.image_path
            )
            db.add(new_image)
            db.flush()

            # Create prediction with user notes
            new_prediction = models.Prediction(
                image_id=new_image.id,
                model_version="YOLOv8s-Cyberpunk-v1",
                total_apples=request.total_count,
                good_apples=request.healthy_count,
                damaged_apples=request.damaged_count,
                healthy_percentage=request.health_index,
                user_notes=request.user_notes,
                inference_time_ms=request.inference_time_ms 
            )
            db.add(new_prediction)
            db.flush()
            prediction_id = new_prediction.id

            logger.info(f"✅ Saved with full traceability - Image ID: {new_image.id}, Prediction ID: {prediction_id}")
        elif request.orchard_id:
            logger.info(f"⚠️  Saved to YieldRecord only (no tree_id provided)")

        db.commit()

        logger.info(
            f"✅ Detection saved after review - User: {current_user.id}, "
            f"Record: {new_record.id}, Prediction: {prediction_id}"
        )

        return {
            "status": "success",
            "message": "Detection saved successfully",
            "record_id": new_record.id,
            "prediction_id": prediction_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving detection: {str(e)}"
        )


@router.patch("/prediction/{prediction_id}/notes")
async def update_prediction_notes(

    prediction_id: int,
    notes_data: dict, # get the notes data from the frontend
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    
    """_summary_

    Raises:
        HTTPException: If prediction not found
        HTTPException: If user is not authorized to edit notes

    Returns:
        dict: Success message
    """
    # search for the prediction
    prediction = db.query(models.Prediction).filter(
        models.Prediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # validate ownership
    image = db.query(models.Image).filter(models.Image.id == prediction.image_id).first()
    if image.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this note")

    # Update the notes
    prediction.user_notes = notes_data.get("notes")
    db.commit()
    
    return {"status": "success", "message": "Note updated"}