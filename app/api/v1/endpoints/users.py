from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas import user_schema, orchard_schema

router = APIRouter()

# TODO: Implement proper auth. For now, defaulting to user_id=1
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- PERFIL DE USUARIO ---
@router.patch("/me", response_model=user_schema.UserResponse)
async def update_my_profile(
    obj_in: user_schema.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) 
):
    """El Farmer solo edita su nombre y teléfono"""
    if obj_in.name:
        current_user.name = obj_in.name
    if obj_in.phone_number:
        current_user.phone_number = obj_in.phone_number
    db.commit()
    db.refresh(current_user)
    return current_user

# --- GESTIÓN DE HUERTOS (ORCHARDS) ---
@router.post("/orchards", response_model=orchard_schema.Orchard)
async def create_orchard(orchard: orchard_schema.Create, db: Session = Depends(get_db)):
    new_orchard = models.Orchard(**orchard.dict())
    db.add(new_orchard)
    db.commit()
    db.refresh(new_orchard)
    return new_orchard

@router.patch("/orchards/{orchard_id}", response_model=orchard_schema.Orchard)
async def update_orchard_trees(orchard_id: int, n_trees: int, db: Session = Depends(get_db)):
    db_orchard = db.query(models.Orchard).filter(models.Orchard.id == orchard_id).first()
    if not db_orchard:
        raise HTTPException(status_code=404, detail="Huerto no encontrado")
    
    # Solo permitimos cambiar n_trees según tu regla de negocio
    db_orchard.n_trees = n_trees
    db.commit()
    db.refresh(db_orchard)
    return db_orchard

@router.delete("/orchards/{orchard_id}")
async def delete_orchard(orchard_id: int, db: Session = Depends(get_db)):
    db_orchard = db.query(models.Orchard).filter(models.Orchard.id == orchard_id).first()
    if not db_orchard:
        raise HTTPException(status_code=404, detail="Huerto no encontrado")
    
    db.delete(db_orchard)
    db.commit()
    return {"message": "Huerto y sus datos asociados eliminados"}

@router.delete("/trees/{orchard_id}/{tree_id}")
async def delete_tree(
    orchard_id: int, 
    tree_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina un árbol específico perteneciente a un huerto.
    Verifica que el árbol pertenezca al huerto indicado.
    """
    # Verificar que el árbol existe y pertenece al huerto
    tree = db.query(models.Tree).filter(
        models.Tree.id == tree_id,
        models.Tree.orchard_id == orchard_id
    ).first()
    
    if not tree:
        raise HTTPException(
            status_code=404, 
            detail="Árbol no encontrado en el huerto especificado"
        )
    
    db.delete(tree)
    db.commit()
    
    return {"message": f"Árbol {tree_id} del huerto {orchard_id} eliminado correctamente"}

# --- LIMPIEZA DE DATOS DE IA ---
@router.delete("/images/{image_id}")
async def delete_image_audit(image_id: int, db: Session = Depends(get_db)):
    """Elimina imagen y por cascada sus predicciones y detecciones"""
    img = db.query(models.Image).filter(models.Image.id == image_id).first()
    if img:
        # Aquí también deberías borrar el archivo físico en /uploads/
        db.delete(img)
        db.commit()
    return {"status": "deleted"}

    