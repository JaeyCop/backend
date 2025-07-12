from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
from typing import Optional, List
from datetime import datetime, timedelta
import json

from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate, UserPasswordChange
from app.core.security import get_password_hash, verify_password


async def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
    """Get user by ID."""
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """Get user by email."""
    result = await db.execute(select(UserModel).filter(UserModel.email == email))
    return result.scalars().first()


async def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[UserModel]:
    """Get multiple users with pagination."""
    query = select(UserModel)
    
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_user(db: Session, user: UserCreate) -> UserModel:
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    
    # Convert lists to JSON strings for storage
    dietary_preferences = json.dumps(user.dietary_preferences) if user.dietary_preferences else None
    favorite_cuisines = json.dumps(user.favorite_cuisines) if user.favorite_cuisines else None
    
    db_user = UserModel(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        dietary_preferences=dietary_preferences,
        favorite_cuisines=favorite_cuisines,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[UserModel]:
    """Update user information."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Convert lists to JSON strings for storage
    if 'dietary_preferences' in update_data:
        update_data['dietary_preferences'] = json.dumps(update_data['dietary_preferences'])
    if 'favorite_cuisines' in update_data:
        update_data['favorite_cuisines'] = json.dumps(update_data['favorite_cuisines'])
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def change_password(
    db: Session, 
    user_id: int, 
    password_change: UserPasswordChange
) -> Optional[UserModel]:
    """Change user password."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # Verify current password
    if not verify_password(password_change.current_password, db_user.hashed_password):
        return None
    
    # Update password
    db_user.hashed_password = get_password_hash(password_change.new_password)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def reset_password(db: Session, email: str, new_password: str) -> Optional[UserModel]:
    """Reset user password (for password reset flow)."""
    db_user = await get_user_by_email(db, email)
    if not db_user:
        return None
    
    db_user.hashed_password = get_password_hash(new_password)
    db_user.password_reset_token = None
    db_user.password_reset_expires = None
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]:
    """Authenticate user with email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        await db.commit()
        return None
    
    # Check if account is locked
    if user.is_locked:
        return None
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    user.login_count += 1
    
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: Session, user_id: int) -> Optional[UserModel]:
    """Deactivate user account."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = False
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def activate_user(db: Session, user_id: int) -> Optional[UserModel]:
    """Activate user account."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = True
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: Session, user_id: int) -> bool:
    """Delete user account (soft delete by deactivating)."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    # Soft delete by deactivating
    db_user.is_active = False
    db_user.email = f"deleted_{user_id}_{db_user.email}"  # Prevent email conflicts
    await db.commit()
    return True


async def verify_email(db: Session, user_id: int) -> Optional[UserModel]:
    """Mark user email as verified."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.email_verified = True
    db_user.email_verification_token = None
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def set_password_reset_token(db: Session, email: str, token: str) -> Optional[UserModel]:
    """Set password reset token for user."""
    db_user = await get_user_by_email(db, email)
    if not db_user:
        return None
    
    db_user.password_reset_token = token
    db_user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_stats(db: Session, user_id: int) -> Optional[dict]:
    """Get user statistics."""
    from app.models.rating import Rating
    from app.models.review import Review
    
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # Get rating count and average
    rating_result = await db.execute(
        select(func.count(Rating.id), func.avg(Rating.rating))
        .filter(Rating.user_id == user_id)
    )
    rating_count, avg_rating = rating_result.first()
    
    # Get review count
    review_result = await db.execute(
        select(func.count(Review.id))
        .filter(Review.user_id == user_id)
    )
    review_count = review_result.scalar()
    
    return {
        "total_ratings": rating_count or 0,
        "total_reviews": review_count or 0,
        "average_rating_given": float(avg_rating) if avg_rating else None,
        "joined_date": db_user.created_at,
        "last_login": db_user.last_login,
        "login_count": db_user.login_count
    }


async def search_users(
    db: Session, 
    query: str, 
    skip: int = 0, 
    limit: int = 20
) -> List[UserModel]:
    """Search users by name or email."""
    search_filter = or_(
        UserModel.first_name.ilike(f"%{query}%"),
        UserModel.last_name.ilike(f"%{query}%"),
        UserModel.email.ilike(f"%{query}%")
    )
    
    result = await db.execute(
        select(UserModel)
        .filter(and_(UserModel.is_active == True, search_filter))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
