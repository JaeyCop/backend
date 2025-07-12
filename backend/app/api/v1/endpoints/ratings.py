from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from typing import List
from app.schemas.rating import RatingCreate, Rating
from app.models.rating import Rating as RatingModel
from app.models.user import User as UserModel
from app.models.recipe import Recipe as RecipeModel
from app.core.security import get_db, get_current_active_user
from datetime import datetime

router = APIRouter()

@router.post("/recipes/{recipe_id}/rate", response_model=Rating, status_code=status.HTTP_201_CREATED)
async def create_rating_for_recipe(
    recipe_id: int,
    rating_create: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a rating for a specific recipe.
    The user_id is taken from the authenticated user.
    """
    # Validate that the recipe exists
    result = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
    recipe = result.scalars().first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Ensure the rating is for the current user and the correct recipe
    if rating_create.user_id != current_user.id or rating_create.recipe_id != recipe_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating data does not match authenticated user or recipe ID"
        )

    # Check if user already rated this recipe, update if so, create if not
    result = await db.execute(select(RatingModel).filter(
        RatingModel.recipe_id == recipe_id,
        RatingModel.user_id == current_user.id
    ))
    existing_rating = result.scalars().first()

    if existing_rating:
        existing_rating.rating = rating_create.rating
        existing_rating.created_at = datetime.utcnow() # Update timestamp on edit
        await db.commit()
        await db.refresh(existing_rating)
        # Optionally update recipe's average rating here
        return existing_rating
    else:
        new_rating = RatingModel(
            recipe_id=recipe_id,
            user_id=current_user.id,
            rating=rating_create.rating,
            created_at=datetime.utcnow()
        )
        db.add(new_rating)
        try:
            await db.commit()
            await db.refresh(new_rating)
            # Optionally update recipe's average rating here
            return new_rating
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rating already exists for this recipe and user.")
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating rating: {e}")

@router.get("/recipes/{recipe_id}/ratings", response_model=List[Rating])
async def get_ratings_for_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """Get all ratings for a specific recipe."""
    result = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
    recipe = result.scalars().first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    result = await db.execute(select(RatingModel).filter(RatingModel.recipe_id == recipe_id))
    ratings = result.scalars().all()

    # Populate user_email and recipe_title for the response
    populated_ratings = []
    for r in ratings:
        user_result = await db.execute(select(UserModel).filter(UserModel.id == r.user_id))
        user = user_result.scalars().first()
        populated_ratings.append(Rating(
            id=r.id,
            recipe_id=r.recipe_id,
            user_id=r.user_id,
            rating=r.rating,
            created_at=r.created_at,
            user_email=user.email if user else None,
            recipe_title=recipe.title if recipe else None
        ))
    return populated_ratings

@router.get("/users/{user_id}/ratings", response_model=List[Rating])
async def get_ratings_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all ratings made by a specific user."""
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(RatingModel).filter(RatingModel.user_id == user_id))
    ratings = result.scalars().all()

    # Populate recipe_title for the response
    populated_ratings = []
    for r in ratings:
        recipe_result = await db.execute(select(RecipeModel).filter(RecipeModel.id == r.recipe_id))
        recipe = recipe_result.scalars().first()
        populated_ratings.append(Rating(
            id=r.id,
            recipe_id=r.recipe_id,
            user_id=r.user_id,
            rating=r.rating,
            created_at=r.created_at,
            user_email=user.email, # User email is known
            recipe_title=recipe.title if recipe else None
        ))
    return populated_ratings