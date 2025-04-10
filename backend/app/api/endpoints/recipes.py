from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from ...db.supabase_client import get_supabase_client
from ...schemas.recipe import RecipeResponse
from ...services.deepseek_service import DeepSeekService
from ...services.auth_service import get_current_user

router = APIRouter()

@router.post("/suggest", response_model=RecipeResponse)
async def suggest_recipe(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Suggest a recipe based on available ingredients.
    """
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get all ingredients from the database for the current user
    response = supabase.table("ingredients").select("name").eq("user_id", current_user["id"]).execute()
    ingredients = response.data
    
    if not ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ingredients available. Please add ingredients first."
        )
    
    # Extract ingredient names for recipe suggestion
    ingredient_names = [ingredient["name"] for ingredient in ingredients]
    
    try:
        # Get servings from request body or use default
        servings = request.get('servings', 2)
        # Ensure servings is an integer between 1 and 10
        servings = max(1, min(10, int(servings)))
        
        # Initialize DeepSeek service
        deepseek_service = DeepSeekService()
        
        # Create the prompt
        prompt = deepseek_service._create_recipe_prompt(ingredient_names, servings)
        
        # Call the API
        api_response = await deepseek_service._call_deepseek_api(prompt)
        
        # Parse the response
        recipe_data = deepseek_service._parse_recipe_response(api_response)
        recipe_data["servings"] = servings
        
        return recipe_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest recipe: {str(e)}"
        )
