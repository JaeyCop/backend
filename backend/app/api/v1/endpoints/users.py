from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas.user import (
    User, UserUpdate, UserStats
)
from app.crud.user import (
    get_user_by_email, get_user_by_id,
    update_user, get_users, deactivate_user,
    activate_user, delete_user, search_users
)
from app.core.security import (
    get_current_active_user
)
from app.api.deps import get_db

router = APIRouter()


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    updated_user = await update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's statistics."""
    stats = await get_user_stats(db, current_user.id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found"
        )
    return UserStats(**stats)


@router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account."""
    success = await delete_user(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete account"
        )
    return {"message": "Account deleted successfully"}


# Admin endpoints (require superuser privileges)
@router.get("/", response_model=List[User])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = await get_users(db, skip=skip, limit=limit, is_active=is_active)
    return users


@router.get("/search", response_model=List[User])
async def search_users_endpoint(
    q: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search users by name or email."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = await search_users(db, q, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def get_user_by_id_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only or own profile)."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await deactivate_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deactivated successfully"}


@router.put("/{user_id}/activate")
async def activate_user_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Activate user account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await activate_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User activated successfully"}