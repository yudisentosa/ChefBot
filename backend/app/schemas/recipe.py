from pydantic import BaseModel, Field
from typing import List, Optional

class RecipeBase(BaseModel):
    recipe_name: str = Field(..., description="Name of the recipe")
    ingredients_required: List[str] = Field(..., description="List of ingredients with quantities required for the recipe")
    missing_ingredients: List[str] = Field(default=[], description="List of ingredients that are missing")
    instructions: List[str] = Field(..., description="Step-by-step cooking instructions")
    difficulty_level: str = Field("medium", description="Difficulty level of the recipe")
    cooking_time: str = Field(..., description="Estimated cooking time in minutes")
    servings: int = Field(2, description="Number of servings this recipe makes")

class RecipeResponse(RecipeBase):
    pass
