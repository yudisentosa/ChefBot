from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Base Ingredient Schema (shared properties)
class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the ingredient")
    quantity: float = Field(1.0, gt=0, description="Quantity of the ingredient")
    unit: str = Field("pieces", min_length=1, max_length=50, description="Unit of measurement")

# Schema for creating a new ingredient
class IngredientCreate(IngredientBase):
    pass

# Schema for updating an ingredient
class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the ingredient")
    quantity: Optional[float] = Field(None, gt=0, description="Quantity of the ingredient")
    unit: Optional[str] = Field(None, min_length=1, max_length=50, description="Unit of measurement")

# Schema for ingredient in response
class Ingredient(IngredientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility
