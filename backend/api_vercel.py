"""
Simplified API handler for Vercel deployment of Chef Bot.
This file serves as the entry point for Vercel serverless functions.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Chef Bot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Import API routes
try:
    from app.api.endpoints import ingredients, recipes, auth, saved_recipes
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(ingredients.router, prefix="/api/v1/ingredients", tags=["ingredients"])
    app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
    app.include_router(saved_recipes.router, prefix="/api/v1/saved-recipes", tags=["saved-recipes"])
    
    logger.info("Successfully loaded API routes")
except Exception as e:
    logger.error(f"Error loading API routes: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML page."""
    try:
        with open("backend/static/simple.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving HTML: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": os.environ.get("VERCEL_ENV", "development")}

# For Vercel serverless functions
def handler(request, *args, **kwargs):
    """Handler for Vercel serverless functions."""
    return app(request, *args, **kwargs)
