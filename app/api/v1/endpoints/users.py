from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db import models
from app.db.models.users import User, UserRole
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.core import security
from app.api import deps
from app.core.logging import logger

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Get the current user profile 
    Show User information
    """
    return current_user

# --- PROTECTED DATA    ---

# Read User Profile (Requested as /{user_id})
@router.get("/{user_id}", response_model=UserResponse, tags=["Users"])  
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user) 
):
    """Search an User by Id, check ig it is Admin User """
    #RBAC: if it is admin user, return all users, then search user_id
    is_admin = current_user.role == UserRole.ADMIN
    is_self = current_user.id == user_id
    # if User is not admin  tell that it is not allowed action
    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Allowed to see others users profile"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        
        
        raise HTTPException(status_code=404, detail="User no found")
    
    return user


# 1. Public Endpoint to register new farmers users (Sign Up)
@router.post("/signup", response_model=UserResponse)
async def register_new_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Public Register open to public
    Security features, it force user to be farmers
    Creates a new farmer user (forces role to FARMER)
    """
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="email is already used by other user")
        
    hashed_password = security.get_password_hash(user_in.password)
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone_number=user_in.phone_number,
        password_hash=hashed_password,
        role=UserRole.FARMER 
    )
    # Save in Database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. Get All Users (Admin Only)
@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    """
    Retrieve users.
    Only for admins.
    """
    users = (
        db.query(User)
        .order_by(User.created_at.desc())  # ← Suggestion applied: newest first
        .offset(skip)
        .limit(limit)
        .all()
    )
    return users


# Create a new User, it is protected , oly for admin can create new admin users.
@router.post("/", response_model=UserResponse)
async def create_user_for_admins(
    user_in: UserCreate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    # Check if email exists
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email is already used in db")
        
    hashed_password = security.get_password_hash(user_in.password)
    
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone_number=user_in.phone_number,
        password_hash=hashed_password,
        role=user_in.role # Admin can set any role
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
            detail="Admin can not delete its own account, ask request to your system administrator."
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not Found User")
    
    db.delete(user)
    db.commit()
    
    print(f"DEBUG: User {user_id} deleted successfully")
    
    logger.info(f"User {user_id} deleted successfully by admin {current_user.id}")  # ← Replaced print with logger

    return {"message": f"User ID {user_id} has been deleted"}


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    obj_in: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user) # 1. Capa de Autenticación
):
    """
    Updare fileds from an specfiic user
    Security Rules:
    - Admin can edit all roles.
    - Regular User can only edit its own profile information, not beyond
    """
    
    # Auth layer to check for permissions
    # If Not admin, attempting to edit another profile,  Deny!
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        # Action Not allowed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to take on this action."
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not found")

    # User Data update
    if obj_in.name:
        user.name = obj_in.name
    if obj_in.phone_number:
        user.phone_number = obj_in.phone_number
    
    # Password update
    if obj_in.password:
        user.password_hash = security.get_password_hash(obj_in.password)

    # Email update (with uniqueness check) — only admins can change email
    if obj_in.email and current_user.role == UserRole.ADMIN:
        if obj_in.email != user.email:  # Only check if actually changing
            existing = db.query(models.User).filter(models.User.email == obj_in.email).first()
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="Email is already in use")
            user.email = obj_in.email
            # TODO (future): Send confirmation email to new address
            logger.info(f"Admin changed email for user {user_id} to {obj_in.email}")
    
    db.commit()
    db.refresh(user)
    return user



    