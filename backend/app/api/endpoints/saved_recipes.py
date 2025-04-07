from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List, Any

from ...db.base import get_db
from ...db.models import SavedRecipe, User
from ...schemas.recipe import SavedRecipeCreate, SavedRecipeResponse, SavedRecipeUpdate
from ...services.auth_service import AuthService

router = APIRouter()

@router.post("", response_model=SavedRecipeResponse)
async def create_saved_recipe(
    recipe: SavedRecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Save a recipe to the user's collection.
    """
    # Create new saved recipe
    db_recipe = SavedRecipe(
        recipe_name=recipe.recipe_name,
        ingredients_required=recipe.ingredients_required,
        missing_ingredients=recipe.missing_ingredients,
        instructions=recipe.instructions,
        difficulty_level=recipe.difficulty_level,
        cooking_time=recipe.cooking_time,
        servings=recipe.servings,
        notes=recipe.notes,
        user_id=current_user.id
    )
    
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    
    return db_recipe


@router.get("", response_model=List[SavedRecipeResponse])
async def get_saved_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Get all saved recipes for the current user.
    """
    recipes = db.query(SavedRecipe).filter(
        SavedRecipe.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return recipes


@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_saved_recipe(
    recipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Get a specific saved recipe by ID.
    """
    recipe = db.query(SavedRecipe).filter(
        SavedRecipe.id == recipe_id,
        SavedRecipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return recipe


@router.put("/{recipe_id}", response_model=SavedRecipeResponse)
async def update_saved_recipe(
    recipe_update: SavedRecipeUpdate,
    recipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Update a saved recipe.
    """
    recipe = db.query(SavedRecipe).filter(
        SavedRecipe.id == recipe_id,
        SavedRecipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Update recipe fields
    update_data = recipe_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recipe, key, value)
    
    db.commit()
    db.refresh(recipe)
    
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_recipe(
    recipe_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> None:
    """
    Delete a saved recipe.
    """
    recipe = db.query(SavedRecipe).filter(
        SavedRecipe.id == recipe_id,
        SavedRecipe.user_id == current_user.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    db.delete(recipe)
    db.commit()
