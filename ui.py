import gradio as gr
import requests
from typing import Dict, Any, List, Tuple, Optional
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
    
    def _update_ingredient(self, id: int, name: str, quantity: float, unit: str) -> Dict[str, Any]:
        """Update an existing ingredient via the API."""
        data = {
            "name": name,
            "quantity": quantity,
            "unit": unit
        }
        response = requests.put(f"{self.api_base_url}/api/ingredients/{id}", json=data)
        return response.json()
    
    def _delete_ingredient(self, id: int) -> Dict[str, Any]:
        """Delete an ingredient via the API."""
        response = requests.delete(f"{self.api_base_url}/api/ingredients/{id}")
        return response.json()
        
    def _get_recipe_suggestion(self, servings: int = 2) -> Dict[str, Any]:
        """Get recipe suggestions based on available ingredients."""
        response = requests.get(f"{self.api_base_url}/api/suggest-recipe?servings={servings}")
        if response.status_code == 200:
            return response.json()
        return {"error": "Failed to get recipe suggestion"}

    def _format_recipe(self, recipe: Dict[str, Any], servings: int = 2) -> str:
        """Format recipe data into a readable string."""
        if "error" in recipe:
            return f"Error: {recipe['error']}"
            
        return f"""
# {recipe['recipe_name']} (Serves {servings})

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
    
    def handle_update_ingredient(self, ingredient_id: str, name: str, quantity: str, unit: str) -> str:
        """Handle updating an existing ingredient."""
        try:
            if not ingredient_id:
                return "Error: Please select an ingredient to update"
                
            id = int(ingredient_id.split(':')[0].strip())
            quantity = float(quantity) if quantity else 0
            
            if not name:
                return "Error: Ingredient name is required"
                
            result = self._update_ingredient(id, name, quantity, unit)
            if "error" in result:
                return f"Error: {result['error']}"
                
            return f"Successfully updated {name}"
        except ValueError:
            return "Error: Invalid quantity format or ingredient ID"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def handle_delete_ingredient(self, ingredient_id: str) -> str:
        """Handle deleting an ingredient."""
        try:
            if not ingredient_id:
                return "Error: Please select an ingredient to delete"
                
            id = int(ingredient_id.split(':')[0].strip())
            
            result = self._delete_ingredient(id)
            if "error" in result:
                return f"Error: {result['error']}"
                
            return f"Successfully deleted ingredient"
        except ValueError:
            return "Error: Invalid ingredient ID"
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_get_recipe(self, servings: int) -> str:
        """Handle getting recipe suggestions with serving size."""
        try:
            ingredients = self._get_ingredients()
            if not ingredients:
                return "Error: No ingredients available. Please add some ingredients first."
                
            recipe = self._get_recipe_suggestion(servings)
            return self._format_recipe(recipe, servings)
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
    
    def get_ingredient_choices(self) -> List[str]:
        """Get list of ingredients as choices for dropdown."""
        try:
            ingredients = self._get_ingredients()
            return [f"{ing['id']}: {ing['name']} ({ing['quantity']} {ing['unit']})" for ing in ingredients]
        except Exception:
            return []
    
    def load_ingredient_details(self, ingredient_id: str) -> Tuple[str, str, str]:
        """Load ingredient details for editing."""
        try:
            if not ingredient_id:
                return "", "", ""
                
            id = int(ingredient_id.split(':')[0].strip())
            ingredients = self._get_ingredients()
            
            for ing in ingredients:
                if ing['id'] == id:
                    return ing['name'], str(ing['quantity']), ing['unit']
                    
            return "", "", ""
        except Exception:
            return "", "", ""

    def create_ui(self) -> gr.Blocks:
        """Create and configure the Gradio interface."""
        with gr.Blocks(title="Chef Bot", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 👨‍🍳 Chef Bot")
            gr.Markdown("Your AI-powered cooking assistant")
            
            with gr.Tab("Manage Ingredients"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Add New Ingredient")
                        name_input = gr.Textbox(label="Ingredient Name")
                        quantity_input = gr.Textbox(label="Quantity")
                        unit_input = gr.Dropdown(
                            choices=["pieces", "grams", "kg", "ml", "liters", "cups", "tablespoons", "teaspoons"],
                            label="Unit",
                            value="pieces"
                        )
                        add_btn = gr.Button("Add Ingredient", variant="primary")
                        add_output = gr.Markdown()
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### Update Ingredient")
                        ingredient_dropdown = gr.Dropdown(
                            label="Select Ingredient",
                            choices=self.get_ingredient_choices(),
                            interactive=True
                        )
                        update_name_input = gr.Textbox(label="Ingredient Name")
                        update_quantity_input = gr.Textbox(label="Quantity")
                        update_unit_input = gr.Dropdown(
                            choices=["pieces", "grams", "kg", "ml", "liters", "cups", "tablespoons", "teaspoons"],
                            label="Unit",
                            value="pieces"
                        )
                        update_btn = gr.Button("Update Ingredient", variant="primary")
                        update_output = gr.Markdown()
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Delete Ingredient")
                        delete_dropdown = gr.Dropdown(
                            label="Select Ingredient to Delete",
                            choices=self.get_ingredient_choices(),
                            interactive=True
                        )
                        delete_btn = gr.Button("Delete Ingredient", variant="stop")
                        delete_output = gr.Markdown()
                    
                    with gr.Column(scale=1):
                        refresh_btn = gr.Button("Refresh Ingredients")
                        ingredients_list = gr.Markdown()
            
            with gr.Tab("Get Recipe Suggestions"):
                with gr.Row():
                    servings_dropdown = gr.Dropdown(
                        choices=["2", "4", "6", "8"],
                        label="Number of Servings",
                        value="2"
                    )
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
            ).then(
                fn=self.get_ingredient_choices,
                outputs=[ingredient_dropdown, delete_dropdown]
            )
            
            # Update ingredient events
            ingredient_dropdown.change(
                fn=self.load_ingredient_details,
                inputs=[ingredient_dropdown],
                outputs=[update_name_input, update_quantity_input, update_unit_input]
            )
            
            update_btn.click(
                fn=self.handle_update_ingredient,
                inputs=[ingredient_dropdown, update_name_input, update_quantity_input, update_unit_input],
                outputs=update_output
            ).then(
                fn=self.list_ingredients,
                outputs=ingredients_list
            ).then(
                fn=self.get_ingredient_choices,
                outputs=[ingredient_dropdown, delete_dropdown]
            )
            
            # Delete ingredient event
            delete_btn.click(
                fn=self.handle_delete_ingredient,
                inputs=[delete_dropdown],
                outputs=delete_output
            ).then(
                fn=self.list_ingredients,
                outputs=ingredients_list
            ).then(
                fn=self.get_ingredient_choices,
                outputs=[ingredient_dropdown, delete_dropdown]
            )
            
            # Refresh ingredients event
            refresh_btn.click(
                fn=self.list_ingredients,
                outputs=ingredients_list
            ).then(
                fn=self.get_ingredient_choices,
                outputs=[ingredient_dropdown, delete_dropdown]
            )
            
            # Get recipe suggestion event
            suggest_btn.click(
                fn=self.handle_get_recipe,
                inputs=[servings_dropdown],
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
        server_port=7861,  
        share=True,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
