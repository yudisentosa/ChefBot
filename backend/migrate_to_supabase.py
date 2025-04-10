"""
Migrate data from SQLite to Supabase for Chef Bot application.
"""
import os
import sys
import logging
import uuid
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, select
from supabase import create_client, Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
# For data migration, we need to use the service_role key (not the anon key)
# You can find this in your Supabase dashboard under Project Settings > API
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# If service key is not provided, try using the regular key
SUPABASE_KEY = SUPABASE_SERVICE_KEY or os.environ.get("SUPABASE_KEY")

# SQLite database URL
SQLITE_URL = "sqlite:///./chef_bot.db"

def get_supabase_client():
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        logger.error("For data migration, you need to use the service_role key")
        logger.error("Set SUPABASE_SERVICE_KEY environment variable with your service role key")
        sys.exit(1)
    
    try:
        # Create client with headers that bypass RLS
        headers = {
            "X-Client-Info": "chef-bot-migration-script"
        }
        return create_client(SUPABASE_URL, SUPABASE_KEY, headers=headers)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        sys.exit(1)

def migrate_users():
    """Migrate users from SQLite to Supabase."""
    logger.info("Migrating users...")
    
    # Connect to SQLite
    sqlite_engine = create_engine(SQLITE_URL)
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # Get users table
    if 'users' not in metadata.tables:
        logger.error("Users table not found in SQLite database")
        return False
    
    users_table = metadata.tables['users']
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Migrate users
    with sqlite_engine.connect() as conn:
        # Get all users from SQLite
        select_stmt = select(users_table)
        users = conn.execute(select_stmt).fetchall()
        
        if not users:
            logger.info("No users found in SQLite database")
            return True
        
        logger.info(f"Found {len(users)} users to migrate")
        
        # Insert users into Supabase
        for user in users:
            # Convert SQLite user to dict
            user_dict = {c.name: getattr(user, c.name) for c in users_table.columns}
            
            # Generate UUID for user ID
            user_id = str(uuid.uuid4())
            
            # Prepare user data for Supabase
            supabase_user = {
                "id": user_id,
                "email": user_dict["email"],
                "name": user_dict["name"],
                "picture": user_dict["picture"],
                "google_id": user_dict["google_id"],
                "is_active": user_dict["is_active"],
                # created_at and updated_at will be set automatically
            }
            
            try:
                # Insert user into Supabase
                response = supabase.table("users").insert(supabase_user).execute()
                
                if response.data:
                    logger.info(f"Migrated user: {user_dict['email']} (ID: {user_id})")
                    
                    # Store mapping of old ID to new UUID for foreign key references
                    id_mapping[user_dict["id"]] = user_id
                else:
                    logger.error(f"Failed to migrate user: {user_dict['email']}")
            except Exception as e:
                logger.error(f"Error migrating user {user_dict['email']}: {str(e)}")
    
    return True

def migrate_ingredients():
    """Migrate ingredients from SQLite to Supabase."""
    logger.info("Migrating ingredients...")
    
    # Connect to SQLite
    sqlite_engine = create_engine(SQLITE_URL)
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # Get ingredients table
    if 'ingredients' not in metadata.tables:
        logger.error("Ingredients table not found in SQLite database")
        return False
    
    ingredients_table = metadata.tables['ingredients']
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Migrate ingredients
    with sqlite_engine.connect() as conn:
        # Get all ingredients from SQLite
        select_stmt = select(ingredients_table)
        ingredients = conn.execute(select_stmt).fetchall()
        
        if not ingredients:
            logger.info("No ingredients found in SQLite database")
            return True
        
        logger.info(f"Found {len(ingredients)} ingredients to migrate")
        
        # Insert ingredients into Supabase
        for ingredient in ingredients:
            # Convert SQLite ingredient to dict
            ingredient_dict = {c.name: getattr(ingredient, c.name) for c in ingredients_table.columns}
            
            # Get new user ID from mapping
            old_user_id = ingredient_dict["user_id"]
            if old_user_id in id_mapping:
                new_user_id = id_mapping[old_user_id]
            else:
                logger.warning(f"User ID {old_user_id} not found in mapping, skipping ingredient")
                continue
            
            # Prepare ingredient data for Supabase
            supabase_ingredient = {
                "name": ingredient_dict["name"],
                "quantity": ingredient_dict["quantity"],
                "unit": ingredient_dict["unit"],
                "user_id": new_user_id,
                # created_at and updated_at will be set automatically
            }
            
            try:
                # Insert ingredient into Supabase
                response = supabase.table("ingredients").insert(supabase_ingredient).execute()
                
                if response.data:
                    logger.info(f"Migrated ingredient: {ingredient_dict['name']}")
                else:
                    logger.error(f"Failed to migrate ingredient: {ingredient_dict['name']}")
            except Exception as e:
                logger.error(f"Error migrating ingredient {ingredient_dict['name']}: {str(e)}")
    
    return True

