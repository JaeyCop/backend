from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.user import get_user_by_id
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_current_user


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user