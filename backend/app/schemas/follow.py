
from pydantic import BaseModel

class FollowBase(BaseModel):
    followed_id: int

class FollowCreate(FollowBase):
    pass

class Follow(FollowBase):
    follower_id: int

    class Config:
        orm_mode = True
