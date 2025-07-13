from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import json
from .cookbook import Cookbook
from .follow import Follow
from .user_recipe import UserRecipe
from .meal_plan import MealPlan
from .notification import Notification


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    dietary_preferences: Optional[List[str]] = None
    favorite_cuisines: Optional[List[str]] = None



