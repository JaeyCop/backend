from pydantic import BaseModel, EmailStr, validator, Field, HttpUrl
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




class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserInDBBase(UserBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class UserInDB(UserInDBBase):
    hashed_password: str

class User(UserInDBBase):
    pass

class UserStats(BaseModel):
    recipe_count: int = 0
    follower_count: int = 0
    following_count: int = 0
