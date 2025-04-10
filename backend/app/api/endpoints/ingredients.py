from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from typing import List, Optional, Dict, Any
import uuid
import logging
import datetime
from pydantic import BaseModel

from ...db.supabase_client import get_supabase_client
from ...services.auth_service import AuthService
from ..dependencies import get_current_user_dependency
from ...schemas.ingredient import IngredientCreate, IngredientUpdate, Ingredient as IngredientSchema

class LocalIngredient(BaseModel):
    name: str
    quantity: float
    unit: str
    temp_id: Optional[str] = None

class SyncIngredientsRequest(BaseModel):
    ingredients: List[LocalIngredient]

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[IngredientSchema])
async def get_ingredients(request: Request, current_user: Dict[str, Any] = Depends(get_current_user_dependency(use_cache=True))):
    """
    Get all ingredients for the current user.
    If user is not logged in, returns an empty list (client should use local cache).
    """
    # Log the request headers to debug authentication issues
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # If no current_user, return empty list (client will use local cache)
    if not current_user:
        logger.info("No authenticated user, returning empty list (client should use local cache)")
        return []
    
    logger.info(f"Current user in get_ingredients: {current_user['id']}")
    supabase = get_supabase_client()
    
    try:
        # Get user ID from the current user
        user_id = current_user.get("id")
        logger.info(f"Querying ingredients for user_id: {user_id}")
        
        # Query ingredients for this user
        response = supabase.table("ingredients").select("*").eq("user_id", user_id).execute()
        logger.info(f"Found {len(response.data) if response.data else 0} ingredients")
        
        if response.data:
            return response.data
        return []  # Return empty list if no ingredients found
    except Exception as e:
        logger.error(f"Error in get_ingredients: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ingredients: {str(e)}"
        )

@router.post("/", response_model=IngredientSchema, status_code=status.HTTP_201_CREATED)
async def create_ingredient(ingredient: IngredientCreate, current_user: Dict[str, Any] = Depends(get_current_user_dependency(use_cache=True))):
    """
    Create a new ingredient for the current user.
    If user is logged in, insert directly into Supabase.
    If user is not logged in, return a temporary ingredient for client-side caching.
    """
    # If no current_user, return a mock response for client-side caching
    if not current_user:
        logger.info("No authenticated user, returning mock ingredient for client-side caching")
        # Generate a temporary ID for client-side caching
        # The client should store this locally and replace it when syncing
        temp_id = f"temp_{uuid.uuid4()}"
        
        # Create a valid Ingredient object that matches our schema
        return IngredientSchema(
            id=temp_id,
            name=ingredient.name,
            quantity=ingredient.quantity,
            unit=ingredient.unit,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            user_id=None  # No user ID yet
        )
    
    # If user is logged in, insert directly into Supabase
    logger.info(f"Authenticated user {current_user['id']}, inserting ingredient directly into Supabase")
    
    supabase = get_supabase_client()
    
    try:
        # Get user ID from the current user
        user_id = current_user.get("id")
        
        # Check if ingredient with same name already exists for this user
        response = supabase.table("ingredients").select("*").eq("name", ingredient.name).eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ingredient with name '{ingredient.name}' already exists"
            )
        
        # Create new ingredient with user_id
        new_ingredient = {
            "name": ingredient.name,
            "quantity": ingredient.quantity,
            "unit": ingredient.unit,
            "user_id": user_id
        }
        
        response = supabase.table("ingredients").insert(new_ingredient).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create ingredient"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ingredient: {str(e)}"
        )

@router.get("/{ingredient_id}", response_model=IngredientSchema)
async def get_ingredient(ingredient_id: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency())):
    """
    Get a specific ingredient by ID for the current user.
    """
    supabase = get_supabase_client()
    
    try:
        # Get user ID from the current user
        user_id = current_user.get("id")
        
        # Query ingredient by ID and user_id
        response = supabase.table("ingredients").select("*").eq("id", ingredient_id).eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ingredient: {str(e)}"
        )

@router.put("/{ingredient_id}", response_model=IngredientSchema)
async def update_ingredient(ingredient_id: str, ingredient: IngredientUpdate, current_user: Dict[str, Any] = Depends(get_current_user_dependency())):
    """
    Update an ingredient for the current user.
    """
    supabase = get_supabase_client()
    
    try:
        # Get user ID from the current user
        user_id = current_user.get("id")
        
        # Check if ingredient exists and belongs to the user
        response = supabase.table("ingredients").select("*").eq("id", ingredient_id).eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        
        # Update ingredient fields if provided
        update_data = ingredient.dict(exclude_unset=True)
        
        response = supabase.table("ingredients").update(update_data).eq("id", ingredient_id).eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update ingredient"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ingredient: {str(e)}"
        )

@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(ingredient_id: str, current_user: Dict[str, Any] = Depends(get_current_user_dependency())):
    """
    Delete an ingredient for the current user.
    """
    supabase = get_supabase_client()
    
    try:
        # Get user ID from the current user
        user_id = current_user.get("id")
        
        # Check if ingredient exists and belongs to the user
        response = supabase.table("ingredients").select("*").eq("id", ingredient_id).eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        
        # Delete the ingredient
        response = supabase.table("ingredients").delete().eq("id", ingredient_id).eq("user_id", user_id).execute()
        
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ingredient: {str(e)}"
        )


@router.post("/sync", response_model=List[IngredientSchema])
async def sync_ingredients(
    sync_data: SyncIngredientsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_dependency())
):
    """
    Sync local ingredients with Supabase after login.
    This endpoint is used when a user logs in and wants to upload their locally cached ingredients.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in to sync ingredients",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    supabase = get_supabase_client()
    user_id = current_user.get("id")
    logger.info(f"Syncing {len(sync_data.ingredients)} ingredients for user {user_id}")
    
    # Get existing ingredients for this user to avoid duplicates
    existing_response = supabase.table("ingredients").select("name").eq("user_id", user_id).execute()
    existing_names = [item["name"].lower() for item in existing_response.data] if existing_response.data else []
    
    # Filter out ingredients that already exist (case-insensitive comparison)
    new_ingredients = []
    for ingredient in sync_data.ingredients:
        if ingredient.name.lower() not in existing_names:
            new_ingredients.append({
                "name": ingredient.name,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit,
                "user_id": user_id
            })
    
    if not new_ingredients:
        logger.info("No new ingredients to sync")
        # Return all existing ingredients
        response = supabase.table("ingredients").select("*").eq("user_id", user_id).execute()
        return response.data if response.data else []
    
    try:
        # Insert all new ingredients in a single operation
        logger.info(f"Inserting {len(new_ingredients)} new ingredients")
        response = supabase.table("ingredients").insert(new_ingredients).execute()
        
        if not response.data:
            logger.error("Failed to insert new ingredients")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync ingredients"
            )
        
        # Return all ingredients for this user (including both existing and newly added)
        all_response = supabase.table("ingredients").select("*").eq("user_id", user_id).execute()
        return all_response.data if all_response.data else []
    
    except Exception as e:
        logger.error(f"Error syncing ingredients: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync ingredients: {str(e)}"
        )
