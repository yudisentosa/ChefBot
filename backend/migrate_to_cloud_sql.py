"""
Migration script to transfer data from SQLite to PostgreSQL.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table, select, insert
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Source (SQLite) database URL
SQLITE_URL = "sqlite:///./chef_bot.db"

# Target (PostgreSQL) database URL - use the one from your .env file
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrate_data():
    """Migrate data from SQLite to PostgreSQL."""
    if not POSTGRES_URL:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
        
    logger.info(f"Migrating from SQLite to PostgreSQL: {POSTGRES_URL}")
    
    # Create engine for SQLite (source)
    sqlite_engine = create_engine(SQLITE_URL)
    sqlite_metadata = MetaData()
    sqlite_metadata.reflect(bind=sqlite_engine)
    
    # Create engine for PostgreSQL (target)
    postgres_engine = create_engine(POSTGRES_URL)
    postgres_metadata = MetaData()
    postgres_metadata.reflect(bind=postgres_engine)
    
    # Get all tables from SQLite
    tables = sqlite_metadata.sorted_tables
    
    # Migrate each table
    with sqlite_engine.connect() as sqlite_conn, postgres_engine.connect() as postgres_conn:
        for table in tables:
            table_name = table.name
            logger.info(f"Migrating table: {table_name}")
            
            # Get the corresponding table in PostgreSQL
            if table_name not in postgres_metadata.tables:
                logger.warning(f"Table {table_name} does not exist in PostgreSQL. Skipping.")
                continue
                
            postgres_table = postgres_metadata.tables[table_name]
            
            # Get all data from SQLite table
            select_stmt = select(table)
            rows = sqlite_conn.execute(select_stmt).fetchall()
            
            if not rows:
                logger.info(f"Table {table_name} is empty. Skipping.")
                continue
                
            logger.info(f"Found {len(rows)} rows in {table_name}")
            
            # Insert data into PostgreSQL table
            for row in rows:
                # Convert row to dictionary
                row_dict = {column.name: value for column, value in zip(table.columns, row)}
                
                # Insert into PostgreSQL
                try:
                    insert_stmt = insert(postgres_table).values(**row_dict)
                    postgres_conn.execute(insert_stmt)
                except Exception as e:
                    logger.error(f"Error inserting row into {table_name}: {e}")
                    continue
            
            # Commit the transaction
            postgres_conn.commit()
            logger.info(f"Successfully migrated table: {table_name}")
    
    logger.info("Migration completed successfully")

if __name__ == "__main__":
    migrate_data()
