
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api import deps
from app.schemas.user_recipe import UserRecipe, UserRecipeCreate, UserRecipeUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=UserRecipe, status_code=status.HTTP_201_CREATED)
def create_user_recipe(
    *, 
    db: Session = Depends(deps.get_db),
    user_recipe_in: UserRecipeCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    user_recipe = crud.user_recipe.create_user_recipe(
        db=db, user_recipe=user_recipe_in, owner_id=current_user.id
    )
    return user_recipe

@router.get("/{user_recipe_id}", response_model=UserRecipe)
def read_user_recipe(
    *, 
    db: Session = Depends(deps.get_db),
    user_recipe_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    user_recipe = crud.user_recipe.get_user_recipe(db=db, user_recipe_id=user_recipe_id)
    if not user_recipe:
        raise HTTPException(status_code=404, detail="User recipe not found")
    if user_recipe.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user_recipe

@router.get("/user/{owner_id}", response_model=List[UserRecipe])
def read_user_recipes_by_owner(
    *, 
    db: Session = Depends(deps.get_db),
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
):
    user_recipes = crud.user_recipe.get_user_recipes_by_owner(
        db=db, owner_id=owner_id, skip=skip, limit=limit
    )
    return user_recipes

@router.put("/{user_recipe_id}", response_model=UserRecipe)
def update_user_recipe(
    *, 
    db: Session = Depends(deps.get_db),
    user_recipe_id: int,
    user_recipe_in: UserRecipeUpdate,
    current_user: User = Depends(deps.get_current_active_user)
):
    user_recipe = crud.user_recipe.get_user_recipe(db=db, user_recipe_id=user_recipe_id)
    if not user_recipe:
        raise HTTPException(status_code=404, detail="User recipe not found")
    if user_recipe.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user_recipe = crud.user_recipe.update_user_recipe(
        db=db, user_recipe_id=user_recipe_id, user_recipe=user_recipe_in
    )
    return user_recipe

@router.delete("/{user_recipe_id}", response_model=UserRecipe)
def delete_user_recipe(
    *, 
    db: Session = Depends(deps.get_db),
    user_recipe_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    user_recipe = crud.user_recipe.get_user_recipe(db=db, user_recipe_id=user_recipe_id)
    if not user_recipe:
        raise HTTPException(status_code=404, detail="User recipe not found")
    if user_recipe.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user_recipe = crud.user_recipe.delete_user_recipe(db=db, user_recipe_id=user_recipe_id)
    return user_recipe
