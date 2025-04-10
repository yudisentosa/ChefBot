"""
Test connection to Google Cloud SQL.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    """Test connection to the database."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
        
    # Mask password in logs
    db_log_url = DATABASE_URL.replace(":" + DATABASE_URL.split(":")[2].split("@")[0] + "@", ":***@") if "@" in DATABASE_URL else DATABASE_URL
    logger.info(f"Testing connection to: {db_log_url}")
    
    try:
        # Create engine
        engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Connection successful: {result.scalar()}")
            
            # Get database version
            version = connection.execute(text("SELECT version()")).scalar()
            logger.info(f"Database version: {version}")
            
        logger.info("Connection test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
