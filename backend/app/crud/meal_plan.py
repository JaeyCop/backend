
from sqlalchemy.orm import Session
from app.models.meal_plan import MealPlan
from app.schemas.meal_plan import MealPlanCreate, MealPlanUpdate

def get_meal_plan(db: Session, meal_plan_id: int):
    return db.query(MealPlan).filter(MealPlan.id == meal_plan_id).first()

def get_meal_plans_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(MealPlan)
        .filter(MealPlan.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_meal_plan(db: Session, meal_plan: MealPlanCreate, owner_id: int):
    db_meal_plan = MealPlan(**meal_plan.dict(), owner_id=owner_id)
    db.add(db_meal_plan)
    db.commit()
    db.refresh(db_meal_plan)
    return db_meal_plan

def update_meal_plan(db: Session, meal_plan_id: int, meal_plan: MealPlanUpdate):
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan:
        update_data = meal_plan.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_meal_plan, key, value)
        db.commit()
        db.refresh(db_meal_plan)
    return db_meal_plan

def delete_meal_plan(db: Session, meal_plan_id: int):
    db_meal_plan = get_meal_plan(db, meal_plan_id)
    if db_meal_plan:
        db.delete(db_meal_plan)
        db.commit()
    return db_meal_plan
