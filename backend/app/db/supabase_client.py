"""
Supabase client for Chef Bot application.
This module provides a Supabase client instance for database operations.
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    logger.warning("Make sure to set these variables for Supabase connection")

# Create Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info(f"Supabase client initialized with URL: {SUPABASE_URL[:20]}...")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    supabase = None

def get_supabase_client() -> Client:
    """
    Returns the Supabase client instance.
    Use this function to get access to the Supabase client throughout the application.
    
    Returns:
        Client: Supabase client instance
    """
    if not supabase:
        raise ValueError("Supabase client not initialized. Check your SUPABASE_URL and SUPABASE_KEY.")
    return supabase
