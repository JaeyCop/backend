from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewCreate(BaseModel):
    recipe_id: int
    user_id: int
    text: str = Field(..., min_length=1, max_length=500) # Review text

class Review(BaseModel):
    id: int
    recipe_id: int
    user_id: int
    text: str
    created_at: datetime
    user_email: Optional[str] = None # To display user's email
    recipe_title: Optional[str] = None # To display recipe title

    class Config:
        orm_mode = True