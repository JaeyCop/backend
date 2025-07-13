
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate

def create_notification(db: Session, notification: NotificationCreate):
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification(db: Session, notification_id: int):
    return db.query(Notification).filter(Notification.id == notification_id).first()

def get_notifications_by_recipient(db: Session, recipient_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == recipient_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_notification(db: Session, notification_id: int, notification: NotificationUpdate):
    db_notification = get_notification(db, notification_id)
    if db_notification:
        update_data = notification.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_notification, key, value)
        db.commit()
        db.refresh(db_notification)
    return db_notification

def delete_notification(db: Session, notification_id: int):
    db_notification = get_notification(db, notification_id)
    if db_notification:
        db.delete(db_notification)
        db.commit()
    return db_notification
