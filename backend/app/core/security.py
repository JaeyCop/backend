from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.settings import settings
from app.models.user import User
from app.db.session import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


async def get_db():
    """Database dependency."""
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    """Get current authenticated user by validating Supabase JWT."""
    from sqlalchemy.future import select
    from app.models.user import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate JWT using Supabase JWT secret
        payload = jwt.decode(
            credentials.credentials, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=[settings.ALGORITHM] # Supabase uses HS256 by default
        )
        
        user_id: str = payload.get("sub") # 'sub' claim contains the user ID in Supabase JWT
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        print(f"JWT Error: {e}") # Log the error for debugging
        raise credentials_exception
    
    # Get user from database using the user_id from JWT
    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user