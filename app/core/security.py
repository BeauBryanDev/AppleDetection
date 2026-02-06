import os
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt
from dotenv import load_dotenv
import hashlib
import hmac

# Load environment variables from .env file
load_dotenv()


# --- CONFIGURACIÓN ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ CRITICAL: SECRET_KEY not found in .env file! Set it before running the app.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash"""
    try:
        # Handle HMAC-SHA256 format
        if hashed_password.startswith("hmac_sha256$"):
            stored_hash = hashed_password.replace("hmac_sha256$", "")
            computed_hash = hmac.new(
                SECRET_KEY.encode(),
                plain_password.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(computed_hash, stored_hash)
        
        # Fallback to bcrypt if available
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except:
            return False
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Convierte una contraseña plana en un hash seguro"""
    hashed = hmac.new(
        SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"hmac_sha256${hashed}"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Genera el JWT Token que el usuario usará para identificarse"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt