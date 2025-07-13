
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class MealPlanBase(BaseModel):
    name: str
    plan_data: Dict[str, Any] = Field(default_factory=dict)

class MealPlanCreate(MealPlanBase):
    pass

class MealPlanUpdate(MealPlanBase):
    pass

class MealPlan(MealPlanBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
