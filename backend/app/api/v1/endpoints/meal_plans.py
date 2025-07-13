
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api import deps
from app.schemas.meal_plan import MealPlan, MealPlanCreate, MealPlanUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=MealPlan, status_code=status.HTTP_201_CREATED)
def create_meal_plan(
    *, 
    db: Session = Depends(deps.get_db),
    meal_plan_in: MealPlanCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    meal_plan = crud.meal_plan.create_meal_plan(
        db=db, meal_plan=meal_plan_in, owner_id=current_user.id
    )
    return meal_plan

@router.get("/{meal_plan_id}", response_model=MealPlan)
def read_meal_plan(
    *, 
    db: Session = Depends(deps.get_db),
    meal_plan_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    meal_plan = crud.meal_plan.get_meal_plan(db=db, meal_plan_id=meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    if meal_plan.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return meal_plan

@router.get("/user/{owner_id}", response_model=List[MealPlan])
def read_meal_plans_by_owner(
    *, 
    db: Session = Depends(deps.get_db),
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
):
    meal_plans = crud.meal_plan.get_meal_plans_by_owner(
        db=db, owner_id=owner_id, skip=skip, limit=limit
    )
    return meal_plans

@router.put("/{meal_plan_id}", response_model=MealPlan)
def update_meal_plan(
    *, 
    db: Session = Depends(deps.get_db),
    meal_plan_id: int,
    meal_plan_in: MealPlanUpdate,
    current_user: User = Depends(deps.get_current_active_user)
):
    meal_plan = crud.meal_plan.get_meal_plan(db=db, meal_plan_id=meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    if meal_plan.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    meal_plan = crud.meal_plan.update_meal_plan(
        db=db, meal_plan_id=meal_plan_id, meal_plan=meal_plan_in
    )
    return meal_plan

@router.delete("/{meal_plan_id}", response_model=MealPlan)
def delete_meal_plan(
    *, 
    db: Session = Depends(deps.get_db),
    meal_plan_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    meal_plan = crud.meal_plan.get_meal_plan(db=db, meal_plan_id=meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    if meal_plan.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    meal_plan = crud.meal_plan.delete_meal_plan(db=db, meal_plan_id=meal_plan_id)
    return meal_plan
