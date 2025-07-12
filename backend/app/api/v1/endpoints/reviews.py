from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from typing import List
from app.schemas.review import ReviewCreate, Review
from app.models.review import Review as ReviewModel
from app.models.user import User as UserModel
from app.models.recipe import Recipe as RecipeModel
from app.core.security import get_db, get_current_active_user
from datetime import datetime

router = APIRouter()

@router.post("/recipes/{recipe_id}/review", response_model=Review, status_code=status.HTTP_201_CREATED)
async def create_review_for_recipe(
    recipe_id: int,
    review_create: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a review for a specific recipe.
    The user_id is taken from the authenticated user.
    """
    # Validate that the recipe exists
    result = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
    recipe = result.scalars().first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Ensure the review is for the current user and the correct recipe
    if review_create.user_id != current_user.id or review_create.recipe_id != recipe_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review data does not match authenticated user or recipe ID"
        )

    # Check if user already reviewed this recipe, update if so, create if not
    result = await db.execute(select(ReviewModel).filter(
        ReviewModel.recipe_id == recipe_id,
        ReviewModel.user_id == current_user.id
    ))
    existing_review = result.scalars().first()

    if existing_review:
        existing_review.text = review_create.text
        existing_review.created_at = datetime.utcnow() # Update timestamp on edit
        await db.commit()
        await db.refresh(existing_review)
        return existing_review
    else:
        new_review = ReviewModel(
            recipe_id=recipe_id,
            user_id=current_user.id,
            text=review_create.text,
            created_at=datetime.utcnow()
        )
        db.add(new_review)
        try:
            await db.commit()
            await db.refresh(new_review)
            return new_review
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already exists for this recipe and user.")
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating review: {e}")

@router.get("/recipes/{recipe_id}/reviews", response_model=List[Review])
async def get_reviews_for_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """Get all reviews for a specific recipe."""
    result = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
    recipe = result.scalars().first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    result = await db.execute(select(ReviewModel).filter(ReviewModel.recipe_id == recipe_id))
    reviews = result.scalars().all()

    # Populate user_email and recipe_title for the response
    populated_reviews = []
    for r in reviews:
        user_result = await db.execute(select(UserModel).filter(UserModel.id == r.user_id))
        user = user_result.scalars().first()
        populated_reviews.append(Review(
            id=r.id,
            recipe_id=r.recipe_id,
            user_id=r.user_id,
            text=r.text,
            created_at=r.created_at,
            user_email=user.email if user else None,
            recipe_title=recipe.title if recipe else None
        ))
    return populated_reviews

@router.get("/users/{user_id}/reviews", response_model=List[Review])
async def get_reviews_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all reviews made by a specific user."""
    result = await db.execute(select(UserModel).filter(UserModel.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(ReviewModel).filter(ReviewModel.user_id == user_id))
    reviews = result.scalars().all()

    # Populate recipe_title for the response
    populated_reviews = []
    for r in reviews:
        recipe_result = await db.execute(select(RecipeModel).filter(RecipeModel.id == r.recipe_id))
        recipe = recipe_result.scalars().first()
        populated_reviews.append(Review(
            id=r.id,
            recipe_id=r.recipe_id,
            user_id=r.user_id,
            text=r.text,
            created_at=r.created_at,
            user_email=user.email, # User email is known
            recipe_title=recipe.title if recipe else None
        ))
    return populated_reviews