from fastapi import APIRouter

from app.api.v1.endpoints import recipes, utils, users, ratings, reviews, cookbooks

api_router = APIRouter()
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(cookbooks.router, prefix="/cookbooks", tags=["cookbooks"])
api_router.include_router(follows.router, prefix="/follows", tags=["follows"])
api_router.include_router(user_recipes.router, prefix="/user-recipes", tags=["user-recipes"])
api_router.include_router(meal_plans.router, prefix="/meal-plans", tags=["meal-plans"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
