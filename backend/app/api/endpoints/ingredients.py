from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...db.base import get_db
from ...db.models import Ingredient
from ...schemas.ingredient import IngredientCreate, IngredientUpdate, Ingredient as IngredientSchema

router = APIRouter()

@router.get("/", response_model=List[IngredientSchema])
def get_ingredients(db: Session = Depends(get_db)):
    """
    Get all ingredients.
    """
    ingredients = db.query(Ingredient).all()
    return ingredients

@router.post("/", response_model=IngredientSchema, status_code=status.HTTP_201_CREATED)
def create_ingredient(ingredient: IngredientCreate, db: Session = Depends(get_db)):
    """
    Create a new ingredient.
    """
    # Check if ingredient with same name already exists
    db_ingredient = db.query(Ingredient).filter(Ingredient.name == ingredient.name).first()
    if db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingredient with name '{ingredient.name}' already exists"
        )
    
    # Create new ingredient
    db_ingredient = Ingredient(
        name=ingredient.name,
        quantity=ingredient.quantity,
        unit=ingredient.unit
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@router.get("/{ingredient_id}", response_model=IngredientSchema)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """
    Get a specific ingredient by ID.
    """
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with ID {ingredient_id} not found"
        )
    return db_ingredient

@router.put("/{ingredient_id}", response_model=IngredientSchema)
def update_ingredient(ingredient_id: int, ingredient: IngredientUpdate, db: Session = Depends(get_db)):
    """
    Update an ingredient.
    """
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with ID {ingredient_id} not found"
        )
    
    # Update ingredient fields if provided
    update_data = ingredient.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ingredient, field, value)
    
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """
    Delete an ingredient.
    """
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with ID {ingredient_id} not found"
        )
    
    db.delete(db_ingredient)
    db.commit()
    return None
