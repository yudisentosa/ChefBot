from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import os

# Minimal HTML response for the root path
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Chef Bot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #2c3e50;
        }
        .container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <h1>Chef Bot</h1>
    <div class="container">
        <h2>Welcome to Chef Bot</h2>
        <p>This is a simplified version of Chef Bot deployed on Vercel.</p>
        <p>The application is designed to help you find recipes based on ingredients you have.</p>
        <h3>API Endpoints:</h3>
        <ul>
            <li><a href="/api/health">/api/health</a> - Check if the API is working</li>
            <li><a href="/api/ingredients">/api/ingredients</a> - Get sample ingredients</li>
        </ul>
    </div>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        # Set default content type
        content_type = 'text/html'
        
        # Default response
        status_code = 200
        response_content = HTML_CONTENT
        
        # Health check endpoint
        if path == '/api/health':
            content_type = 'application/json'
            response_data = {
                "status": "healthy",
                "version": "1.0.0",
                "environment": os.environ.get("VERCEL_ENV", "development")
            }
            response_content = json.dumps(response_data)
            
        # Ingredients endpoint - sample data since we can't connect to Supabase here
        elif path == '/api/ingredients' or path == '/api/v1/ingredients/':
            content_type = 'application/json'
            # Sample ingredients that would normally come from Supabase
            ingredients = [
                {"id": "temp_1", "name": "Tomato", "quantity": 2, "unit": "pieces"},
                {"id": "temp_2", "name": "Onion", "quantity": 1, "unit": "pieces"},
                {"id": "temp_3", "name": "Garlic", "quantity": 3, "unit": "cloves"}
            ]
            response_content = json.dumps(ingredients)
            
        # 404 for other paths
        elif path != '/':
            status_code = 404
            response_content = "<html><body><h1>404 Not Found</h1><p>The requested path does not exist.</p></body></html>"
        
        # Send response
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response_content.encode('utf-8'))
    
    def do_POST(self):
        path = self.path
        content_type = 'application/json'
        status_code = 200
        
        # Read request body
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        post_data = self.rfile.read(content_length)
        
        try:
            # Parse JSON data
            if content_length > 0:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
                
            # Handle ingredient creation
            if path == '/api/ingredients' or path == '/api/v1/ingredients' or path == '/api/v1/ingredients/':
                # Generate a temporary ID for the ingredient
                import uuid
                import datetime
                
                temp_id = f"temp_{uuid.uuid4()}"
                now = datetime.datetime.now().isoformat()
                
                # Create a new ingredient object
                new_ingredient = {
                    "id": temp_id,
                    "name": data.get("name", ""),
                    "quantity": data.get("quantity", 1),
                    "unit": data.get("unit", "pieces"),
                    "created_at": now,
                    "updated_at": now,
                    "user_id": None  # No user ID for unauthenticated users
                }
                
                response_content = json.dumps(new_ingredient)
            else:
                status_code = 404
                response_content = json.dumps({"error": "Endpoint not found"})
        except Exception as e:
            status_code = 500
            response_content = json.dumps({"error": str(e)})
        
        # Send response
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response_content.encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
