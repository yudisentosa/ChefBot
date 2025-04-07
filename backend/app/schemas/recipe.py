from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

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


class SavedRecipeBase(RecipeBase):
    notes: Optional[str] = Field(None, description="User notes about the recipe")


class SavedRecipeCreate(SavedRecipeBase):
    pass


class SavedRecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    ingredients_required: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    cooking_time: Optional[str] = None
    servings: Optional[int] = None
    notes: Optional[str] = None


class SavedRecipeInDB(SavedRecipeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SavedRecipeResponse(SavedRecipeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
