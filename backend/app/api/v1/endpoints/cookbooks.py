
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api import deps
from app.schemas.cookbook import Cookbook, CookbookCreate, CookbookUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=Cookbook)
def create_cookbook(
    *, 
    db: Session = Depends(deps.get_db),
    cookbook_in: CookbookCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    cookbook = crud.cookbook.create_cookbook(
        db=db, cookbook=cookbook_in, user_id=current_user.id
    )
    return cookbook

@router.get("/{cookbook_id}", response_model=Cookbook)
def read_cookbook(
    *, 
    db: Session = Depends(deps.get_db),
    cookbook_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    cookbook = crud.cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if not cookbook:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    if cookbook.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return cookbook

@router.get("/user/{user_id}", response_model=List[Cookbook])
def read_cookbooks_by_user(
    *, 
    db: Session = Depends(deps.get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
):
    cookbooks = crud.cookbook.get_cookbooks_by_user(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return cookbooks

@router.put("/{cookbook_id}", response_model=Cookbook)
def update_cookbook(
    *, 
    db: Session = Depends(deps.get_db),
    cookbook_id: int,
    cookbook_in: CookbookUpdate,
    current_user: User = Depends(deps.get_current_active_user)
):
    cookbook = crud.cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if not cookbook:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    if cookbook.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    cookbook = crud.cookbook.update_cookbook(
        db=db, cookbook_id=cookbook_id, cookbook=cookbook_in
    )
    return cookbook

@router.delete("/{cookbook_id}", response_model=Cookbook)
def delete_cookbook(
    *, 
    db: Session = Depends(deps.get_db),
    cookbook_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    cookbook = crud.cookbook.get_cookbook(db=db, cookbook_id=cookbook_id)
    if not cookbook:
        raise HTTPException(status_code=404, detail="Cookbook not found")
    if cookbook.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    cookbook = crud.cookbook.delete_cookbook(db=db, cookbook_id=cookbook_id)
    return cookbook
