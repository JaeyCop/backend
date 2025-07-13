
from pydantic import BaseModel
from typing import List, Optional
from .recipe import Recipe

class CookbookBase(BaseModel):
    name: str
    description: Optional[str] = None

class CookbookCreate(CookbookBase):
    pass

class CookbookUpdate(CookbookBase):
    pass

class Cookbook(CookbookBase):
    id: int
    owner_id: int
    recipes: List[Recipe] = []

    class Config:
        orm_mode = True
