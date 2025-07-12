from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RatingCreate(BaseModel):
    recipe_id: int
    user_id: int
    rating: int = Field(..., ge=1, le=5) # Assuming rating is an integer from 1 to 5

class Rating(BaseModel):
    id: int
    recipe_id: int
    user_id: int
    rating: int
    created_at: datetime
    user_email: Optional[str] = None # To display user's email
    recipe_title: Optional[str] = None # To display recipe title

    class Config:
        orm_mode = True