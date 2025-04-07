import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeepSeekService:
    """Service for interacting with the DeepSeek API for recipe suggestions."""
    
    API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the DeepSeek service.
        
        Args:
            api_key: DeepSeek API key. If not provided, will try to get from environment.
        """
        # Try to get API key from provided parameter, DEEPSEEK_API_KEY, or CHEFBOT_API_KEY
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("CHEFBOT_API_KEY")
        self.use_mock = not self.api_key
        if not self.api_key:
            self.logger = logging.getLogger(__name__)
            self.logger.warning("DeepSeek API key not found. Using mock responses.")
        
        self.logger = logging.getLogger(__name__)
    
    def suggest_recipe(self, ingredients: List[str], servings: int = 2) -> Dict[str, Any]:
        """
        Generate recipe suggestions based on available ingredients.
        
        Args:
            ingredients: List of available ingredient names
            servings: Number of servings to prepare
            
        Returns:
            Dict containing recipe suggestion including name, ingredients, and steps
        """
        if not ingredients:
            return {
                "recipe_name": "No Recipe",
                "ingredients_required": [],
                "missing_ingredients": [],
                "instructions": ["Please add some ingredients first"],
                "difficulty_level": "N/A",
                "cooking_time": "0",
                "servings": servings
            }
        
        prompt = self._create_recipe_prompt(ingredients, servings)
        
        try:
            response = self._call_deepseek_api(prompt)
            recipe = self._parse_recipe_response(response)
            recipe["servings"] = servings
            return recipe
        except Exception as e:
            self.logger.error(f"Recipe suggestion failed: {str(e)}")
            return {
                "recipe_name": "Error",
                "ingredients_required": ingredients,
                "missing_ingredients": [],
                "instructions": [f"Failed to generate recipe: {str(e)}. Please try again later."],
                "difficulty_level": "N/A",
                "cooking_time": "0",
                "servings": servings
            }
    
    def _create_recipe_prompt(self, ingredients: List[str], servings: int) -> str:
        """Create a prompt for the DeepSeek API based on ingredients."""
        return f"""You are a professional chef. Create a recipe for {servings} servings using these ingredients: {', '.join(ingredients)}.
        Return ONLY a valid JSON object with this exact structure, no other text or explanation:
        {{
            "recipe_name": "Name of the dish",
            "ingredients_required": ["ingredient 1 with quantity", "ingredient 2 with quantity"],
            "missing_ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["Step 1", "Step 2"],
            "difficulty_level": "easy/medium/hard",
            "cooking_time": "30"
        }}
        
        Make sure all ingredient quantities are appropriate for {servings} servings."""
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """Make API call to DeepSeek."""
        # Use mock response if API key is not available
        if self.use_mock:
            self.logger.info("Using mock response instead of calling DeepSeek API")
            return self._get_mock_response(prompt)
        
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_ENDPOINT,
                    headers=headers,
                    json=data
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
                
        except httpx.TimeoutException:
            raise Exception("API request timed out. Please try again.")
        except httpx.ConnectError:
            raise Exception("Could not connect to the API. Please check your internet connection.")
        except Exception as e:
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
            
    def _get_mock_response(self, prompt: str) -> str:
        """Generate a mock response when API key is not available."""
        # Extract ingredients from the prompt
        ingredients_start = prompt.find("using these ingredients: ") + len("using these ingredients: ")
        ingredients_end = prompt.find(".", ingredients_start)
        ingredients_text = prompt[ingredients_start:ingredients_end]
        ingredients_list = [ing.strip() for ing in ingredients_text.split(',')]
        
        # Extract servings from the prompt
        servings_start = prompt.find("Create a recipe for ") + len("Create a recipe for ")
        servings_end = prompt.find(" servings", servings_start)
        servings = prompt[servings_start:servings_end]
        
        # Create a mock recipe based on the available ingredients
        if any(ing in ['egg', 'eggs'] for ing in ingredients_list):
            recipe_name = "Simple Omelette"
            instructions = [
                "Beat the eggs in a bowl and season with salt and pepper.",
                "Heat a non-stick pan over medium heat and add butter or oil.",
                "Pour in the egg mixture and cook for 2-3 minutes until the bottom is set.",
                "Add any additional ingredients like cheese, vegetables, or herbs.",
                "Fold the omelette in half and cook for another minute.",
                "Serve hot with your favorite side dishes."
            ]
            difficulty = "easy"
            cooking_time = "15"
        elif any(ing in ['chicken', 'beef', 'pork', 'meat'] for ing in ingredients_list):
            recipe_name = "Simple Stir Fry"
            instructions = [
                "Cut the meat into thin strips and marinate with soy sauce and garlic.",
                "Chop any vegetables into bite-sized pieces.",
                "Heat oil in a wok or large pan over high heat.",
                "Cook the meat until browned, about 3-4 minutes.",
                "Add the vegetables and stir-fry for another 3-4 minutes.",
                "Add sauce and seasonings, then cook for 1-2 more minutes.",
                "Serve hot over rice or noodles."
            ]
            difficulty = "medium"
            cooking_time = "25"
        else:
            recipe_name = "Mixed Vegetable Salad"
            instructions = [
                "Wash and chop all vegetables into bite-sized pieces.",
                "Combine all ingredients in a large bowl.",
                "In a small bowl, whisk together olive oil, vinegar, salt, and pepper for the dressing.",
                "Pour the dressing over the salad and toss to combine.",
                "Chill in the refrigerator for 30 minutes before serving."
            ]
            difficulty = "easy"
            cooking_time = "15"
        
        # Format ingredients with quantities
        ingredients_with_qty = []
        for ing in ingredients_list:
            if ing in ['egg', 'eggs']:
                ingredients_with_qty.append(f"{int(servings) * 2} {ing}")
            elif ing in ['salt', 'pepper', 'oil', 'vinegar']:
                ingredients_with_qty.append(f"1 teaspoon {ing}")
            elif ing in ['water', 'milk', 'juice']:
                ingredients_with_qty.append(f"{int(servings) * 100} ml {ing}")
            else:
                ingredients_with_qty.append(f"{int(servings) * 50} g {ing}")
        
        # Create the mock response in JSON format
        mock_response = {
            "recipe_name": recipe_name,
            "ingredients_required": ingredients_with_qty,
            "missing_ingredients": [],
            "instructions": instructions,
            "difficulty_level": difficulty,
            "cooking_time": cooking_time
        }
        
        return json.dumps(mock_response, indent=2)
