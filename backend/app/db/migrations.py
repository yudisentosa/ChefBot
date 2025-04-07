import logging
import sqlalchemy as sa
from sqlalchemy import inspect
from .base import engine

logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations."""
    try:
        inspector = inspect(engine)
        
        # Migration 1: Check if user_id column exists in ingredients table
        if 'ingredients' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('ingredients')]
            if 'user_id' not in columns:
                # Add user_id column to ingredients table
                logger.info("Adding user_id column to ingredients table")
                with engine.connect() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE ingredients ADD COLUMN user_id INTEGER REFERENCES users(id)"
                    ))
                    conn.commit()
                logger.info("Migration completed successfully")
            else:
                logger.info("user_id column already exists in ingredients table")
        
        # Migration 2: Check if missing_ingredients column exists in saved_recipes table
        if 'saved_recipes' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('saved_recipes')]
            if 'missing_ingredients' not in columns:
                # Add missing_ingredients column to saved_recipes table
                logger.info("Adding missing_ingredients column to saved_recipes table")
                with engine.connect() as conn:
                    conn.execute(sa.text(
                        "ALTER TABLE saved_recipes ADD COLUMN missing_ingredients JSON DEFAULT '[]'"
                    ))
                    conn.commit()
                logger.info("Migration for saved_recipes completed successfully")
            else:
                logger.info("missing_ingredients column already exists in saved_recipes table")

    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise
