from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class Recipe(BaseModel):
    title: str
    ingredients: List[str] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    time_info: Dict[str, str] = Field(default_factory=dict)
    rating: Optional[Dict[str, Any]] = None
    servings: Optional[str] = None
    description: Optional[str] = None
    source_url: str
    scraped_at: datetime = Field(default_factory=datetime.now)
    video_url: Optional[str] = None
    nutrition: Optional[Dict[str, Any]] = None
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    average_rating: Optional[float] = None
    review_count: int = 0


class RecipeSearchResponse(BaseModel):
    recipes: List[Recipe]
    total_found: int
    query: str
    search_time: float
    cached: bool = False
    video_results: Optional[List[Dict[str, str]]] = None


class RecipeDetailResponse(BaseModel):
    recipe: Recipe
    processing_time: float
    cached: bool = False
    related_recipes: List[Recipe] = Field(default_factory=list)
    video_tutorials: List[Dict[str, str]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    max_results: int = Field(default=10, ge=1, le=50)
    include_nutrition: bool = Field(default=False)
    include_videos: bool = Field(default=True)
    difficulty_filter: Optional[str] = Field(default=None)
    max_time_minutes: Optional[int] = Field(default=None)


class RecipeRecommendationResponse(BaseModel):
    recommendations: List[Recipe]
    based_on: str
    algorithm: str
    confidence: float


class NutritionAnalysis(BaseModel):
    recipe_title: str
    estimated_nutrition: Dict[str, Any]
    health_score: float
    dietary_tags: List[str]


class MealPlan(BaseModel):
    date: str
    meals: Dict[str, Recipe]
    total_nutrition: Dict[str, Any]
    shopping_list: List[str]


class VideoTutorial(BaseModel):
    title: str
    url: str
    duration: Optional[str] = None
    thumbnail: Optional[str] = None
    channel: Optional[str] = None
    views: Optional[str] = None
