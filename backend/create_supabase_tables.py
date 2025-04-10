"""
Create Supabase tables for Chef Bot application.
This script creates all the necessary tables in your Supabase project.
"""
import os
import sys
import logging
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    logger.error("Make sure to set these variables before running this script")
    sys.exit(1)

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info(f"Supabase client initialized with URL: {SUPABASE_URL[:20]}...")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    sys.exit(1)

def create_users_table():
    """Create users table in Supabase."""
    logger.info("Creating users table...")
    
    # SQL for creating users table
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        picture VARCHAR(255),
        google_id VARCHAR(255) UNIQUE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create index on email and google_id
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
    """
    
    try:
        # Execute SQL
        supabase.table("users").select("*").limit(1).execute()
        logger.info("Users table already exists")
    except Exception:
        try:
            # Table doesn't exist, create it
            response = supabase.rpc("exec_sql", {"query": sql}).execute()
            logger.info("Users table created successfully")
        except Exception as e:
            logger.error(f"Error creating users table: {str(e)}")
            return False
    
    return True

def create_ingredients_table():
    """Create ingredients table in Supabase."""
    logger.info("Creating ingredients table...")
    
    # SQL for creating ingredients table
    sql = """
    CREATE TABLE IF NOT EXISTS ingredients (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        quantity FLOAT DEFAULT 1.0,
        unit VARCHAR(50) DEFAULT 'pieces',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE
    );
    
    -- Create index on user_id
    CREATE INDEX IF NOT EXISTS idx_ingredients_user_id ON ingredients(user_id);
    """
    
    try:
        # Execute SQL
        supabase.table("ingredients").select("*").limit(1).execute()
        logger.info("Ingredients table already exists")
    except Exception:
        try:
            # Table doesn't exist, create it
            response = supabase.rpc("exec_sql", {"query": sql}).execute()
            logger.info("Ingredients table created successfully")
        except Exception as e:
            logger.error(f"Error creating ingredients table: {str(e)}")
            return False
    
    return True

def create_saved_recipes_table():
    """Create saved_recipes table in Supabase."""
    logger.info("Creating saved_recipes table...")
    
    # SQL for creating saved_recipes table
    sql = """
    CREATE TABLE IF NOT EXISTS saved_recipes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        recipe_name VARCHAR(255) NOT NULL,
        ingredients_required JSONB NOT NULL,
        missing_ingredients JSONB DEFAULT '[]'::JSONB,
        instructions JSONB NOT NULL,
        difficulty_level VARCHAR(50),
        cooking_time VARCHAR(50),
        servings INTEGER DEFAULT 2,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE
    );
    
    -- Create index on user_id
    CREATE INDEX IF NOT EXISTS idx_saved_recipes_user_id ON saved_recipes(user_id);
    """
    
    try:
        # Execute SQL
        supabase.table("saved_recipes").select("*").limit(1).execute()
        logger.info("Saved recipes table already exists")
    except Exception:
        try:
            # Table doesn't exist, create it
            response = supabase.rpc("exec_sql", {"query": sql}).execute()
            logger.info("Saved recipes table created successfully")
        except Exception as e:
            logger.error(f"Error creating saved_recipes table: {str(e)}")
            return False
    
    return True

def create_rpc_functions():
    """Create RPC functions in Supabase."""
    logger.info("Creating RPC functions...")
    
    # SQL for creating exec_sql function
    sql = """
    CREATE OR REPLACE FUNCTION exec_sql(query TEXT)
    RETURNS VOID AS $$
    BEGIN
        EXECUTE query;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    try:
        # Execute SQL to create the function
        response = supabase.rpc("exec_sql", {"query": "SELECT 1"}).execute()
        logger.info("RPC functions already exist")
    except Exception:
        try:
            # Function doesn't exist, create it
            # We need to use the REST API directly for this
            url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            import httpx
            response = httpx.post(
                url,
                headers=headers,
                json={"query": sql}
            )
            if response.status_code == 200:
                logger.info("RPC functions created successfully")
            else:
                logger.warning(f"RPC function creation returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error creating RPC functions: {str(e)}")
            return False
    
    return True

def main():
    """Main function to create all tables."""
    logger.info("Starting Supabase table creation...")
    
    # Create RPC functions first
    if not create_rpc_functions():
        logger.error("Failed to create RPC functions. Exiting.")
        sys.exit(1)
    
    # Wait a bit for the function to be available
    time.sleep(2)
    
    # Create tables
    tables_created = (
        create_users_table() and
        create_ingredients_table() and
        create_saved_recipes_table()
    )
    
    if tables_created:
        logger.info("✅ All tables created successfully!")
    else:
        logger.error("❌ Failed to create some tables.")
        sys.exit(1)

if __name__ == "__main__":
    main()
