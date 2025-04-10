"""
Test Supabase connection for Chef Bot application.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from app.db.supabase_client import get_supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test connection to Supabase."""
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        logger.info("Successfully initialized Supabase client")
        
        # Test a simple query
        response = supabase.table('users').select("*").limit(1).execute()
        
        # Check if the query was successful
        if hasattr(response, 'data'):
            if response.data:
                logger.info(f"Successfully queried users table. Found {len(response.data)} user(s).")
            else:
                logger.info("Successfully queried users table. No users found.")
        else:
            logger.warning("Query executed but returned unexpected structure")
            
        logger.info("Supabase connection test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
        logger.error("SUPABASE_URL or SUPABASE_KEY environment variables are not set")
        logger.info("Please set these variables in your .env file or environment")
        sys.exit(1)
        
    success = test_supabase_connection()
    if success:
        logger.info("✅ Supabase connection test passed!")
        sys.exit(0)
    else:
        logger.error("❌ Supabase connection test failed!")
        sys.exit(1)
