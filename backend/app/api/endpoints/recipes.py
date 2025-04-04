from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.base import get_db
from ...db.models import Ingredient
from ...schemas.recipe import RecipeResponse
from ...services.deepseek_service import DeepSeekService

router = APIRouter()

@router.post("/suggest", response_model=RecipeResponse)
async def suggest_recipe(
    servings: int = Query(2, ge=1, le=10, description="Number of servings"),
    db: Session = Depends(get_db)
):
    """
    Suggest a recipe based on available ingredients.
    """
    # Get all ingredients from the database
    ingredients = db.query(Ingredient).all()
    
    if not ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ingredients available. Please add ingredients first."
        )
    
    # Extract ingredient names for recipe suggestion
    ingredient_names = [ingredient.name for ingredient in ingredients]
    
    try:
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
