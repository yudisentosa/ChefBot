import os
import requests
import json
import logging
from typing import List, Dict, Any

class ChefBot:
    API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"  # Updated endpoint

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")

    def suggest_recipe(self, ingredients: List[str]) -> Dict[str, Any]:
        """
        Generate recipe suggestions based on available ingredients.
        
        Args:
            ingredients (List[str]): List of available ingredient names
            
        Returns:
            Dict[str, Any]: Recipe suggestion including name, ingredients, and steps
        """
        if not ingredients:
            return {
                "recipe_name": "No Recipe",
                "ingredients_required": [],
                "missing_ingredients": [],
                "instructions": ["Please add some ingredients first"],
                "difficulty_level": "N/A",
                "cooking_time": "0"
            }

        prompt = self._create_recipe_prompt(ingredients)
        
        try:
            response = self._call_deepseek_api(prompt)
            return self._parse_recipe_response(response)
        except Exception as e:
            self.logger.error(f"Recipe suggestion failed: {str(e)}")
            return {
                "recipe_name": "Error",
                "ingredients_required": ingredients,
                "missing_ingredients": [],
                "instructions": [f"Failed to generate recipe: {str(e)}. Please try again later."],
                "difficulty_level": "N/A",
                "cooking_time": "0"
            }

    def _create_recipe_prompt(self, ingredients: List[str]) -> str:
        """Create a prompt for the DeepSeek API based on ingredients."""
        return f"""You are a professional chef. Create a recipe for 2 servings using these ingredients: {', '.join(ingredients)}.
        Return ONLY a valid JSON object with this exact structure, no other text or explanation:
        {{
            "recipe_name": "Name of the dish",
            "ingredients_required": ["ingredient 1 with quantity", "ingredient 2 with quantity"],
            "missing_ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["Step 1", "Step 2"],
            "difficulty_level": "easy/medium/hard",
            "cooking_time": "30"
        }}
        
        Make sure all ingredient quantities are appropriate for 2 servings. The recipe will be scaled for more servings later."""

    def _call_deepseek_api(self, prompt: str) -> str:
        """Make API call to DeepSeek."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a professional chef who provides recipe suggestions in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            self.logger.info("Calling DeepSeek API...")
            response = requests.post(
                self.API_ENDPOINT,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 401:
                raise Exception("Invalid API key. Please check your DeepSeek API key.")
            elif response.status_code == 429:
                raise Exception("Too many requests. Please try again later.")
            elif response.status_code != 200:
                raise Exception(f"API call failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise Exception("No response choices found")
                
            content = result["choices"][0]["message"]["content"]
            return content.strip()
            
        except requests.exceptions.Timeout:
            raise Exception("API request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to the API. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def _parse_recipe_response(self, response: str) -> Dict[str, Any]:
        """Parse the API response into a structured recipe format."""
        try:
            # Try to find JSON content if there's any surrounding text
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = response[start_idx:end_idx]
            recipe_data = json.loads(json_str)
            
            # Validate and ensure all required fields
            required_fields = {
                "recipe_name": str,
                "ingredients_required": list,
                "instructions": list
            }
            
            for field, field_type in required_fields.items():
                if field not in recipe_data:
                    recipe_data[field] = [] if field_type == list else "Unnamed Recipe"
                elif not isinstance(recipe_data[field], field_type):
                    recipe_data[field] = field_type()
            
            # Ensure optional fields
            if "missing_ingredients" not in recipe_data:
                recipe_data["missing_ingredients"] = []
            if "difficulty_level" not in recipe_data:
                recipe_data["difficulty_level"] = "medium"
            if "cooking_time" not in recipe_data:
                recipe_data["cooking_time"] = "30"
            
            return recipe_data
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse recipe response: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing recipe: {str(e)}")

if __name__ == "__main__":
    pass