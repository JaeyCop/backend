
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api import deps
from app.schemas.notification import Notification, NotificationCreate, NotificationUpdate
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
def create_notification(
    *, 
    db: Session = Depends(deps.get_db),
    notification_in: NotificationCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    # Ensure the recipient is either the current user or a valid user if it's a system notification
    if notification_in.recipient_id != current_user.id and notification_in.sender_id != None:
        raise HTTPException(status_code=403, detail="Not authorized to create notifications for other users")

    notification = crud.notification.create_notification(db=db, notification=notification_in)
    return notification

@router.get("/{notification_id}", response_model=Notification)
def read_notification(
    *, 
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    notification = crud.notification.get_notification(db=db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return notification

@router.get("/user/{recipient_id}", response_model=List[Notification])
def read_notifications_by_recipient(
    *, 
    db: Session = Depends(deps.get_db),
    recipient_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
):
    if recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' notifications")

    notifications = crud.notification.get_notifications_by_recipient(
        db=db, recipient_id=recipient_id, skip=skip, limit=limit
    )
    return notifications

@router.put("/{notification_id}", response_model=Notification)
def update_notification(
    *, 
    db: Session = Depends(deps.get_db),
    notification_id: int,
    notification_in: NotificationUpdate,
    current_user: User = Depends(deps.get_current_active_user)
):
    notification = crud.notification.get_notification(db=db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    notification = crud.notification.update_notification(
        db=db, notification_id=notification_id, notification=notification_in
    )
    return notification

@router.delete("/{notification_id}", response_model=Notification)
def delete_notification(
    *, 
    db: Session = Depends(deps.get_db),
    notification_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    notification = crud.notification.get_notification(db=db, notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    notification = crud.notification.delete_notification(db=db, notification_id=notification_id)
    return notification
