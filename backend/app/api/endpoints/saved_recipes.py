from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import List, Any, Dict
import uuid

from ...db.supabase_client import get_supabase_client
from ...schemas.recipe import SavedRecipeCreate, SavedRecipeResponse, SavedRecipeUpdate
from ...services.auth_service import get_current_user

router = APIRouter()

@router.post("", response_model=SavedRecipeResponse)
async def create_saved_recipe(
    recipe: SavedRecipeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Save a recipe to the user's collection.
    """
    supabase = get_supabase_client()
    
    # Create new saved recipe
    recipe_data = {
        "id": str(uuid.uuid4()),
        "recipe_name": recipe.recipe_name,
        "ingredients_required": recipe.ingredients_required,
        "missing_ingredients": recipe.missing_ingredients,
        "instructions": recipe.instructions,
        "difficulty_level": recipe.difficulty_level,
        "cooking_time": recipe.cooking_time,
        "servings": recipe.servings,
        "notes": recipe.notes,
        "user_id": current_user["id"]
    }
    
    response = supabase.table("saved_recipes").insert(recipe_data).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save recipe"
        )


@router.get("", response_model=List[SavedRecipeResponse])
async def get_saved_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get all saved recipes for the current user.
    """
    supabase = get_supabase_client()
    
    response = supabase.table("saved_recipes") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .range(skip, skip + limit - 1) \
        .execute()
    
    return response.data


@router.get("/{recipe_id}", response_model=SavedRecipeResponse)
async def get_saved_recipe(
    recipe_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a specific saved recipe by ID.
    """
    supabase = get_supabase_client()
    
    response = supabase.table("saved_recipes") \
        .select("*") \
        .eq("id", recipe_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    return response.data[0]


@router.put("/{recipe_id}", response_model=SavedRecipeResponse)
async def update_saved_recipe(
    recipe_update: SavedRecipeUpdate,
    recipe_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a saved recipe.
    """
    supabase = get_supabase_client()
    
    # First check if the recipe exists and belongs to the user
    check_response = supabase.table("saved_recipes") \
        .select("id") \
        .eq("id", recipe_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not check_response.data or len(check_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Update recipe fields
    update_data = recipe_update.dict(exclude_unset=True)
    
    response = supabase.table("saved_recipes") \
        .update(update_data) \
        .eq("id", recipe_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update recipe"
        )
    
    return response.data[0]


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_recipe(
    recipe_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    Delete a saved recipe.
    """
    supabase = get_supabase_client()
    
    # First check if the recipe exists and belongs to the user
    check_response = supabase.table("saved_recipes") \
        .select("id") \
        .eq("id", recipe_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not check_response.data or len(check_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found"
        )
    
    # Delete the recipe
    supabase.table("saved_recipes") \
        .delete() \
        .eq("id", recipe_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
