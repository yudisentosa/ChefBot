"""
Chef Bot main application with Supabase integration.
This version uses Supabase instead of SQLite for database operations.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import logging
import os

from app.core.config import settings
from app.api.endpoints import ingredients, recipes, auth, saved_recipes
from app.db.supabase_client import get_supabase_client, supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Verify Supabase connection
try:
    supabase_client = get_supabase_client()
    logger.info("Successfully connected to Supabase")
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {str(e)}")
    logger.error("Make sure SUPABASE_URL and SUPABASE_KEY are set in your environment")
    raise

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
# Note: You'll need to update your endpoint implementations to use Supabase
app.include_router(
    ingredients.router,
    prefix=f"{settings.API_V1_STR}/ingredients",
    tags=["ingredients"],
)
app.include_router(
    recipes.router,
    prefix=f"{settings.API_V1_STR}/recipes",
    tags=["recipes"],
)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"],
)
app.include_router(
    saved_recipes.router,
    prefix=f"{settings.API_V1_STR}/saved-recipes",
    tags=["saved-recipes"],
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    """Redirect to the static HTML UI."""
    return RedirectResponse(url="/static/simple.html")

@app.get("/api")
def api_info():
    """API information endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "AI-powered cooking assistant that suggests recipes based on available ingredients",
        "database": "Supabase",
        "endpoints": {
            "/api/v1/ingredients": "Ingredient management endpoints",
            "/api/v1/recipes/suggest": "Recipe suggestion endpoint",
            "/api/v1/auth": "Authentication endpoints",
            "/api/v1/saved-recipes": "Saved recipes management endpoints",
            "/docs": "API documentation",
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    # Test Supabase connection
    try:
        response = supabase.table('users').select("count").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main_supabase:app", host="0.0.0.0", port=8000, reload=True)
