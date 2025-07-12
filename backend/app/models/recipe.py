from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.session import Base
from sqlalchemy.orm import relationship


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    ingredients = Column(JSON)
    instructions = Column(JSON)
    image_url = Column(String, nullable=True)
    time_info = Column(JSON, nullable=True)
    rating = Column(JSON, nullable=True)
    servings = Column(String, nullable=True)
    description = Column(String, nullable=True)
    source_url = Column(String, unique=True, index=True)
    scraped_at = Column(DateTime)
    video_url = Column(String, nullable=True)
    nutrition = Column(JSON, nullable=True)
    difficulty = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)

    ratings = relationship("Rating", back_populates="recipe")
    reviews = relationship("Review", back_populates="recipe")
