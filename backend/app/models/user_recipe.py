
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class UserRecipe(Base):
    __tablename__ = "user_recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    image_url = Column(String, nullable=True)
    time_info = Column(JSON, nullable=True)
    servings = Column(String, nullable=True)
    description = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="user_recipes")