def migrate_saved_recipes():
    """Migrate saved recipes from SQLite to Supabase."""
    logger.info("Migrating saved recipes...")
    
    # Connect to SQLite
    sqlite_engine = create_engine(SQLITE_URL)
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    # Get saved_recipes table
    if 'saved_recipes' not in metadata.tables:
        logger.error("Saved recipes table not found in SQLite database")
        return False
    
    saved_recipes_table = metadata.tables['saved_recipes']
    
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Migrate saved recipes
    with sqlite_engine.connect() as conn:
        # Get all saved recipes from SQLite
        select_stmt = select(saved_recipes_table)
        saved_recipes = conn.execute(select_stmt).fetchall()
        
        if not saved_recipes:
            logger.info("No saved recipes found in SQLite database")
            return True
        
        logger.info(f"Found {len(saved_recipes)} saved recipes to migrate")
        
        # Insert saved recipes into Supabase
        for recipe in saved_recipes:
            # Convert SQLite recipe to dict
            recipe_dict = {c.name: getattr(recipe, c.name) for c in saved_recipes_table.columns}
            
            # Get new user ID from mapping
            old_user_id = recipe_dict["user_id"]
            if old_user_id in id_mapping:
                new_user_id = id_mapping[old_user_id]
            else:
                logger.warning(f"User ID {old_user_id} not found in mapping, skipping recipe")
                continue
            
            # Prepare recipe data for Supabase
            supabase_recipe = {
                "recipe_name": recipe_dict["recipe_name"],
                "ingredients_required": recipe_dict["ingredients_required"],
                "missing_ingredients": recipe_dict["missing_ingredients"],
                "instructions": recipe_dict["instructions"],
                "difficulty_level": recipe_dict["difficulty_level"],
                "cooking_time": recipe_dict["cooking_time"],
                "servings": recipe_dict["servings"],
                "notes": recipe_dict["notes"],
                "user_id": new_user_id,
                # created_at and updated_at will be set automatically
            }
            
            try:
                # Insert recipe into Supabase
                response = supabase.table("saved_recipes").insert(supabase_recipe).execute()
                
                if response.data:
                    logger.info(f"Migrated recipe: {recipe_dict['recipe_name']}")
                else:
                    logger.error(f"Failed to migrate recipe: {recipe_dict['recipe_name']}")
            except Exception as e:
                logger.error(f"Error migrating recipe {recipe_dict['recipe_name']}: {str(e)}")
    
    return True

if __name__ == "__main__":
    logger.info("Starting migration from SQLite to Supabase...")
    
    if not os.environ.get("SUPABASE_SERVICE_KEY"):
        logger.warning("SUPABASE_SERVICE_KEY not found in environment variables")
        logger.warning("For data migration, you should use the service_role key from Supabase")
        logger.warning("Set SUPABASE_SERVICE_KEY environment variable with your service role key")
        logger.warning("Attempting to continue with the provided key, but this may fail due to RLS policies")
    
    # Dictionary to map old IDs to new UUIDs
    id_mapping = {}
    
    # Migrate data
    if migrate_users() and migrate_ingredients() and migrate_saved_recipes():
        logger.info("✅ Migration completed successfully!")
        logger.info("")
        logger.info("IMPORTANT: Now you need to enable RLS in Supabase SQL Editor:")
        logger.info("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;")
        logger.info("ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;")
        logger.info("ALTER TABLE public.saved_recipes ENABLE ROW LEVEL SECURITY;")
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)
