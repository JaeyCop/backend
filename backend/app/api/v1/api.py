from fastapi import APIRouter

from app.api.v1.endpoints import recipes, utils, users, ratings, reviews

api_router = APIRouter()
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ratings.router, prefix="/ratings", tags=["ratings"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
