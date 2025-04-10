from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Add the parent directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app from your main_supabase.py
from backend.main_supabase import app as chef_bot_app

# Create a new FastAPI app for Vercel
app = chef_bot_app

# This is needed for Vercel serverless functions
def handler(request, *args, **kwargs):
    return app(request, *args, **kwargs)
