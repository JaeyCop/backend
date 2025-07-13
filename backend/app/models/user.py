from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Profile information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Preferences
    dietary_preferences = Column(String, nullable=True)  # JSON string for dietary preferences
    favorite_cuisines = Column(String, nullable=True)   # JSON string for favorite cuisines
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Account status
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Login tracking
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    cookbooks = relationship("Cookbook", back_populates="owner", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.followed_id", back_populates="followed", cascade="all, delete-orphan")
    user_recipes = relationship("UserRecipe", back_populates="owner", cascade="all, delete-orphan")
    meal_plans = relationship("MealPlan", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", foreign_keys="Notification.recipient_id", back_populates="recipient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split('@')[0]  # Use email prefix as fallback
    
    @property
    def is_locked(self):
        """Check if user account is locked."""
        if self.locked_until:
            from datetime import datetime
            return datetime.utcnow() < self.locked_until
        return False
