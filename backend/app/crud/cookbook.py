from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.models.cookbook import Cookbook as CookbookModel
from app.schemas.cookbook import CookbookCreate, CookbookUpdate

async def create_cookbook(db: Session, cookbook: CookbookCreate, owner_id: int):
    db_cookbook = CookbookModel(**cookbook.dict(), owner_id=owner_id)
    db.add(db_cookbook)
    await db.commit()
    await db.refresh(db_cookbook)
    return db_cookbook

async def get_cookbook(db: Session, cookbook_id: int):
    result = await db.execute(select(CookbookModel).filter(CookbookModel.id == cookbook_id))
    return result.scalars().first()

async def get_cookbooks_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(CookbookModel)
        .filter(CookbookModel.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_cookbook(db: Session, cookbook_id: int, cookbook: CookbookUpdate):
    result = await db.execute(select(CookbookModel).filter(CookbookModel.id == cookbook_id))
    db_cookbook = result.scalars().first()
    if db_cookbook:
        update_data = cookbook.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_cookbook, key, value)
        await db.commit()
        await db.refresh(db_cookbook)
    return db_cookbook

async def delete_cookbook(db: Session, cookbook_id: int):
    result = await db.execute(select(CookbookModel).filter(CookbookModel.id == cookbook_id))
    db_cookbook = result.scalars().first()
    if db_cookbook:
        await db.delete(db_cookbook)
        await db.commit()
    return db_cookbook