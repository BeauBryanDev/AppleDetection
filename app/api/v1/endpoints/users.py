from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.schemas import user_schema

router = APIRouter()

# TODO: Implement proper auth. For now, defaulting to user_id=1
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- PERFIL DE USUARIO ---

# Read User Profile (Requested as /mee/{user_id})
@router.get("/mee/{user_id}", response_model=user_schema.UserResponse)
async def read_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el perfil de un usuario por ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# Create New User
@router.post("/", response_model=user_schema.UserResponse)
async def create_user(
    user_in: user_schema.UserCreate, 
    db: Session = Depends(get_db)
):
    # Check if email exists
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
        
    # TODO: Hash password properly. Storing plain for MVP as requested implicitly by context
    fake_hashed_password = f"hashed_{user_in.password}" 
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone_number=user_in.phone_number,
        password_hash=fake_hashed_password,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Delete User
@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    return {"message": f"Usuario {user_id} eliminado exitosamente"}


@router.patch("/{user_id}", response_model=user_schema.UserResponse)
async def update_user(
    user_id: int,
    obj_in: user_schema.UserUpdate, 
    db: Session = Depends(get_db)
):
    """Actualiza campos de un usuario específico"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if obj_in.name:
        user.name = obj_in.name
    if obj_in.phone_number:
        user.phone_number = obj_in.phone_number
    if obj_in.password:
        user.password_hash = f"hashed_{obj_in.password}"
        
    db.commit()
    db.refresh(user)
    return user



    