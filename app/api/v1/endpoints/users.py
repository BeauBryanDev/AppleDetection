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

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.utils.s3_storage import upload_image_to_s3, get_presigned_url, delete_image_from_s3, s3_is_configured

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Get the current user profile 
    Show User information
    """
    
    logger.debug(f"Login attempt for {current_user.email}")
    logger.info("User logged in", user_id=current_user.id)
    
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



@router.post("/{user_id}/profile-picture", response_model=UserResponse)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Upload a profile picture for a user.
    Saves the image to S3 under the avatars/ folder.
    Only the user themselves or an admin can upload.
    """
    # Permission check
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this profile picture"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_types)}"
        )

    # Find the user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Read image bytes
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image file"
        )

    # Delete old avatar from S3 if exists
    if user.avatar_url and s3_is_configured():
        # avatar_url is stored as 'avatars/filename.jpg'
        delete_image_from_s3(user.avatar_url)

    # Generate unique filename and upload to S3 avatars/ folder
    import uuid
    extension = file.filename.rsplit(".", 1)[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{extension}"
    s3_key = f"avatars/{unique_filename}"

    if s3_is_configured():
        import boto3
        import os
        from botocore.exceptions import ClientError

        client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        try:
            client.put_object(
                Bucket=os.getenv("S3_BUCKET_NAME"),
                Key=s3_key,
                Body=image_bytes,
                ContentType=file.content_type,
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image to S3: {e}"
            )
    else:
        # Fallback local storage for development
        import os
        os.makedirs("uploads/avatars", exist_ok=True)
        with open(f"uploads/avatars/{unique_filename}", "wb") as f:
            f.write(image_bytes)

    # Save s3_key in DB as avatar_url
    user.avatar_url = s3_key
    db.commit()
    db.refresh(user)

    logger.info(f"Profile picture updated for user {user_id}: {s3_key}")

    return user

@router.get("/{user_id}/profile-picture-url")
async def get_profile_picture_url(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Get a pre-signed URL for the user's profile picture from S3.
    Valid for 1 hour.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user has no profile picture"
        )

    if s3_is_configured():
        url = get_presigned_url(user.avatar_url, expiration_seconds=3600)
        return {"url": url, "source": "s3"}
    else:
        return {"url": f"/uploads/{user.avatar_url}", "source": "local"}
    

@router.delete("/{user_id}/profile-picture", response_model=UserResponse)
async def delete_profile_picture(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Delete a profile picture for a user.
    Deletes the image from S3 under the avatars/ folder.
    Only the user themselves or an admin can delete.
    """
    # Permission check
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this profile picture"
        )

    # Find the user
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete from S3 if exists
    if user.avatar_url and s3_is_configured():
        delete_image_from_s3(user.avatar_url)

    # Clear avatar_url in DB
    user.avatar_url = None
    db.commit()
    db.refresh(user)

    logger.info(f"Profile picture deleted for user {user_id}")

    return user