
from sqlalchemy.orm import Session
from app.models.cookbook import Cookbook
from app.schemas.cookbook import CookbookCreate, CookbookUpdate

def get_cookbook(db: Session, cookbook_id: int):
    return db.query(Cookbook).filter(Cookbook.id == cookbook_id).first()

def get_cookbooks_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Cookbook)
        .filter(Cookbook.owner_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_cookbook(db: Session, cookbook: CookbookCreate, user_id: int):
    db_cookbook = Cookbook(**cookbook.dict(), owner_id=user_id)
    db.add(db_cookbook)
    db.commit()
    db.refresh(db_cookbook)
    return db_cookbook

def update_cookbook(db: Session, cookbook_id: int, cookbook: CookbookUpdate):
    db_cookbook = get_cookbook(db, cookbook_id)
    if db_cookbook:
        update_data = cookbook.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_cookbook, key, value)
        db.commit()
        db.refresh(db_cookbook)
    return db_cookbook

def delete_cookbook(db: Session, cookbook_id: int):
    db_cookbook = get_cookbook(db, cookbook_id)
    if db_cookbook:
        db.delete(db_cookbook)
        db.commit()
    return db_cookbook
