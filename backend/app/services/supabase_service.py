"""
Supabase service for Chef Bot application.
This service provides methods to interact with Supabase tables.
"""
import logging
from typing import Dict, List, Any, Optional
from app.db.supabase_client import get_supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase database."""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email.
        
        Args:
            email: User's email address
            
        Returns:
            User data or None if not found
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('users').select("*").eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    @staticmethod
    def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by Google ID.
        
        Args:
            google_id: User's Google ID
            
        Returns:
            User data or None if not found
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('users').select("*").eq('google_id', google_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by Google ID: {str(e)}")
            return None
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new user.
        
        Args:
            user_data: User data to insert
            
        Returns:
            Created user data or None if failed
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('users').insert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    @staticmethod
    def get_ingredients_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all ingredients for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of ingredients
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('ingredients').select("*").eq('user_id', user_id).execute()
            
            if response.data:
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error getting ingredients: {str(e)}")
            return []
    
    @staticmethod
    def add_ingredient(ingredient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new ingredient.
        
        Args:
            ingredient_data: Ingredient data to insert
            
        Returns:
            Created ingredient data or None if failed
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('ingredients').insert(ingredient_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error adding ingredient: {str(e)}")
            return None
    
    @staticmethod
    def update_ingredient(ingredient_id: int, ingredient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an ingredient.
        
        Args:
            ingredient_id: Ingredient ID
            ingredient_data: Updated ingredient data
            
        Returns:
            Updated ingredient data or None if failed
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('ingredients').update(ingredient_data).eq('id', ingredient_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating ingredient: {str(e)}")
            return None
    
    @staticmethod
    def delete_ingredient(ingredient_id: int) -> bool:
        """
        Delete an ingredient.
        
        Args:
            ingredient_id: Ingredient ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('ingredients').delete().eq('id', ingredient_id).execute()
            
            return response.data is not None
        except Exception as e:
            logger.error(f"Error deleting ingredient: {str(e)}")
            return False
    
    @staticmethod
    def get_saved_recipes_by_user_id(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all saved recipes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of saved recipes
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('saved_recipes').select("*").eq('user_id', user_id).execute()
            
            if response.data:
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error getting saved recipes: {str(e)}")
            return []
    
    @staticmethod
    def save_recipe(recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save a recipe.
        
        Args:
            recipe_data: Recipe data to insert
            
        Returns:
            Saved recipe data or None if failed
        """
        try:
            supabase = get_supabase_client()
            response = supabase.table('saved_recipes').insert(recipe_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error saving recipe: {str(e)}")
            return None
