import gradio as gr
import requests
from typing import Dict, Any, List
import json

class ChefBotUI:
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        self.api_base_url = api_base_url.rstrip('/')
        
    def _get_ingredients(self) -> List[Dict[str, Any]]:
        """Fetch ingredients from the API."""
        response = requests.get(f"{self.api_base_url}/api/ingredients")
        if response.status_code == 200:
            return response.json()
        return []
        
    def _add_ingredient(self, name: str, quantity: float, unit: str) -> Dict[str, Any]:
        """Add a new ingredient via the API."""
        data = {
            "name": name,
            "quantity": quantity,
            "unit": unit
        }
        response = requests.post(f"{self.api_base_url}/api/ingredients", json=data)
        return response.json()
        
    def _get_recipe_suggestion(self) -> Dict[str, Any]:
        """Get recipe suggestions based on available ingredients."""
        response = requests.get(f"{self.api_base_url}/api/suggest-recipe")
        if response.status_code == 200:
            return response.json()
        return {"error": "Failed to get recipe suggestion"}

    def _format_recipe(self, recipe: Dict[str, Any]) -> str:
        """Format recipe data into a readable string."""
        if "error" in recipe:
            return f"Error: {recipe['error']}"
            
        return f"""
# {recipe['recipe_name']}

## Required Ingredients:
{chr(10).join(f'- {ingredient}' for ingredient in recipe['ingredients_required'])}

## Missing Ingredients:
{chr(10).join(f'- {ingredient}' for ingredient in recipe.get('missing_ingredients', []))}

## Instructions:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(recipe['instructions']))}

Difficulty: {recipe.get('difficulty_level', 'N/A')}
Cooking Time: {recipe.get('cooking_time', 'N/A')} minutes
"""

    def handle_add_ingredient(self, name: str, quantity: str, unit: str) -> str:
        """Handle adding a new ingredient."""
        try:
            quantity = float(quantity) if quantity else 0
            if not name:
                return "Error: Ingredient name is required"
                
            result = self._add_ingredient(name, quantity, unit)
            if "error" in result:
                return f"Error: {result['error']}"
                
            return f"Successfully added {name}"
        except ValueError:
            return "Error: Invalid quantity format"
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_get_recipe(self) -> str:
        """Handle getting recipe suggestions."""
        try:
            ingredients = self._get_ingredients()
            if not ingredients:
                return "Error: No ingredients available. Please add some ingredients first."
                
            recipe = self._get_recipe_suggestion()
            return self._format_recipe(recipe)
        except Exception as e:
            return f"Error: {str(e)}"

    def list_ingredients(self) -> str:
        """List all available ingredients."""
        try:
            ingredients = self._get_ingredients()
            if not ingredients:
                return "No ingredients available"
                
            result = "# Available Ingredients\n\n"
            for ing in ingredients:
                result += f"- {ing['name']}: {ing['quantity']} {ing['unit']}\n"
            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def create_ui(self) -> gr.Blocks:
        """Create and configure the Gradio interface."""
        with gr.Blocks(title="Chef Bot", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 👨‍🍳 Chef Bot")
            gr.Markdown("Your AI-powered cooking assistant")
            
            with gr.Tab("Add Ingredients"):
                with gr.Row():
                    name_input = gr.Textbox(label="Ingredient Name")
                    quantity_input = gr.Textbox(label="Quantity")
                    unit_input = gr.Dropdown(
                        choices=["pieces", "grams", "kg", "ml", "liters", "cups", "tablespoons", "teaspoons"],
                        label="Unit"
                    )
                add_btn = gr.Button("Add Ingredient", variant="primary")
                add_output = gr.Markdown()
                
                # Show current ingredients
                refresh_btn = gr.Button("Refresh Ingredients")
                ingredients_list = gr.Markdown()
                
            with gr.Tab("Get Recipe Suggestions"):
                suggest_btn = gr.Button("Suggest Recipe", variant="primary")
                recipe_output = gr.Markdown()
            
            # Add ingredient event
            add_btn.click(
                fn=self.handle_add_ingredient,
                inputs=[name_input, quantity_input, unit_input],
                outputs=add_output
            ).then(
                fn=self.list_ingredients,
                outputs=ingredients_list
            )
            
            # Refresh ingredients event
            refresh_btn.click(
                fn=self.list_ingredients,
                outputs=ingredients_list
            )
            
            # Get recipe suggestion event
            suggest_btn.click(
                fn=self.handle_get_recipe,
                outputs=recipe_output
            )
            
            # Initialize ingredients list
            ingredients_list.value = self.list_ingredients()
            
        return interface

def main():
    ui = ChefBotUI()
    interface = ui.create_ui()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
