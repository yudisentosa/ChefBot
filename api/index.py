from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create FastAPI app
app = FastAPI()

@app.get("/")
async def read_root():
    """Root endpoint for Vercel deployment."""
    try:
        # Try to read the HTML file
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "backend", "static", "simple.html")
        
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            logger.error(f"HTML file not found at {html_path}")
            return HTMLResponse(content="<html><body><h1>Chef Bot</h1><p>HTML file not found</p></body></html>")
    except Exception as e:
        logger.error(f"Error serving HTML: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": os.environ.get("VERCEL_ENV", "development")}

@app.get("/api/ingredients")
async def get_ingredients():
    """Get ingredients endpoint."""
    try:
        # This is a placeholder - in a real app, you'd connect to Supabase here
        return JSONResponse(content=[
            {"id": "1", "name": "Tomato", "quantity": 2, "unit": "pieces"},
            {"id": "2", "name": "Onion", "quantity": 1, "unit": "pieces"},
            {"id": "3", "name": "Garlic", "quantity": 3, "unit": "cloves"}
        ])
    except Exception as e:
        logger.error(f"Error getting ingredients: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# This is required for Vercel serverless functions
def handler(request, *args, **kwargs):
    return app(request, *args, **kwargs)
