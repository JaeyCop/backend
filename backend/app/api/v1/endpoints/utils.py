from fastapi import APIRouter
from app.services.cache import cache
from datetime import datetime
from app.schemas.recipe import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0"
    )


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return {
        "cache_stats": cache.stats(),
        "cache_ttl_seconds": cache.ttl_seconds
    }


@router.post("/cache/clear")
async def clear_cache():
    """Clear the cache."""
    cache.clear()
    return {"message": "Cache cleared successfully"}


@router.get("/stats")
async def get_api_stats():
    """Get API statistics."""
    return {
        "api_version": "2.0.0",
        "uptime": "N/A",  # Would need to track this
        "cache_stats": cache.stats(),
        "supported_sites": ["allrecipes.com"],
        "supported_video_platforms": ["youtube.com"],
        "max_results_per_query": 50,
        "features": [
            "recipe_scraping",
            "video_tutorials",
            "meal_planning",
            "nutrition_analysis",
            "recipe_recommendations",
            "batch_processing",
            "advanced_search"
        ]
    }


@router.get("/endpoints")
async def list_endpoints():
    """List all available API endpoints."""
    return {
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API health check"},
            {"path": "/health", "method": "GET", "description": "Health status"},
            {"path": "/search", "method": "GET", "description": "Search recipes"},
            {"path": "/search", "method": "POST", "description": "Advanced search with filters"},
            {"path": "/recipe", "method": "GET", "description": "Get single recipe details"},
            {"path": "/videos/search", "method": "GET", "description": "Search recipe videos"},
            {"path": "/recommendations", "method": "GET", "description": "Get recipe recommendations"},
            {"path": "/trending", "method": "GET", "description": "Get trending recipes"},
            {"path": "/meal-plan/generate", "method": "GET", "description": "Generate meal plan"},
            {"path": "/nutrition/analyze", "method": "GET", "description": "Analyze recipe nutrition"},
            {"path": "/search/ingredient", "method": "GET", "description": "Search by ingredient"},
            {"path": "/search/quick", "method": "GET", "description": "Search quick recipes"},
            {"path": "/search/dietary", "method": "GET", "description": "Search by dietary restriction"},
            {"path": "/random", "method": "GET", "description": "Get random recipes"},
            {"path": "/popular", "method": "GET", "description": "Get popular recipes"},
            {"path": "/categories", "method": "GET", "description": "List recipe categories"},
            {"path": "/search/category/{category}", "method": "GET", "description": "Search by category"},
            {"path": "/batch/urls", "method": "GET", "description": "Batch scrape multiple URLs"},
            {"path": "/search/advanced", "method": "GET", "description": "Advanced search with filters"},
            {"path": "/cache/stats", "method": "GET", "description": "Get cache statistics"},
            {"path": "/cache/clear", "method": "POST", "description": "Clear cache"},
            {"path": "/stats", "method": "GET", "description": "Get API statistics"},
            {"path": "/endpoints", "method": "GET", "description": "List all endpoints"}
        ],
        "total_endpoints": 23
    }


@router.get("/categories")
async def get_categories():
    """Get available recipe categories."""
    categories = [
        "appetizers", "breakfast", "lunch", "dinner", "dessert",
        "salads", "soups", "main-dishes", "side-dishes", "snacks",
        "beverages", "bread", "pasta", "pizza", "chicken", "beef",
        "pork", "seafood", "vegetarian", "vegan", "gluten-free",
        "low-carb", "healthy", "quick-easy", "slow-cooker", "instant-pot",
        "air-fryer", "one-pot", "meal-prep", "comfort-food", "international"
    ]

    return {
        "categories": categories,
        "total_categories": len(categories)
    }
