
from sqlalchemy.orm import Session
from app.models.follow import Follow
from app.schemas.follow import FollowCreate

def create_follow(db: Session, follower_id: int, followed_id: int):
    db_follow = Follow(follower_id=follower_id, followed_id=followed_id)
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    return db_follow

def get_follow(db: Session, follower_id: int, followed_id: int):
    return (
        db.query(Follow)
        .filter(Follow.follower_id == follower_id, Follow.followed_id == followed_id)
        .first()
    )

def delete_follow(db: Session, follower_id: int, followed_id: int):
    db_follow = get_follow(db, follower_id, followed_id)
    if db_follow:
        db.delete(db_follow)
        db.commit()
    return db_follow

def get_following(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Follow)
        .filter(Follow.follower_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_followers(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Follow)
        .filter(Follow.followed_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
