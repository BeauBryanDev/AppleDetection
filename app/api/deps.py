from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.session import get_db
from app.db.models.users import User, UserRole
from app.core import security
from app.core.config import settings


# SECURITY SCHEMES

# Bearer token scheme
security_scheme = HTTPBearer(auto_error=True)  # Required
security_scheme_optional = HTTPBearer(auto_error=False)  # Opcional


# AUTHENTICATION - DEPENDENCIES

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to Auth User.
    
    REQUIERED : If Not token then Forbidden
    
    Args:
        credentials: JWT  for Auth Header
        db: Init DB Session 
        
    Returns:
        User: Authenticated User 
        
    Raises:
        HTTPException 401: if not token || invalid token 
        
    """
    token = credentials.credentials
    
    try:
        # dECODE JWT 
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Search User in db.users
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get Authenticated User.
    
    OPTIONAL:  If not token returns None .
    
    Args:
        credentials: Token JWT Optional
        db: database session
        
    Returns:
        User | None: Authenticated User or None if not token .
        

    """
    # If not credential , it reutnrs None || Guest mode.
    if credentials is None:
        return None
    
    token = credentials.credentials
    
    try:
        # decode JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        
        if user_id is None:
            return None
        
    except JWTError:
        # Invalid token  then returns  None. 
        return None
    
    # Search for user in database
    user = db.query(User).filter(User.id == user_id).first()
    
    return user # it can be None if User not exist


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to validate of is Active User 
    
    Args:
        current_user: Auth User 
        
    Returns:
        User: Ative User
        
    Raises:
        HTTPException 403: If user is not active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency validate if it is an acrive admin user
    
    Args:
        current_user: active authenticate user
        
    Returns:
        User: admin user
        
    Raises:
        HTTPException 403: if user is not admin 
        
    Message : Only Admin user can run this feature
    
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )
    
    return current_user



# VALIDATION DEPENDENCIES

def validate_file_size(
    content_length: Optional[int] = None
) -> int:
    """
    Validate File is not bigger than Max size allowed
    
    Args:
        content_length: size of file in bytes
        
    Returns:
        int: file size is supported
        
    Raises:
        HTTPException 413: if file size /images/ is bigger than supported
    """
    max_size = 10 * 1024 * 1024  # 10 MB -> big image size 
    
    if content_length and content_length > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed (10 MB)"
        )
    
    return content_length or 0


def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """
    Dependency for pagination parameters
    
    Args:
        skip: Number of register to jump ahead
        limit: Max registers 
        
    Returns:
        dict: valid parameters
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="skip must be >= 0"
        )
    
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 1000"
        )
    
    return {"skip": skip, "limit": limit}