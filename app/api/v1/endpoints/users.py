from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db import models
from app.db.models.users import User, UserRole
from app.schemas import user_schema
from app.core import security
from app.api import deps


router = APIRouter()

@router.get("/me", response_model=user_schema.UserResponse)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Obtiene el perfil del usuario logueado usando el Token.
    No requiere enviar ID en la URL.
    """
    return current_user

# --- PROTECTED DATA    ---

# Read User Profile (Requested as /{user_id})
@router.get("/{user_id}", response_model=user_schema.UserResponse)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user) # Opcional: Protegerlo también
):
    """Busca un usuario específico por su ID  || si eres admin, devuelve todos los usuarios"""
    #RBAC: Si eres admin, devuelve todos los usuarios
    is_admin = current_user.role == UserRole.ADMIN
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver el perfil de otros usuarios."
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        
        
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user


# 1. Endpoint PÚBLICO: Registro de nuevos agricultores (Sign Up)
@router.post("/signup", response_model=user_schema.UserResponse)
async def register_new_user(
    user_in: user_schema.UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Registro público. Cualquiera puede registrarse.
    🔒 SEGURIDAD: El rol se fuerza a FARMER automáticamente.
    """
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
        
    hashed_password = security.get_password_hash(user_in.password)
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone_number=user_in.phone_number,
        password_hash=hashed_password,
        role=UserRole.FARMER # <--- AQUÍ ESTÁ EL CANDADO. Ignoramos user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Create New User (Protected) ONLy for Admins
@router.post("/", response_model=user_schema.UserResponse)
async def create_user_for_admins(
    user_in: user_schema.UserCreate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    # Check if email exists
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
        
    hashed_password = security.get_password_hash(user_in.password)
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone_number=user_in.phone_number,
        password_hash=hashed_password,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_admin) # Only admin can delete users

):
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No puedes eliminar tu propia cuenta de administrador."
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    
    print(f"DEBUG: User {user_id} deleted successfully")
    
    return {"message": f"Usuario {user_id} eliminado exitosamente"}


@router.patch("/{user_id}", response_model=user_schema.UserResponse)
async def update_user(
    user_id: int,
    obj_in: user_schema.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user) # 1. Capa de Autenticación
):
    """
    Actualiza campos de un usuario específico.
    Reglas de Seguridad:
    - Un ADMIN puede editar a cualquiera.
    - Un USUARIO normal solo puede editarse a sí mismo.
    """
    
    # 2. Capa de Autorización (Check de permisos)
    # Si no es Admin Y está intentando editar un ID que no es el suyo -> ERROR
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para editar este perfil."
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 3. Actualización de datos
    if obj_in.name:
        user.name = obj_in.name
    if obj_in.phone_number:
        user.phone_number = obj_in.phone_number
    
    # 'password: Optional[str] = None' a tu UserUpdate schema
    if hasattr(obj_in, 'password') and obj_in.password:
        # 3. Capa de Criptografía: Usamos Bcrypt real
        user.password_hash = security.get_password_hash(obj_in.password)
        
    db.commit()
    db.refresh(user)
    return user



    