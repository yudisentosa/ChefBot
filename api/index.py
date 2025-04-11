from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, parse_qsl
import json
import os
import sys
import uuid
import datetime
import base64
import hmac
import hashlib
import traceback
from urllib.request import urlopen, Request
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Setup basic logging
def log_message(message, level="INFO"):
    """Log a message with timestamp and level"""
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)
    sys.stderr.flush()

# Initialize Supabase client
supabase_client = None
try:
    from supabase import create_client, Client
    # Get Supabase credentials from environment variables
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    # Log environment variable status for debugging
    log_message(f"SUPABASE_URL found: {bool(supabase_url)}")
    log_message(f"SUPABASE_KEY found: {bool(supabase_key)}")
    
    if supabase_url and supabase_key:
        # Create the Supabase client correctly
        supabase_client = create_client(supabase_url, supabase_key)
        log_message("Supabase client initialized successfully")
        log_message(f"Connected to Supabase URL: {supabase_url[:20]}...")
        
        # Verify connection by attempting a simple query
        try:
            # Test query to verify connection
            test_response = supabase_client.table('ingredients').select('*').limit(1).execute()
            log_message(f"Supabase connection verified with test query")
        except Exception as test_error:
            log_message(f"Supabase connection test failed: {str(test_error)}", "WARNING")
            log_message(f"This may indicate an issue with permissions or table structure")
    else:
        log_message("Supabase URL or key not found in environment variables", "WARNING")
        log_message("Make sure to set SUPABASE_URL and SUPABASE_KEY in your Vercel environment variables")
except ImportError:
    log_message("Supabase client not installed, make sure 'supabase' is in requirements.txt", "WARNING")
except Exception as e:
    log_message(f"Error initializing Supabase client: {str(e)}", "ERROR")
    log_message(traceback.format_exc(), "ERROR")

# Log startup information
log_message(f"Starting Chef Bot API server in {os.environ.get('VERCEL_ENV', 'development')} environment")
log_message(f"Python version: {sys.version}")
log_message(f"Current directory: {os.getcwd()}")

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

