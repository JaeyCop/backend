
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserRecipeBase(BaseModel):
    title: str
    ingredients: List[str] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    image_url: Optional[HttpUrl] = None
    time_info: Dict[str, str] = Field(default_factory=dict)
    servings: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class UserRecipeCreate(UserRecipeBase):
    pass

class UserRecipeUpdate(UserRecipeBase):
    pass

class UserRecipe(UserRecipeBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
