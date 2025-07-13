import asyncio
import hashlib
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Optional, List

import aiohttp
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.schemas.recipe import (
    RecipeSearchResponse,
    SearchQuery,
    RecipeDetailResponse,
    RecipeRecommendationResponse, NutritionAnalysis, Recipe
)
from app.services.cache import cache
from app.services.scraper import scraper
from app.services.video_scraper import video_scraper
from pydantic import HttpUrl
from app.crud.recipe import get_recipe_by_url, create_recipe, get_recipes_by_query
from app.services.ai_service import ai_service
from app.core.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session


logger = logging.getLogger(__name__)
router = APIRouter()





@router.get("/search", response_model=RecipeSearchResponse)
async def search_recipes(
        q: str = Query(..., min_length=1, max_length=100, description="Search query"),
        limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
        use_cache: bool = Query(default=True, description="Whether to use cached results"),
        include_videos: bool = Query(default=True, description="Include video tutorials"),
        ingredients: Optional[str] = Query(default=None, description="Comma-separated ingredients to filter by"),
        cuisine: Optional[str] = Query(default=None, description="Cuisine type to filter by"),
        difficulty: Optional[str] = Query(default=None, description="Difficulty level to filter by"),
        tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
        db: AsyncSession = Depends(get_db)
):
    """Search for recipes by query."""
    start_time = time.time()

    # Generate cache key
    cache_key = generate_cache_key(q, limit, include_videos, ingredients, cuisine, difficulty, tags)

    # Check cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result["search_time"] = time.time() - start_time
            cached_result["cached"] = True
            return RecipeSearchResponse(**cached_result)

    try:
        # Use AI for semantic search if enabled and API key is present
        refined_query = q
        if settings.GEMINI_API_KEY:
            refined_query = await ai_service.get_semantic_search_query(q)
            logger.info(f"Original query: {q}, Refined query (AI): {refined_query}")

        # Check database first with refined query
        db_recipes = await get_recipes_by_query(db, query=refined_query, limit=limit, ingredients=ingredients, cuisine=cuisine, difficulty=difficulty, tags=tags)
        if db_recipes:
            search_time = time.time() - start_time
            video_results = None
            if include_videos:
                video_results = video_scraper.get_youtube_videos(refined_query, max_results=5)
            result = {
                "recipes": db_recipes,
                "total_found": len(db_recipes),
                "query": refined_query,
                "search_time": search_time,
                "cached": False,
                "video_results": video_results
            }
            if use_cache:
                cache.set(cache_key, result)
            return RecipeSearchResponse(**result)

        # If not in DB, scrape recipes
        recipes = await scraper.search_recipes(refined_query, limit, include_videos)

        # Save recipes to DB
        for recipe in recipes:
            db_recipe = await get_recipe_by_url(db, url=recipe.source_url)
            if not db_recipe:
                await create_recipe(db, recipe=recipe)

        # Get video results if requested
        video_results = None
        if include_videos:
            video_results = video_scraper.get_youtube_videos(refined_query, max_results=5)

        search_time = time.time() - start_time

        result = {
            "recipes": recipes,
            "total_found": len(recipes),
            "query": refined_query,
            "search_time": search_time,
            "cached": False,
            "video_results": video_results
        }

        # Cache the result
        if use_cache:
            cache.set(cache_key, result)

        return RecipeSearchResponse(**result)

    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/search", response_model=RecipeSearchResponse)