# Define a simple handler for Vercel serverless functions
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        full_path = self.path
        query_params = {}
        
        # Parse query parameters if present
        if '?' in full_path:
            path_parts = full_path.split('?', 1)
            path = path_parts[0]
            query_string = path_parts[1]
            query_params = dict(parse_qsl(query_string))
        else:
            path = full_path
        
        # Normalize path by removing trailing slash
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        
        # Log the request
        log_message(f"GET request: {full_path} (normalized path: {path})")
        log_message(f"Query parameters: {query_params}")
        
        # Set default content type
        content_type = 'text/html'
        
        # Default response
        status_code = 200
        response_content = HTML_CONTENT
        
        try:
            # Health check endpoint
            if path == '/api/health' or path == '/api/v1/health':
                content_type = 'application/json'
                response_data = {
                    "status": "healthy",
                    "version": "1.0.0",
                    "environment": os.environ.get("VERCEL_ENV", "development"),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "python_version": sys.version
                }
                response_content = json.dumps(response_data)
                
            # Ingredients endpoint with Supabase integration
            elif path in ['/api/ingredients', '/api/v1/ingredients']:
                content_type = 'application/json'
                log_message(f"Processing ingredients request: {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # In a real app, you would validate the token
                    # Here we just extract the user ID from the token
                    if token:
                        try:
                            # Try to extract user_id from token
                            user_id = token.split('_')[0] if '_' in token else None
                            log_message(f"GET ingredients for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                
                # Initialize Supabase status
                supabase_status = {
                    "success": False,
                    "message": "Not attempted",
                    "details": None
                }
                
                # Try to get ingredients from Supabase
                if supabase_client:
                    try:
                        # Query ingredients for the user
                        query = supabase_client.table('ingredients')
                        
                        # Filter by user_id if available
                        if user_id:
                            # Use the correct eq method for filtering in Supabase Python client
                            query = query.eq('user_id', user_id)
                        
                        # Execute the query with detailed logging
                        log_message(f"Executing Supabase query for ingredients with user_id filter: {user_id is not None}")
                        response = query.execute()
                        log_message(f"Supabase query executed successfully")
                        
                        if response.data is not None:
                            ingredients = response.data
                            supabase_status = {
                                "success": True,
                                "message": f"Retrieved {len(ingredients)} ingredients from Supabase",
                                "details": {
                                    "count": len(ingredients),
                                    "user_id": user_id or "anonymous"
                                }
                            }
                            log_message(f"Retrieved {len(ingredients)} ingredients from Supabase for user {user_id or 'anonymous'}")
                        else:
                            supabase_status = {
                                "success": False,
                                "message": "No ingredients found in Supabase",
                                "details": "Using sample data"
                            }
                            log_message("No ingredients found in Supabase, using sample data", "WARNING")
                            ingredients = [
                                {
                                    "id": "temp_1",
                                    "name": "Tomato",
                                    "quantity": 2,
                                    "unit": "pieces",
                                    "user_id": user_id or "demo_user",
                                    "created_at": datetime.datetime.now().isoformat(),
                                    "updated_at": datetime.datetime.now().isoformat()
                                },
                                {
                                    "id": "temp_2",
                                    "name": "Onion",
                                    "quantity": 1,
                                    "unit": "pieces",
                                    "user_id": user_id or "demo_user",
                                    "created_at": datetime.datetime.now().isoformat(),
                                    "updated_at": datetime.datetime.now().isoformat()
                                },
                                {
                                    "id": "temp_3",
                                    "name": "Garlic",
                                    "quantity": 3,
                                    "unit": "cloves",
                                    "user_id": user_id or "demo_user",
                                    "created_at": datetime.datetime.now().isoformat(),
                                    "updated_at": datetime.datetime.now().isoformat()
                                }
                            ]
                    except Exception as e:
                        error_msg = str(e)
                        supabase_status = {
                            "success": False,
                            "message": "Error retrieving from Supabase",
                            "details": error_msg
                        }
                        log_message(f"Error getting ingredients from Supabase: {error_msg}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        ingredients = [
                            {
                                "id": "temp_1",
                                "name": "Tomato",
                                "quantity": 2,
                                "unit": "pieces",
                                "user_id": user_id or "demo_user",
                                "created_at": datetime.datetime.now().isoformat(),
                                "updated_at": datetime.datetime.now().isoformat()
                            },
                            {
                                "id": "temp_2",
                                "name": "Onion",
                                "quantity": 1,
                                "unit": "pieces",
                                "user_id": user_id or "demo_user",
                                "created_at": datetime.datetime.now().isoformat(),
                                "updated_at": datetime.datetime.now().isoformat()
                            },
                            {
                                "id": "temp_3",
                                "name": "Garlic",
                                "quantity": 3,
                                "unit": "cloves",
                                "user_id": user_id or "demo_user",
                                "created_at": datetime.datetime.now().isoformat(),
                                "updated_at": datetime.datetime.now().isoformat()
                            }
                        ]
                else:
                    supabase_status = {
                        "success": False,
                        "message": "Supabase client not available",
                        "details": "Using sample data"
                    }
                    log_message("Supabase client not available, using sample ingredients", "WARNING")
                    ingredients = [
                        {
                            "id": "temp_1",
                            "name": "Tomato",
                            "quantity": 2,
                            "unit": "pieces",
                            "user_id": user_id or "demo_user",
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat()
                        },
                        {
                            "id": "temp_2",
                            "name": "Onion",
                            "quantity": 1,
                            "unit": "pieces",
                            "user_id": user_id or "demo_user",
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat()
                        },
                        {
                            "id": "temp_3",
                            "name": "Garlic",
                            "quantity": 3,
                            "unit": "cloves",
                            "user_id": user_id or "demo_user",
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat()
                        }
                    ]
                
                # Return ingredients as JSON with Supabase status
                response_content = json.dumps({
                    "success": True,
                    "ingredients": ingredients,
                    "supabase": supabase_status
                })
                
            # 404 for other paths
            elif path != '/':
                status_code = 404
                content_type = 'application/json' if self._accepts_json() else 'text/html'
                
                if content_type == 'application/json':
                    response_content = json.dumps({
                        "error": "Not Found",
                        "message": "The requested path does not exist",
                        "path": path
                    })
                else:
                    response_content = "<html><body><h1>404 Not Found</h1><p>The requested path does not exist.</p></body></html>"
        except Exception as e:
            # Log the error
            log_message(f"Error processing GET request to {path}: {str(e)}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            
            # Return a 500 error
            status_code = 500
            content_type = 'application/json' if self._accepts_json() else 'text/html'
            
            if content_type == 'application/json':
                response_content = json.dumps({
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred"
                })
            else:
                response_content = "<html><body><h1>500 Internal Server Error</h1><p>An unexpected error occurred.</p></body></html>"
        
        # Send response
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response_content.encode('utf-8'))
    
    def do_POST(self):
        full_path = self.path
        content_type = 'application/json'
        status_code = 200
        response_content = ""
        
        # Parse the path and query parameters
        path = full_path.split('?')[0] if '?' in full_path else full_path
        
        # Normalize path by removing trailing slash
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        
        # Log the request with detailed information
        log_message(f"POST request: {full_path} (normalized path: {path})")
        
        # Read request body
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        post_data = self.rfile.read(content_length)
        
        try:
            # Parse JSON data
            if content_length > 0:
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    # Log request data (omit sensitive fields)
                    safe_data = {k: v for k, v in data.items() if k.lower() not in ['password', 'token', 'credential']}
                    if 'credential' in data:
                        safe_data['credential'] = '***REDACTED***'
                    log_message(f"POST data: {safe_data}")
                except json.JSONDecodeError as json_err:
                    log_message(f"JSON decode error: {str(json_err)}", "ERROR")
                    status_code = 400
                    response_content = json.dumps({"error": "Invalid JSON in request body"})
                    self._send_response(status_code, content_type, response_content)
                    return
            else:
                data = {}
            
            # Handle Google OAuth authentication
            if path in ['/api/auth/google', '/api/v1/auth/google']:
                # Log all data for debugging
                log_message(f"Auth data received: {data}")
                
                # Try to get the Google ID token from different possible locations
                id_token = None
                
                # Check in the JSON body under different possible keys
                for key in ['credential', 'token', 'id_token', 'googleToken']:
                    if key in data and data[key]:
                        id_token = data[key]
                        log_message(f"Found token in data[{key}]")
                        break
                
                # If still not found, check query parameters
                if not id_token and '?' in full_path:
                    query_string = full_path.split('?', 1)[1]
                    query_params = dict(parse_qsl(query_string))
                    log_message(f"Query parameters: {query_params}")
                    
                    for key in ['credential', 'token', 'id_token', 'googleToken']:
                        if key in query_params and query_params[key]:
                            id_token = query_params[key]
                            log_message(f"Found token in query_params[{key}]")
                            break
                
                if not id_token:
                    status_code = 400
                    response_content = json.dumps({"error": "Missing Google ID token", "received_data": safe_data})
                else:
                    try:
                        # Verify the token with Google's servers
                        log_message("Verifying Google token...")
                        google_response = self._verify_google_token(id_token)
                        
                        if google_response and 'sub' in google_response:
                            # Generate a session token
                            user_id = f"google_{google_response['sub']}"
                            log_message(f"Authentication successful for user: {user_id}")
                            session_token = self._generate_session_token(user_id)
                            
                            # Create user response in the format expected by the frontend
                            # Frontend expects: { access_token: string, user: { id, email, name, picture } }
                            user_data = {
                                "access_token": session_token,
                                "user": {
                                    "id": user_id,
                                    "email": google_response.get('email', ''),
                                    "name": google_response.get('name', ''),
                                    "picture": google_response.get('picture', '')
                                }
                            }
                            
                            response_content = json.dumps(user_data)
                        else:
                            log_message("Invalid Google token or missing 'sub' field", "WARNING")
                            status_code = 401
                            response_content = json.dumps({"error": "Invalid Google token"})
                    except Exception as auth_error:
                        log_message(f"Authentication error: {str(auth_error)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        status_code = 401
                        response_content = json.dumps({"error": f"Authentication failed: {str(auth_error)}"})
                
            # Handle ingredient creation with Supabase integration
            elif path in ['/api/ingredients', '/api/v1/ingredients']:
                log_message(f"Processing ingredient creation request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # In a real app, you would validate the token
                    # Here we just extract the user ID from the token
                    if token:
                        try:
                            user_id = token.split('_')[0] if '_' in token else None
                            log_message(f"Creating ingredient for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                
                # Validate required fields
                if not data.get("name"):
                    status_code = 400
                    response_content = json.dumps({"error": "Ingredient name is required"})
                else:
                    # Generate a UUID for the ingredient
                    ingredient_id = str(uuid.uuid4())
                    now = datetime.datetime.now().isoformat()
                    
                    # Create a new ingredient object with all required fields
                    new_ingredient = {
                        "id": ingredient_id,
                        "name": data.get("name", ""),
                        "quantity": float(data.get("quantity", 1)),  # Ensure quantity is a number
                        "unit": data.get("unit", "pieces"),
                        "created_at": now,
                        "updated_at": now,
                        "user_id": user_id or "demo_user"  # Use the authenticated user ID or demo_user
                    }
                    
                    # Initialize Supabase status
                    supabase_status = {
                        "success": False,
                        "message": "Not attempted",
                        "details": None
                    }
                    
                    # Try to insert the ingredient into Supabase
                    if supabase_client:
                        try:
                            # Insert the ingredient into Supabase
                            log_message(f"Attempting to insert ingredient into Supabase table 'ingredients': {new_ingredient['name']}")
                            # Use the correct insert syntax for the Supabase Python client
                            log_message(f"Executing Supabase insert with data: {json.dumps(new_ingredient)}")
                            response = supabase_client.table('ingredients').insert([new_ingredient]).execute()
                            log_message(f"Supabase insert executed successfully")
                            
                            # If successful, use the returned data
                            if response and hasattr(response, 'data') and response.data:
                                new_ingredient = response.data[0]
                                supabase_status = {
                                    "success": True,
                                    "message": f"Ingredient successfully added to Supabase",
                                    "details": {
                                        "id": new_ingredient['id'],
                                        "name": new_ingredient['name'],
                                        "timestamp": new_ingredient.get('created_at', str(datetime.now()))
                                    }
                                }
                                log_message(f"Ingredient successfully inserted into Supabase: {new_ingredient['name']} with ID: {new_ingredient['id']}")
                            else:
                                supabase_status = {
                                    "success": False,
                                    "message": "Supabase insert returned no data",
                                    "details": str(response) if response else None
                                }
                                log_message(f"Supabase insert returned no data or unexpected response: {response}", "WARNING")
                        except Exception as e:
                            error_msg = str(e)
                            supabase_status = {
                                "success": False,
                                "message": "Error inserting into Supabase",
                                "details": error_msg
                            }
                            log_message(f"Error inserting ingredient into Supabase: {error_msg}", "ERROR")
                            log_message(traceback.format_exc(), "ERROR")
                            # Continue with the local ingredient, don't fail the request
                    else:
                        supabase_status = {
                            "success": False,
                            "message": "Supabase client not available",
                            "details": "Using local storage only"
                        }
                        log_message("Supabase client not available, using local ingredient only", "WARNING")
                    
                    log_message(f"Created ingredient: {new_ingredient['name']} with ID: {new_ingredient['id']}")
                    response_content = json.dumps(new_ingredient)
            else:
                status_code = 404
                response_content = json.dumps({"error": "Endpoint not found", "path": path})
        except Exception as e:
            # Log the error
            log_message(f"Error processing POST request to {path}: {str(e)}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            
            status_code = 500
            response_content = json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            })
        
        # Send response with proper headers
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        # Make sure we're sending a string
        if isinstance(response_content, str):
            self.wfile.write(response_content.encode('utf-8'))
        else:
            log_message(f"Warning: Response content is not a string: {type(response_content)}", "WARNING")
            self.wfile.write(json.dumps({"error": "Invalid response format"}).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        log_message(f"OPTIONS request: {self.path}")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _send_response(self, status_code, content_type, response_content):
        """Helper method to send a response with proper headers"""
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            
            # Ensure we're sending a properly encoded string
            if isinstance(response_content, str):
                self.wfile.write(response_content.encode('utf-8'))
            elif isinstance(response_content, bytes):
                self.wfile.write(response_content)
            else:
                # If it's not a string or bytes, convert to JSON
                self.wfile.write(json.dumps(response_content).encode('utf-8'))
                
            log_message(f"Response sent successfully with status {status_code}")
        except Exception as e:
            log_message(f"Error sending response: {str(e)}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
    
    def _accepts_json(self):
        """Check if the client accepts JSON responses"""
        accept_header = self.headers.get('Accept', '')
        return 'application/json' in accept_header
    
    def _verify_google_token(self, token):
        """Verify Google ID token by making a request to Google's tokeninfo endpoint"""
        try:
            # For simplicity, we'll use Google's tokeninfo endpoint
            # In production, you should use a proper JWT verification library
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            
            # Create a request with a timeout
            headers = {'User-Agent': 'ChefBot/1.0'}
            req = Request(url, headers=headers)
            
            # Open with timeout (5 seconds)
            response = urlopen(req, timeout=5)
            data = json.loads(response.read().decode())
            
            # Verify the audience matches your Google Client ID
            client_id = os.environ.get('GOOGLE_CLIENT_ID')
            if client_id and data.get('aud') != client_id:
                log_message(f"Token audience mismatch. Expected: {client_id}, Got: {data.get('aud')}", "WARNING")
                # For demo purposes, we'll still accept the token even if client_id doesn't match
                # In production, you should return None here
            
            return data
        except Exception as e:
            log_message(f"Error verifying Google token: {str(e)}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            return None
    
    def _generate_session_token(self, user_id):
        """Generate a simple session token for the user"""
        # In a real app, you would use a proper JWT library
        # This is a simplified version for demo purposes
        timestamp = datetime.datetime.now().timestamp()
        random_part = uuid.uuid4().hex[:10]
        
        # Create a simple token with user_id, timestamp, and random part
        token = f"{user_id}_{timestamp}_{random_part}"
        
        # In a real app, you would sign this token with a secret key
        # Here's a simplified example of signing
        secret = os.environ.get('SECRET_KEY', 'default_secret_key')
        signature = hmac.new(
            secret.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()[:10]
        
        return f"{token}_{signature}"
