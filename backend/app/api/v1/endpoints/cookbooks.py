from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import cookbook as crud_cookbook
from app.models import User
from app.schemas.cookbook import Cookbook, CookbookCreate, CookbookUpdate

router = APIRouter()

@router.post("/", response_model=Cookbook)
async def create_cookbook(
    cookbook_in: CookbookCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create new cookbook.
    """
    cookbook = await crud_cookbook.create_cookbook(db=db, cookbook=cookbook_in, owner_id=current_user.id)
    return cookbook


@router.get("/{cookbook_id}", response_model=Cookbook)
async def read_cookbook(
    cookbook_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Get cookbook by ID.
    """
    db_cookbook = await crud_cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if db_cookbook is None:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    return db_cookbook


@router.get("/", response_model=List[Cookbook])
async def read_cookbooks(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Retrieve cookbooks for the current user.
    """
    cookbooks = await crud_cookbook.get_cookbooks_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return cookbooks


@router.put("/{cookbook_id}", response_model=Cookbook)
async def update_cookbook(
    cookbook_id: int,
    cookbook_in: CookbookUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Update a cookbook.
    """
    db_cookbook = await crud_cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if db_cookbook is None:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    if db_cookbook.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    cookbook = await crud_cookbook.update_cookbook(
        db=db, cookbook_id=cookbook_id, cookbook=cookbook_in
    )
    return cookbook


@router.delete("/{cookbook_id}", response_model=Cookbook)
async def delete_cookbook(
    cookbook_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Delete a cookbook.
    """
    db_cookbook = await crud_cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if db_cookbook is None:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    if db_cookbook.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    cookbook = await crud_cookbook.delete_cookbook(db=db, cookbook_id=cookbook_id)
    return cookbook