async def search_recipes_post(search_query: SearchQuery):
    """Search for recipes using POST method with detailed parameters."""
    start_time = time.time()

    cache_key = generate_cache_key(search_query.query, search_query.max_results, search_query.include_videos, search_query.ingredients_filter, search_query.cuisine_filter, search_query.difficulty_filter, search_query.tags_filter)

    # Check cache
    cached_result = cache.get(cache_key)
    if search_query.use_cache and cached_result:
        cached_result["search_time"] = time.time() - start_time
        cached_result["cached"] = True
        return RecipeSearchResponse(**cached_result)

    try:
        # Use AI for semantic search if enabled and API key is present
        refined_query = search_query.query
        if settings.GEMINI_API_KEY:
            refined_query = await ai_service.get_semantic_search_query(search_query.query)
            logger.info(f"Original query: {search_query.query}, Refined query (AI): {refined_query}")

        # Check database first with refined query
        db_recipes = await get_recipes_by_query(db, query=refined_query, limit=search_query.max_results, ingredients=search_query.ingredients_filter, cuisine=search_query.cuisine_filter, difficulty=search_query.difficulty_filter, tags=search_query.tags_filter)
        if db_recipes:
            search_time = time.time() - start_time
            video_results = None
            if search_query.include_videos:
                video_results = video_scraper.get_youtube_videos(refined_query, max_results=5)
            result = {
                "recipes": db_recipes,
                "total_found": len(db_recipes),
                "query": refined_query,
                "search_time": search_time,
                "cached": False,
                "video_results": video_results
            }
            if search_query.use_cache:
                cache.set(cache_key, result)
            return RecipeSearchResponse(**result)

        recipes = await scraper.search_recipes(refined_query, search_query.max_results,
                                               search_query.include_videos, search_query.ingredients_filter, search_query.cuisine_filter, search_query.difficulty_filter, search_query.tags_filter)

        # Apply filters
        if search_query.difficulty_filter:
            recipes = [r for r in recipes if r.difficulty == search_query.difficulty_filter]

        if search_query.max_time_minutes:
            # Filter by total time (simplified)
            recipes = [r for r in recipes if\
                       r.time_info.get('total_time', '0') <= str(search_query.max_time_minutes)]

        # Get video results if requested
        video_results = None
        if search_query.include_videos:
            video_results = video_scraper.get_youtube_videos(refined_query, max_results=5)

        search_time = time.time() - start_time

        result = {
            "recipes": recipes,
            "total_found": len(recipes),
            "query": refined_query,
            "search_time": search_time,
            "cached": False,
            "video_results": video_results
        }

        if search_query.use_cache:
            cache.set(cache_key, result)

        return RecipeSearchResponse(**result)

    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recipe", response_model=RecipeDetailResponse)
async def get_single_recipe(
        url: HttpUrl = Query(..., description="Recipe URL to scrape"),
        use_cache: bool = Query(default=True, description="Whether to use cached results"),
        include_related: bool = Query(default=True, description="Include related recipes"),
        db: Session = Depends(get_db)
):
    """Get detailed information for a single recipe by URL."""
    start_time = time.time()

    # Generate cache key from URL
    cache_key = hashlib.md5(f"{str(url)}:{include_related}".encode()).hexdigest()

    # Check cache
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            cached_result["processing_time"] = time.time() - start_time
            cached_result["cached"] = True
            return RecipeDetailResponse(**cached_result)

    try:
        # Check database first
        db_recipe = await get_recipe_by_url(db, url=str(url))
        if db_recipe:
            processing_time = time.time() - start_time
            related_recipes = []
            video_tutorials = []
            if include_related and db_recipe.title:
                related_recipes = await scraper.search_recipes(db_recipe.title, max_results=3, include_videos=False)
                related_recipes = [r for r in related_recipes if r.source_url != db_recipe.source_url]
                video_tutorials = video_scraper.get_youtube_videos(db_recipe.title, max_results=3)

            result = {
                "recipe": db_recipe,
                "processing_time": processing_time,
                "cached": False,
                "related_recipes": related_recipes,
                "video_tutorials": video_tutorials
            }
            if use_cache:
                cache.set(cache_key, result)
            return RecipeDetailResponse(**result)

        async with aiohttp.ClientSession(headers=scraper.headers) as session:
            recipe = await scraper.scrape_recipe(session, str(url), include_videos=True)

        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found or could not be scraped")

        # Save recipe to DB
        db_recipe = await get_recipe_by_url(db, url=recipe.source_url)
        if not db_recipe:
            await create_recipe(db, recipe=recipe)

        # Get related recipes and video tutorials
        related_recipes = []
        video_tutorials = []

        if include_related and recipe.title:
            # Search for related recipes
            related_recipes = await scraper.search_recipes(recipe.title, max_results=3, include_videos=False)
            related_recipes = [r for r in related_recipes if r.source_url != recipe.source_url]

            # Get video tutorials
            video_tutorials = video_scraper.get_youtube_videos(recipe.title, max_results=3)

        processing_time = time.time() - start_time

        result = {
            "recipe": recipe,
            "processing_time": processing_time,
            "cached": False,
            "related_recipes": related_recipes,
            "video_tutorials": video_tutorials
        }

        # Cache the result
        if use_cache:
            cache.set(cache_key, result)

        return RecipeDetailResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping recipe: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/videos/search")
async def search_recipe_videos(
        query: str = Query(..., description="Search query for recipe videos"),
        max_results: int = Query(default=10, ge=1, le=20, description="Maximum number of video results")
):
    """Search for recipe videos on YouTube."""
    try:
        videos = video_scraper.get_youtube_videos(query, max_results)

        return {
            "videos": videos,
            "query": query,
            "total_found": len(videos),
            "platform": "youtube"
        }

    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations", response_model=RecipeRecommendationResponse)
