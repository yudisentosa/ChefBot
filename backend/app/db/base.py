from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chef_bot.db")

# Log database connection (without credentials)
db_log_url = DATABASE_URL.replace(":" + DATABASE_URL.split(":")[2].split("@")[0] + "@", ":***@") if "@" in DATABASE_URL else DATABASE_URL
logger.info(f"Connecting to database: {db_log_url}")

# Configure SQLAlchemy engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine with appropriate settings for Cloud SQL
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=5,  # Recommended for Cloud SQL
    max_overflow=2,
    pool_timeout=30,  # 30 seconds
    pool_recycle=1800,  # 30 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
