
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    recipient_id: int
    sender_id: Optional[int] = None
    notification_type: str
    message: str

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    is_read: bool

class Notification(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