async def get_recipe_recommendations(
        based_on: str = Query(..., description="Recipe title or ingredients to base recommendations on"),
        max_results: int = Query(default=5, ge=1, le=20, description="Maximum number of recommendations")
):
    """Get recipe recommendations based on a recipe or ingredients."""
    try:
        # Simple recommendation based on search
        recommendations = await scraper.search_recipes(based_on, max_results, include_videos=False)

        return RecipeRecommendationResponse(
            recommendations=recommendations,
            based_on=based_on,
            algorithm="content_similarity",
            confidence=0.75
        )

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trending")
async def get_trending_recipes(
        limit: int = Query(default=15, ge=1, le=50, description="Number of trending recipes")
):
    """Get trending recipes based on popular searches."""
    trending_terms = [
        "viral recipes 2024",
        "easy weeknight dinner",
        "healthy meal prep",
        "comfort food recipes",
        "quick breakfast ideas",
        "one pot meals",
        "air fryer recipes"
    ]

    try:
        all_recipes = []
        for term in trending_terms:
            recipes = await scraper.search_recipes(term, max_results=3, include_videos=False)
            all_recipes.extend(recipes)

        # Shuffle and limit
        random.shuffle(all_recipes)

        return {
            "trending_recipes": all_recipes[:limit],
            "total_found": len(all_recipes),
            "trending_terms": trending_terms
        }

    except Exception as e:
        logger.error(f"Error getting trending recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/meal-plan/generate", response_model=MealPlan)
async def generate_meal_plan(
        days: int = Query(default=7, ge=1, le=14, description="Number of days for meal plan"),
        dietary_restrictions: Optional[str] = Query(default=None,\
                                                    description="Dietary restrictions (vegetarian, vegan, gluten-free, etc.)"),
        cuisine_type: Optional[str] = Query(default=None, description="Preferred cuisine type"),
        current_user: User = Depends(deps.get_current_active_user),\
        db: AsyncSession = Depends(get_db)
):
    """Generate a meal plan for specified number of days."""
    try:
        meal_types = ["breakfast", "lunch", "dinner"]
        meal_plan_data = []
        all_ingredients = []

        for day in range(days):
            day_meals = {}
            date_str = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")

            for meal_type in meal_types:
                # Create search query based on meal type and preferences
                search_query = meal_type
                if dietary_restrictions:
                    search_query += f" {dietary_restrictions}"
                if cuisine_type:
                    search_query += f" {cuisine_type}"

                # Get recipes for this meal
                recipes = await scraper.search_recipes(search_query, max_results=1, include_videos=False)
                if recipes:
                    day_meals[meal_type] = recipes[0].dict()  # Convert Recipe object to dict
                    all_ingredients.extend(recipes[0].ingredients)

            meal_plan_data.append({
                "date": date_str,
                "meals": day_meals,
            })
        
        # Generate shopping list (simple deduplication)
        shopping_list = sorted(list(set(all_ingredients)))

        # Placeholder for total nutrition
        total_nutrition = {"calories": "N/A", "protein": "N/A"}

        meal_plan_name = f"Meal Plan for {days} days - {datetime.now().strftime('%Y-%m-%d')}"
        meal_plan_obj = MealPlanCreate(
            name=meal_plan_name,
            plan_data={
                "meal_plan": meal_plan_data,
                "duration_days": days,
                "dietary_restrictions": dietary_restrictions,
                "cuisine_type": cuisine_type,
                "shopping_list": shopping_list,
                "total_nutrition": total_nutrition
            }
        )
        
        saved_meal_plan = await create_meal_plan(db, meal_plan_obj, current_user.id)

        return saved_meal_plan

    except Exception as e:
        logger.error(f"Error generating meal plan: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/nutrition/analyze", response_model=NutritionAnalysis)
