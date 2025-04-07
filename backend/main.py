from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import logging
import os

from app.core.config import settings
from app.api.endpoints import ingredients, recipes, auth, saved_recipes
from app.db.base import Base, engine
from app.db.migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Run migrations
run_migrations()

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
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
