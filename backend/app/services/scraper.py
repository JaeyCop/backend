import asyncio
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote_plus

import aiohttp
from bs4 import BeautifulSoup

from app.schemas.recipe import Recipe
from app.services.video_scraper import video_scraper

logger = logging.getLogger(__name__)


class AsyncRecipeScraper:
    def __init__(self, delay: float = 1.0, timeout: int = 15):
        self.base_url = "https://www.allrecipes.com"
        self.search_url = f"{self.base_url}/search"
        self.delay = delay
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    async def search_recipes(self, query: str, max_results: int = 10, include_videos: bool = True) -> List[Recipe]:
        """Search for recipes asynchronously."""
        try:
            search_url = f"{self.search_url}?q={quote_plus(query)}"

            async with aiohttp.ClientSession(headers=self.headers,
                                             timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.error(f"Search request failed with status {response.status}")
                        return []

                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")

                    # Find recipe links
                    recipe_links = soup.select("a[href*='/recipe/']")

                    if not recipe_links:
                        logger.warning("No recipe links found")
                        return []

                    # Remove duplicates and limit results
                    unique_links = []
                    seen_hrefs = set()
                    for link in recipe_links:
                        href = link.get('href', '')
                        if href and href not in seen_hrefs:
                            seen_hrefs.add(href)
                            unique_links.append(urljoin(self.base_url, href))

                    unique_links = unique_links[:max_results]

                    # Scrape recipes concurrently
                    tasks = []
                    for i, recipe_url in enumerate(unique_links):
                        if i > 0:
                            # Add delay between requests
                            await asyncio.sleep(self.delay)
                        tasks.append(self.scrape_recipe(session, recipe_url, include_videos))

                    recipes = await asyncio.gather(*tasks, return_exceptions=True)

                    # Filter out None results and exceptions
                    valid_recipes = [
                        recipe for recipe in recipes
                        if isinstance(recipe, Recipe)
                    ]

                    return valid_recipes

        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []

    async def scrape_recipe(self, session: aiohttp.ClientSession, recipe_url: str,
                            include_videos: bool = True) -> Optional[Recipe]:
        """Scrape a single recipe."""
        try:
            async with session.get(recipe_url) as response:
                if response.status != 200:
                    logger.error(f"Recipe request failed with status {response.status}")
                    return None

                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")

                # Try JSON-LD first
                json_data = self._extract_json_ld(soup)
                if json_data:
                    json_data["source_url"] = recipe_url

                    # Add video URL if requested
                    if include_videos and json_data.get("title"):
                        json_data["video_url"] = video_scraper.get_single_youtube_link(json_data["title"])

                    return Recipe(**json_data)

                # Fallback to HTML scraping
                recipe_data = {
                    "title": self._extract_title(soup),
                    "ingredients": self._extract_ingredients(soup),
                    "instructions": self._extract_instructions(soup),
                    "image_url": self._extract_image_url(soup),
                    "time_info": self._extract_time_info(soup),
                    "rating": self._extract_rating(soup),
                    "servings": self._extract_servings(soup),
                    "description": self._extract_description(soup),
                    "source_url": recipe_url,
                    "tags": self._extract_tags(soup),
                    "difficulty": self._extract_difficulty(soup)
                }

                # Add video URL if requested
                if include_videos and recipe_data["title"]:
                    recipe_data["video_url"] = video_scraper.get_single_youtube_link(recipe_data["title"])

                if recipe_data["title"]:
                    return Recipe(**recipe_data)

                return None

        except Exception as e:
            logger.error(f"Error scraping recipe {recipe_url}: {e}")
            return None

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract recipe data from JSON-LD structured data."""
        try:
            json_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_scripts:
                try:
                    data = json.loads(script.string)

                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Recipe':
                                return self._parse_json_ld_recipe(item)
                    elif data.get('@type') == 'Recipe':
                        return self._parse_json_ld_recipe(data)
                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error extracting JSON-LD: {e}")
            return None

    def _parse_json_ld_recipe(self, recipe_data: Dict) -> Dict:
        """Parse recipe from JSON-LD structured data."""
        try:
            ingredients = recipe_data.get('recipeIngredient', [])

            instructions = []
            for instruction in recipe_data.get('recipeInstructions', []):
                if isinstance(instruction, dict):
                    text = instruction.get('text', '')
                    if text:
                        instructions.append(text)
                elif isinstance(instruction, str):
                    instructions.append(instruction)

            time_info = {}
            if 'prepTime' in recipe_data:
                time_info['prep_time'] = recipe_data['prepTime']
            if 'cookTime' in recipe_data:
                time_info['cook_time'] = recipe_data['cookTime']
            if 'totalTime' in recipe_data:
                time_info['total_time'] = recipe_data['totalTime']

            rating = None
            if 'aggregateRating' in recipe_data:
                rating_data = recipe_data['aggregateRating']
                rating = {
                    'value': rating_data.get('ratingValue'),
                    'count': rating_data.get('ratingCount')
                }

            image_url = None
            if 'image' in recipe_data:
                image = recipe_data['image']
                if isinstance(image, dict):
                    image_url = image.get('url')
                elif isinstance(image, str):
                    image_url = image
                elif isinstance(image, list) and image:
                    image_url = image[0] if isinstance(image[0], str) else image[0].get('url')

            # Extract nutrition info
            nutrition = None
            if 'nutrition' in recipe_data:
                nutrition_data = recipe_data['nutrition']
                if isinstance(nutrition_data, dict):
                    nutrition = {
                        'calories': nutrition_data.get('calories'),
                        'protein': nutrition_data.get('proteinContent'),
                        'carbs': nutrition_data.get('carbohydrateContent'),
                        'fat': nutrition_data.get('fatContent'),
                        'fiber': nutrition_data.get('fiberContent'),
                        'sugar': nutrition_data.get('sugarContent')
                    }

            # Extract keywords/tags
            tags = []
            if 'keywords' in recipe_data:
                if isinstance(recipe_data['keywords'], list):
                    tags = recipe_data['keywords']
                elif isinstance(recipe_data['keywords'], str):
                    tags = [tag.strip() for tag in recipe_data['keywords'].split(',')]

            return {
                'title': recipe_data.get('name', ''),
                'ingredients': ingredients,
                'instructions': instructions,
                'image_url': image_url,
                'time_info': time_info,
                'rating': rating,
                'servings': str(recipe_data.get('recipeYield', '')),
                'description': recipe_data.get('description', ''),
                'nutrition': nutrition,
                'tags': tags
            }

        except Exception as e:
            logger.error(f"Error parsing JSON-LD recipe: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML."""
        selectors = [
            "h1.entry-title",
            "h1.recipe-title",
            "h1.mntl-text-block",
            "h1.headline",
            "h1"
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_ingredients(self, soup: BeautifulSoup) -> List[str]:
        """Extract ingredients from HTML."""
        selectors = [
            "[data-test-id*='ingredient']",
            ".mntl-structured-ingredients__list-item",
            ".recipe-ingredient",
            ".ingredients-item-name"
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                ingredients = []
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 1:
                        ingredients.append(text)
                if ingredients:
                    return ingredients

        return []

    def _extract_instructions(self, soup: BeautifulSoup) -> List[str]:
        """Extract instructions from HTML."""
        selectors = [
            "[data-test-id*='instruction']",
            ".mntl-sc-block-group--OL .mntl-sc-block",
            ".recipe-instruction",
            ".instructions-section-item p"
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                instructions = []
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10:
                        instructions.append(text)
                if instructions:
                    return instructions

        return []

    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract image URL from HTML."""
        selectors = [
            ".primary-image img",
            ".recipe-image img",
            ".mntl-primary-image img"
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get("data-src") or element.get("src")

        return None

    def _extract_time_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract time info from HTML."""
        return {}  # Simplified for now

    def _extract_rating(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract rating from HTML."""
        return None  # Simplified for now

    def _extract_servings(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract servings from HTML."""
        return None  # Simplified for now

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from HTML."""
        return None  # Simplified for now

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags from HTML."""
        return []  # Simplified for now

    def _extract_difficulty(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract difficulty from HTML."""
        return None  # Simplified for now


scraper = AsyncRecipeScraper(delay=0.5, timeout=15)