async def analyze_recipe_nutrition(
        recipe_url: HttpUrl = Query(..., description="Recipe URL to analyze"),
        include_health_score: bool = Query(default=True, description="Include calculated health score")
):
    """Analyze the nutritional content of a recipe."""
    try:
        # Scrape the recipe first
        async with aiohttp.ClientSession(headers=scraper.headers) as session:
            recipe = await scraper.scrape_recipe(session, str(recipe_url), include_videos=False)

        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Simple nutrition estimation based on ingredients
        estimated_nutrition = {
            "calories": "Estimated 300-500 per serving",
            "protein": "Variable based on ingredients",
            "carbohydrates": "Variable based on ingredients",
            "fat": "Variable based on ingredients",
            "fiber": "Variable based on ingredients"
        }

        # Simple health score calculation
        health_score = 7.5  # Placeholder

        # Basic dietary tags
        dietary_tags = []
        if recipe.ingredients:
            ingredients_text = " ".join(recipe.ingredients).lower()
            if "chicken" in ingredients_text or "beef" in ingredients_text:
                dietary_tags.append("high-protein")
            if "vegetable" in ingredients_text or "spinach" in ingredients_text:
                dietary_tags.append("vegetable-rich")
            if "whole grain" in ingredients_text or "brown rice" in ingredients_text:
                dietary_tags.append("whole-grain")

        return NutritionAnalysis(
            recipe_title=recipe.title,
            estimated_nutrition=estimated_nutrition,
            health_score=health_score,
            dietary_tags=dietary_tags
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing nutrition: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/ingredient")
async def search_by_ingredient(
        ingredient: str = Query(..., description="Main ingredient to search for"),
        limit: int = Query(default=10, ge=1, le=30, description="Maximum number of results"),
        exclude_ingredients: Optional[str] = Query(default=None, description="Comma-separated ingredients to exclude")
):
    """Search for recipes by main ingredient."""
    try:
        search_query = f"{ingredient} recipes"
        recipes = await scraper.search_recipes(search_query, limit, include_videos=False)

        # Filter out recipes with excluded ingredients
        if exclude_ingredients:
            excluded = [ing.strip().lower() for ing in exclude_ingredients.split(",")]
            filtered_recipes = []
            for recipe in recipes:
                ingredients_text = " ".join(recipe.ingredients).lower()
                if not any(exc in ingredients_text for exc in excluded):
                    filtered_recipes.append(recipe)
            recipes = filtered_recipes

        return {
            "recipes": recipes,
            "main_ingredient": ingredient,
            "excluded_ingredients": exclude_ingredients.split(",") if exclude_ingredients else [],
            "total_found": len(recipes)
        }

    except Exception as e:
        logger.error(f"Error searching by ingredient: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/quick")
async def search_quick_recipes(
        max_prep_time: int = Query(default=30, ge=5, le=120, description="Maximum preparation time in minutes"),
        difficulty: str = Query(default="easy", description="Recipe difficulty level"),
        limit: int = Query(default=15, ge=1, le=30, description="Maximum number of results")
):
    """Search for quick and easy recipes."""
    try:
        search_query = f"quick {difficulty} recipes under {max_prep_time} minutes"
        recipes = await scraper.search_recipes(search_query, limit, include_videos=True)

        return {
            "recipes": recipes,
            "max_prep_time": max_prep_time,
            "difficulty": difficulty,
            "total_found": len(recipes)
        }

    except Exception as e:
        logger.error(f"Error searching quick recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/dietary")
async def search_dietary_recipes(
        diet_type: str = Query(..., description="Diet type (vegetarian, vegan, keto, paleo, etc.)"),
        limit: int = Query(default=15, ge=1, le=30, description="Maximum number of results"),
        include_nutrition: bool = Query(default=True, description="Include nutrition information")
):
    """Search for recipes by dietary restriction or type."""
    try:
        search_query = f"{diet_type} recipes"
        recipes = await scraper.search_recipes(search_query, limit, include_videos=False)

        return {
            "recipes": recipes,
            "diet_type": diet_type,
            "include_nutrition": include_nutrition,
            "total_found": len(recipes)
        }

    except Exception as e:
        logger.error(f"Error searching dietary recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/random")
async def get_random_recipes(
        count: int = Query(default=5, ge=1, le=20, description="Number of random recipes")
):
    """Get random recipes from various categories."""
    try:
        categories = [
            "dinner recipes", "lunch ideas", "breakfast recipes",
            "dessert recipes", "snack recipes", "appetizer recipes",
            "soup recipes", "salad recipes", "pasta recipes"
        ]

        all_recipes = []
        for category in random.sample(categories, min(count, len(categories))):
            recipes = await scraper.search_recipes(category, max_results=2, include_videos=False)
            all_recipes.extend(recipes)

        # Shuffle and limit
        random.shuffle(all_recipes)

        return {
            "random_recipes": all_recipes[:count],
            "total_found": len(all_recipes),
            "categories_used": categories
        }

    except Exception as e:
        logger.error(f"Error getting random recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/popular")
async def get_popular_recipes(
        limit: int = Query(default=20, ge=1, le=50, description="Number of popular recipes to return")
):
    """Get popular recipes (searches for trending terms)."""
    popular_searches = [
        "chicken recipes",
        "pasta recipes",
        "easy dinner",
        "healthy recipes",
        "dessert recipes",
        "beef recipes",
        "vegetarian meals"
    ]

    try:
        all_recipes = []
        for search_term in popular_searches:
            recipes = await scraper.search_recipes(search_term, limit // len(popular_searches), include_videos=False)
            all_recipes.extend(recipes)

        return {
            "recipes": all_recipes[:limit],
            "total_found": len(all_recipes),
            "categories": popular_searches
        }

    except Exception as e:
        logger.error(f"Error getting popular recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/category/{category}")
async def search_by_category(
        category: str,
        limit: int = Query(default=10, ge=1, le=50, description="Number of recipes to return"),
        include_videos: bool = Query(default=True, description="Include video tutorials")
):
    """Search recipes by category."""
    try:
        recipes = await scraper.search_recipes(category, limit, include_videos)

        # Get category-specific videos
        videos = []
        if include_videos:
            videos = video_scraper.get_youtube_videos(f"{category} recipes", max_results=3)

        return {
            "recipes": recipes,
            "category": category,
            "total_found": len(recipes),
            "videos": videos
        }

    except Exception as e:
        logger.error(f"Error searching by category: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/batch/urls")
async def batch_scrape_urls(
        urls: str = Query(..., description="Comma-separated list of recipe URLs"),
        max_concurrent: int = Query(default=5, ge=1, le=10, description="Maximum concurrent requests")
):
    """Scrape multiple recipe URLs in batch."""
    try:
        url_list = [url.strip() for url in urls.split(",")]

        if len(url_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed")

        async with aiohttp.ClientSession(headers=scraper.headers) as session:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await scraper.scrape_recipe(session, url, include_videos=False)

            tasks = [scrape_with_semaphore(url) for url in url_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_recipes = [r for r in results if isinstance(r, Recipe)]
        failed_urls = [url_list[i] for i, r in enumerate(results) if not isinstance(r, Recipe)]

        return {
            "successful_recipes": successful_recipes,
            "failed_urls": failed_urls,
            "total_requested": len(url_list),
            "successful_count": len(successful_recipes),
            "failed_count": len(failed_urls)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch scraping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/advanced")
async def advanced_search(
        query: str = Query(..., description="Search query"),
        cuisine: Optional[str] = Query(default=None, description="Cuisine type"),
        diet: Optional[str] = Query(default=None, description="Dietary restriction"),
        max_time: Optional[int] = Query(default=None, description="Maximum cooking time in minutes"),
        difficulty: Optional[str] = Query(default=None, description="Difficulty level"),
        min_rating: Optional[float] = Query(default=None, description="Minimum rating"),
        limit: int = Query(default=10, ge=1, le=30, description="Maximum results")
):
    """Advanced recipe search with multiple filters."""
    try:
        # Build enhanced search query
        search_terms = [query]
        if cuisine:
            search_terms.append(cuisine)
        if diet:
            search_terms.append(diet)
        if difficulty:
            search_terms.append(difficulty)

        enhanced_query = " ".join(search_terms)
        recipes = await scraper.search_recipes(enhanced_query, limit, include_videos=False)

        # Apply filters (simplified)
        filtered_recipes = recipes
        if min_rating:
            filtered_recipes = [r for r in filtered_recipes if r.rating and r.rating.get('value', 0) >= min_rating]

        return {
            "recipes": filtered_recipes,
            "filters_applied": {
                "cuisine": cuisine,
                "diet": diet,
                "max_time": max_time,
                "difficulty": difficulty,
                "min_rating": min_rating
            },
            "total_found": len(filtered_recipes)
        }

    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/generate-from-ingredients")
async def generate_recipe_from_ingredients_endpoint(
    ingredients: List[str],
    current_user: User = Depends(deps.get_current_active_user)
):
    """Generate a recipe based on a list of ingredients using AI."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=501, detail="AI features are not enabled (GEMINI_API_KEY is missing).")
    
    generated_recipe = await ai_service.generate_recipe_from_ingredients(ingredients)
    return {"generated_recipe": generated_recipe}

@router.post("/suggest-substitute")
async def suggest_ingredient_substitute_endpoint(
    original_ingredient: str,
    recipe_context: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user)
):
    """Suggest a substitute for an ingredient using AI."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=501, detail="AI features are not enabled (GEMINI_API_KEY is missing).")
    
    suggested_substitute = await ai_service.suggest_ingredient_substitute(original_ingredient, recipe_context)
    return {"suggested_substitute": suggested_substitute}