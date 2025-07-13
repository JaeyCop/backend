import google.generativeai as genai
import os

class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def get_semantic_search_query(self, user_query: str) -> str:
        prompt = f"""Given the following user query for a recipe search, extract the most relevant keywords or a refined search phrase that would yield the best results. Focus on ingredients, cuisine types, dish names, or cooking styles. If the query is already concise, return it as is. Do not include any conversational filler or explanations, just the refined query. 

User query: {user_query}
Refined query:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return user_query # Fallback to original query on error

    async def generate_recipe_from_ingredients(self, ingredients: list[str]) -> str:
        prompt = f"""Generate a creative and complete recipe using only the following ingredients: {', '.join(ingredients)}. Include title, description, ingredients list with quantities, and step-by-step instructions. Format it clearly and concisely. If possible, suggest a cuisine style.

Recipe:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating recipe from ingredients: {e}")
            return "Could not generate a recipe with the given ingredients." # Fallback on error

    async def suggest_ingredient_substitute(self, original_ingredient: str, recipe_context: str = "") -> str:
        prompt = f"""Suggest a good substitute for '{original_ingredient}'. Consider the following recipe context if provided: '{recipe_context}'. Provide 2-3 common and effective substitutes, and briefly explain why each works (e.g., similar flavor, texture, or function). Format as a list.

Substitutes:"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error suggesting ingredient substitute: {e}")
            return "Could not suggest a substitute for this ingredient." # Fallback on error

ai_service = AIService()