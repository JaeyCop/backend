
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api import deps
from app.schemas.follow import Follow, FollowCreate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=Follow, status_code=status.HTTP_201_CREATED)
def follow_user(
    *, 
    db: Session = Depends(deps.get_db),
    follow_in: FollowCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    if current_user.id == follow_in.followed_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    existing_follow = crud.follow.get_follow(db, current_user.id, follow_in.followed_id)
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    follow = crud.follow.create_follow(db, current_user.id, follow_in.followed_id)
    return follow

@router.delete("/{followed_id}", response_model=Follow)
def unfollow_user(
    *, 
    db: Session = Depends(deps.get_db),
    followed_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    follow = crud.follow.get_follow(db, current_user.id, followed_id)
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    crud.follow.delete_follow(db, current_user.id, followed_id)
    return follow

@router.get("/following/{user_id}", response_model=List[Follow])
def get_user_following(
    *, 
    db: Session = Depends(deps.get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100
):
    following = crud.follow.get_following(db, user_id, skip=skip, limit=limit)
    return following

@router.get("/followers/{user_id}", response_model=List[Follow])
def get_user_followers(
    *, 
    db: Session = Depends(deps.get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100
):
    followers = crud.follow.get_followers(db, user_id, skip=skip, limit=limit)
    return followers
