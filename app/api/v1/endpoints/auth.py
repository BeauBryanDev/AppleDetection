from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.users import User
from app.core import security
from datetime import timedelta

router = APIRouter()

@router.post("/login")
async def login_access_token(
    
    db: Session = Depends(get_db),
    
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # 1. Buscar usuario por email (form_data.username contendrá el email)
    print(f"DEBUG: Attempting login with username: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        print(f"DEBUG: User not found with email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    
    # 2. Verificar contraseña
    print(f"DEBUG: User found: {user.email}, verifying password...")
    password_valid = security.verify_password(form_data.password, user.password_hash)
    print(f"DEBUG: Password valid: {password_valid}")
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    
    # 3. Generar Token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }