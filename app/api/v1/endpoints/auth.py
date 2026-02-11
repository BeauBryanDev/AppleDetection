from fastapi import APIRouter, Depends, HTTPException, logger, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import EmailStr
from app.core.config import settings
from app.db.session import get_db
from app.db.models.users import User
from app.core import security
from datetime import timedelta
from app.core.logging import logger 


router = APIRouter()

@router.post("/login")
async def login_access_token(
    
    db: Session = Depends(get_db),
    
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login endpoint.

    Authenticates a user with email and password, returns a JWT access token.

    Note: Uses form_data.username as email (standard OAuth2 convention).

    Returns:
        dict: {"access_token": str, "token_type": "bearer"}

    Raises:
        HTTPException 401: Invalid email or password
    """
    # 1. Search User by emaill (form_data.username it must get the existing email)
    print(f"DEBUG: Attempting login with username: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        print(f"DEBUG: User not found with email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    # eMAIL Validation 
    # if not EmailStr._validate(form_data.username):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid email format"
    #     )
    
    # 2. Validate Right Password
    print(f"DEBUG: User found: {user.email}, verifying password...")
    password_valid = security.verify_password(form_data.password, user.password_hash)
    print(f"DEBUG: Password valid: {password_valid}")
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or Password Incorrect",
        )
    
    logger.debug(f"Login attempt for email: {form_data.username}")
    
    if password_valid:
        logger.info("User logged in successfully", user_id=user.id)
    else:
        logger.warning("User login failed", user_id=user.id)
        
    logger.info("User logged in successfully", user_id=user.id)
    
    # 3. Create JWT access token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }