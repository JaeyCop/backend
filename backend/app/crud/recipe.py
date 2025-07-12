from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.recipe import Recipe as RecipeModel
from app.models.rating import Rating
from app.schemas.recipe import Recipe as RecipeSchema


async def create_recipe(db: Session, recipe: RecipeSchema):
    # Exclude fields that don't exist in the database model
    recipe_data = recipe.dict(exclude={'average_rating', 'review_count'})
    db_recipe = RecipeModel(**recipe_data)
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return db_recipe


async def get_recipe_by_url(db: Session, url: str):
    result = await db.execute(select(RecipeModel).filter(RecipeModel.source_url == url))
    db_recipe = result.scalars().first()
    if db_recipe:
        return await _add_computed_fields(db, db_recipe)
    return None


async def get_recipes_by_query(db: Session, query: str, skip: int = 0, limit: int = 100):
    result = await db.execute(select(RecipeModel).filter(RecipeModel.title.ilike(f"%{query}%")).offset(skip).limit(limit))
    db_recipes = result.scalars().all()
    
    # Add computed fields to each recipe
    recipes_with_computed = []
    for db_recipe in db_recipes:
        recipe_with_computed = await _add_computed_fields(db, db_recipe)
        recipes_with_computed.append(recipe_with_computed)
    
    return recipes_with_computed


async def _add_computed_fields(db: Session, db_recipe: RecipeModel):
    """Add computed fields like average_rating and review_count to a recipe."""
    # Get average rating and count
    rating_result = await db.execute(
        select(func.avg(Rating.rating), func.count(Rating.id))
        .filter(Rating.recipe_id == db_recipe.id)
    )
    avg_rating, review_count = rating_result.first()
    
    # Convert SQLAlchemy model to Pydantic schema with computed fields
    recipe_dict = {
        'title': db_recipe.title,
        'ingredients': db_recipe.ingredients or [],
        'instructions': db_recipe.instructions or [],
        'image_url': db_recipe.image_url,
        'time_info': db_recipe.time_info or {},
        'rating': db_recipe.rating,
        'servings': db_recipe.servings,
        'description': db_recipe.description,
        'source_url': db_recipe.source_url,
        'scraped_at': db_recipe.scraped_at,
        'video_url': db_recipe.video_url,
        'nutrition': db_recipe.nutrition,
        'difficulty': db_recipe.difficulty,
        'tags': db_recipe.tags or [],
        'average_rating': float(avg_rating) if avg_rating else None,
        'review_count': review_count or 0
    }
    
    return RecipeSchema(**recipe_dict)
