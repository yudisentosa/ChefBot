from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
import requests
from typing import List, Dict, Any

class ChefBot:
    def __init__(self, api_key: str):
        self.api_key = api_key
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
        prompt = self._create_recipe_prompt(ingredients)
        
        try:
            response = self._call_deepseek_api(prompt)
            return self._parse_recipe_response(response)
        except Exception as e:
            raise Exception(f"Failed to generate recipe suggestion: {str(e)}")

    def _create_recipe_prompt(self, ingredients: List[str]) -> str:
        """Create a prompt for the DeepSeek API based on ingredients."""
        return f"""Given these ingredients: {', '.join(ingredients)}
        Suggest a recipe that can be made with these ingredients.
        Please format the response as JSON with the following structure:
        {{
            "recipe_name": "Name of the dish",
            "possible_with_ingredients": true/false,
            "ingredients_required": ["list", "of", "ingredients", "with", "quantities"],
            "missing_ingredients": ["list", "of", "missing", "ingredients"],
            "instructions": ["Step 1", "Step 2", "..."],
            "difficulty_level": "easy/medium/hard",
            "cooking_time": "estimated time in minutes"
        }}"""

    def _call_deepseek_api(self, prompt: str) -> str:
        """Make API call to DeepSeek."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.text}")
            
        return response.json()["choices"][0]["message"]["content"]

    def _parse_recipe_response(self, response: str) -> Dict[str, Any]:
        """Parse the API response into a structured recipe format."""
        try:
            # Clean up response if needed and parse JSON
            import json
            recipe_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["recipe_name", "ingredients_required", "instructions"]
            for field in required_fields:
                if field not in recipe_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return recipe_data
        except json.JSONDecodeError:
            raise Exception("Failed to parse recipe response")

model_name = "facebook/blenderbot-400M-distill"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Initialize conversation history
conversation_history = []

while True:
    # Create conversation history string
    history_string = "\n".join(conversation_history)

    # Get the input data from the user
    input_text = input("> ")

    # Tokenize the input text and history
    inputs = tokenizer.encode_plus(history_string, input_text, return_tensors="pt")

    # Generate the response from the model
    outputs = model.generate(**inputs)

    # Decode the response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    
    print(response)

    # Add interaction to conversation history
    conversation_history.append(input_text)
    conversation_history.append(response)