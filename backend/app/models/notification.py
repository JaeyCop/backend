
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional, for system notifications
    notification_type = Column(String, nullable=False) # e.g., 'follow', 'comment', 'meal_plan_reminder'
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="notifications")
    sender = relationship("User", foreign_keys=[sender_id])
