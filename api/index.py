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
import re
from urllib.request import urlopen, Request
from dotenv import load_dotenv
from supabase import create_client, Client

# Helper function to validate UUID format
def is_valid_uuid(val):
    try:
        uuid_obj = uuid.UUID(str(val))
        return str(uuid_obj) == str(val)
    except (ValueError, AttributeError, TypeError):
        return False

# Function to check if test mode is enabled
def is_test_mode_enabled(headers, path):
    """Check if test mode is enabled via headers or query parameters"""
    # Check for test mode header
    test_mode = headers.get('X-Test-Mode') == 'true'
    
    # Also check query parameters for test mode
    if '?' in path:
        query_string = path.split('?', 1)[1]
        query_params = dict(parse_qsl(query_string))
        test_mode = test_mode or query_params.get('test_mode') == 'true'
    
    # Log if test mode is enabled
    if test_mode:
        log_message("Test mode enabled for this request")
    
    return test_mode

# Function to get user_id from Google ID
def get_user_id_from_google_id(google_id):
    """Look up a user's UUID in the Supabase users table based on their Google ID"""
    if not supabase_client or not google_id:
        log_message(f"Supabase client not available or no Google ID provided", "WARNING")
        return None
    
    try:
        # Query the users table to find the UUID that corresponds to this Google ID
        response = supabase_client.table('users').select('id').match({'google_id': google_id}).execute()
        
        if response and hasattr(response, 'data') and response.data:
            # Return the UUID from the first matching user
            user_id = response.data[0]['id']
            log_message(f"Found user_id {user_id} for Google ID {google_id}")
            return user_id
        else:
            # No matching user found
            log_message(f"No user found with Google ID {google_id}", "WARNING")
            return None
    except Exception as e:
        log_message(f"Error looking up user_id for Google ID {google_id}: {str(e)}", "ERROR")
        return None

# Load environment variables
load_dotenv()

# Check if we're in development mode
is_dev_mode = os.environ.get('VERCEL_ENV') != 'production'

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
    # Try both os.environ.get and os.getenv for compatibility
    supabase_url = os.environ.get('SUPABASE_URL') or os.getenv('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY') or os.getenv('SUPABASE_KEY')
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID') or os.getenv('GOOGLE_CLIENT_ID')
    
    # # Fallback for local development
    # if not supabase_url or not supabase_key:
    #     # Check if we're in a local development environment
    #     if os.environ.get('VERCEL_ENV') != 'production':
    #         log_message("Environment variables not found, using fallback credentials for local development")
    #         # Use hardcoded credentials for local development only
    #         supabase_url = "https://wvkkpwjolvdpfhwpbxwu.supabase.co"
    #         supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2a2twd2pvbHZkcGZod3BieHd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwOTU0NzksImV4cCI6MjA1OTY3MTQ3OX0.5xNkPpG0WGmN2C9sQ8-inpQtt9OtzQiKz2EVnE3-jXc"
    
    # Log environment variable status for debugging
    log_message(f"SUPABASE_URL found: {bool(supabase_url)}")
    log_message(f"SUPABASE_KEY found: {bool(supabase_key)}")
    log_message(f"GOOGLE_CLIENT_ID found: {bool(google_client_id)}")
    
    # Print the current environment for debugging
    log_message(f"Current environment variables: {list(os.environ.keys())}")
    
    if supabase_url and supabase_key:
        try:
            # Create the Supabase client correctly
            supabase_client = create_client(supabase_url, supabase_key)
            log_message("Supabase client initialized successfully")
            log_message(f"Connected to Supabase URL: {supabase_url[:20]}...")
            
            # Test the connection by querying the users table
            test_response = supabase_client.table('users').select('id').limit(1).execute()
            if hasattr(test_response, 'data'):
                log_message(f"Supabase connection test successful. Found {len(test_response.data)} users.")
            else:
                log_message("Supabase connection test failed: unexpected response format", "WARNING")
        except Exception as e:
            log_message(f"Error initializing Supabase client: {str(e)}", "ERROR")
            supabase_client = None
        
        # Get and log the Supabase client version
        try:
            import supabase as supabase_module
            log_message(f"Using Supabase Python client version: {supabase_module.__version__}")
        except (ImportError, AttributeError):
            log_message("Could not determine Supabase client version")
        
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
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')  # 24 hours
        self.end_headers()
        
    def do_DELETE(self):
        """Handle DELETE requests"""
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            log_message(f"DELETE request: {path}")
            
            # Set default response
            status_code = 200
            content_type = 'application/json'
            response_content = '{}'
            
            # Handle saved recipe deletion
            if path.startswith('/api/v1/saved-recipes/') or path.startswith('/api/saved-recipes/'):
                # Extract the recipe ID from the path
                recipe_id = path.split('/')[-1]
                log_message(f"Deleting saved recipe with ID: {recipe_id}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Deleting recipe for user_id: {user_id}, google_id: {google_id}")
                        except Exception as e:
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                
                # Delete the recipe from Supabase
                if supabase_client:
                    try:
                        # Determine the user ID to use for querying
                        query_user_id = None
                        if google_id:
                            # For Google auth, look up the corresponding UUID
                            query_user_id = get_user_id_from_google_id(google_id)
                        elif user_id and is_valid_uuid(user_id):
                            query_user_id = user_id
                        else:
                            # Generate a consistent UUID for development mode
                            dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                            log_message(f"Using generated UUID for development: {dev_user_uuid}")
                            query_user_id = dev_user_uuid
                        
                        log_message(f"Deleting recipe {recipe_id} for user_id: {query_user_id}")
                        
                        # Delete the recipe
                        # First verify that the recipe belongs to the user
                        verify_query = supabase_client.table('saved_recipes').select('id').match({'id': recipe_id, 'user_id': query_user_id})
                        verify_response = verify_query.execute()
                        
                        if verify_response.data and len(verify_response.data) > 0:
                            # Recipe belongs to the user, proceed with deletion
                            delete_query = supabase_client.table('saved_recipes').delete().match({'id': recipe_id})
                            delete_response = delete_query.execute()
                            
                            log_message(f"Recipe deleted successfully: {recipe_id}")
                            response_content = json.dumps({"success": True, "message": "Recipe deleted successfully"})
                        else:
                            # Recipe doesn't belong to the user or doesn't exist
                            status_code = 404
                            log_message(f"Recipe not found or doesn't belong to user: {recipe_id}", "WARNING")
                            response_content = json.dumps({"error": "Recipe not found or doesn't belong to user"})
                    except Exception as e:
                        status_code = 500
                        log_message(f"Error deleting recipe from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        response_content = json.dumps({"error": f"Failed to delete recipe: {str(e)}"})
                else:
                    status_code = 503
                    log_message("Supabase client not available", "WARNING")
                    response_content = json.dumps({"error": "Supabase client not available"})
            
            # Handle ingredient deletion
            elif path.startswith('/api/v1/ingredients/') or path.startswith('/api/ingredients/'):
                # Extract the ingredient ID from the path
                ingredient_id = path.split('/')[-1]
                log_message(f"Deleting ingredient with ID: {ingredient_id}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Deleting ingredient for user_id: {user_id}, google_id: {google_id}")
                        except Exception as e:
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                
                # Delete the ingredient from Supabase
                if supabase_client:
                    try:
                        # Determine the user ID to use for querying
                        query_user_id = None
                        if google_id:
                            # For Google auth, look up the corresponding UUID
                            query_user_id = get_user_id_from_google_id(google_id)
                        elif user_id and is_valid_uuid(user_id):
                            query_user_id = user_id
                        else:
                            # Generate a consistent UUID for development mode
                            dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                            log_message(f"Using generated UUID for development: {dev_user_uuid}")
                            query_user_id = dev_user_uuid
                        
                        log_message(f"Deleting ingredient {ingredient_id} for user_id: {query_user_id}")
                        
                        # Delete the ingredient
                        # First verify that the ingredient belongs to the user
                        verify_query = supabase_client.table('ingredients').select('id').match({'id': ingredient_id, 'user_id': query_user_id})
                        verify_response = verify_query.execute()
                        
                        if verify_response.data and len(verify_response.data) > 0:
                            # Ingredient belongs to the user, proceed with deletion
                            delete_query = supabase_client.table('ingredients').delete().match({'id': ingredient_id})
                            delete_response = delete_query.execute()
                            
                            log_message(f"Ingredient deleted successfully: {ingredient_id}")
                            response_content = json.dumps({"success": True, "message": "Ingredient deleted successfully"})
                        else:
                            # Ingredient doesn't belong to the user or doesn't exist
                            status_code = 404
                            log_message(f"Ingredient not found or doesn't belong to user: {ingredient_id}", "WARNING")
                            response_content = json.dumps({"error": "Ingredient not found or doesn't belong to user"})
                    except Exception as e:
                        status_code = 500
                        log_message(f"Error deleting ingredient from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        response_content = json.dumps({"error": f"Failed to delete ingredient: {str(e)}"})
                else:
                    status_code = 503
                    log_message("Supabase client not available", "WARNING")
                    response_content = json.dumps({"error": "Supabase client not available"})
            else:
                # 404 for other paths
                status_code = 404
                response_content = json.dumps({"error": "Not found"})
            
            # Send response
            self.send_response(status_code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(response_content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            self.wfile.write(response_content.encode('utf-8'))
        except Exception as e:
            log_message(f"Error processing DELETE request: {str(e)}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            self.send_error(500, f"Internal server error: {str(e)}")
    
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
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                
                # Using global is_dev_mode variable
                
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                # Use the token directly as the user_id
                                user_id = token
                                log_message(f"GET ingredients for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                            if is_dev_mode:
                                # In dev mode, use a development user ID
                                user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                                log_message(f"Using development user ID: {user_id}")
                            else:
                                status_code = 401
                                response_content = json.dumps({"error": "Invalid authentication token"})
                                self._send_response(status_code, content_type, response_content)
                                return
                elif is_dev_mode:
                    # In development mode, allow requests without authentication
                    user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                    log_message(f"Development mode: Using default user ID: {user_id}")
                    
                    # Ensure the development user exists in the database
                    if supabase_client:
                        try:
                            # Check if the user exists
                            user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                            
                            # If user doesn't exist, create a new user record
                            if not user_check.data or len(user_check.data) == 0:
                                log_message(f"Creating development user with ID {user_id} in database")
                                
                                # Create a new user record with minimal information
                                now = datetime.datetime.now().isoformat()
                                new_user = {
                                    "id": user_id,
                                    "email": "dev@example.com",
                                    "name": "Development User",
                                    "is_active": True,
                                    "created_at": now,
                                    "updated_at": now
                                }
                                
                                # Insert the new user
                                try:
                                    user_response = supabase_client.table('users').insert(new_user).execute()
                                    log_message(f"Created development user in database")
                                except Exception as user_error:
                                    log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            
                            # Check if the user has any ingredients
                            ingredient_check = supabase_client.table('ingredients').select('id').match({'user_id': user_id}).execute()
                            
                            # If user has no ingredients, create some sample ingredients
                            if not ingredient_check.data or len(ingredient_check.data) == 0:
                                log_message(f"Creating sample ingredients for development user")
                                
                                # Create sample ingredients
                                now = datetime.datetime.now().isoformat()
                                sample_ingredients = [
                                    {
                                        "name": "Tomato",
                                        "quantity": 2,
                                        "unit": "pieces",
                                        "user_id": user_id,
                                        "created_at": now,
                                        "updated_at": now
                                    },
                                    {
                                        "name": "Onion",
                                        "quantity": 1,
                                        "unit": "pieces",
                                        "user_id": user_id,
                                        "created_at": now,
                                        "updated_at": now
                                    },
                                    {
                                        "name": "Garlic",
                                        "quantity": 3,
                                        "unit": "cloves",
                                        "user_id": user_id,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                ]
                                
                                # Insert the sample ingredients
                                try:
                                    ingredient_response = supabase_client.table('ingredients').insert(sample_ingredients).execute()
                                    log_message(f"Created {len(sample_ingredients)} sample ingredients for development user")
                                except Exception as ingredient_error:
                                    log_message(f"Error creating sample ingredients: {str(ingredient_error)}", "WARNING")
                        except Exception as check_error:
                            log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                else:
                    # No auth header and not in development mode
                    status_code = 401
                    log_message("No Authorization header provided", "WARNING")
                    response_content = json.dumps({"error": "Authentication required"})
                    self._send_response(status_code, content_type, response_content)
                    return
                
                # Initialize Supabase status
                supabase_status = {
                    "success": False,
                    "message": "Not attempted",
                    "details": None
                }
                
                # Try to get ingredients from Supabase
                ingredients = []
                if supabase_client:
                    try:
                        # Determine which user ID to use for querying
                        query_user_id = None
                        
                        if user_id and is_valid_uuid(user_id):
                            # If user_id is a valid UUID, use it directly
                            query_user_id = user_id
                            log_message(f"Using valid UUID: {query_user_id}")
                        elif is_dev_mode:
                            # In development mode, use the development user ID
                            query_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                            log_message(f"Using development user ID: {query_user_id}")
                        else:
                            # No valid user ID available and not in development mode
                            log_message("No valid user ID available", "WARNING")
                            response_content = json.dumps([])
                            self._send_response(200, content_type, response_content)
                            return
                        
                        # If we have a valid user ID, query their ingredients
                        response = None
                        if query_user_id:
                            # Build and execute the query
                            log_message(f"Querying ingredients for user_id: {query_user_id}")
                            
                            # First, check if the table exists and has data
                            try:
                                tables_check = supabase_client.table('ingredients').select('count').execute()
                                log_message(f"Ingredients table check: {tables_check.data if hasattr(tables_check, 'data') else 'No data'}")
                            except Exception as table_error:
                                log_message(f"Error checking ingredients table: {str(table_error)}", "ERROR")
                            
                            # Now query for the user's ingredients
                            query = supabase_client.table('ingredients').select('*')
                            
                            # Add debug logging for the query
                            log_message(f"Query object type: {type(query)}")
                            log_message(f"Query object attributes: {dir(query)}")
                            
                            # Add the user_id filter
                            query = query.match({'user_id': query_user_id})
                            log_message(f"Filter added for user_id: {query_user_id}")
                            
                            # Execute the query
                            try:
                                # Try the execute() method first (for newer versions)
                                response = query.execute()
                                log_message("Query executed with execute() method")
                                log_message(f"Response type: {type(response)}")
                                if hasattr(response, 'data'):
                                    log_message(f"Raw response data: {response.data}")
                            except AttributeError as attr_error:
                                # If execute() is not available, the query object itself might be the response
                                log_message(f"AttributeError: {str(attr_error)}", "WARNING")
                                log_message("Using query object directly as response")
                                response = query
                            except Exception as query_error:
                                log_message(f"Error executing query: {str(query_error)}", "ERROR")
                                response = None
                        
                            log_message(f"Supabase query executed successfully")
                        
                        # Handle response data based on the response type
                        if response:
                            log_message(f"Response type: {type(response)}", "INFO")
                            log_message(f"Response attributes: {dir(response)}", "INFO")
                            
                            if hasattr(response, 'data') and response.data is not None:
                                # For newer Supabase client versions
                                ingredients = response.data
                                log_message(f"Using response.data: {len(ingredients)} ingredients found", "INFO")
                                log_message(f"First few ingredients: {ingredients[:3] if ingredients else 'None'}", "INFO")
                            elif isinstance(response, list):
                                # Direct response might be a list
                                ingredients = response
                                log_message(f"Using response as list: {len(ingredients)} ingredients found", "INFO")
                            elif hasattr(response, 'json') and callable(getattr(response, 'json', None)):
                                # Response might have a json method
                                try:
                                    json_data = response.json()
                                    log_message(f"JSON data type: {type(json_data)}", "INFO")
                                    if isinstance(json_data, list):
                                        ingredients = json_data
                                        log_message(f"Using json_data as list: {len(ingredients)} ingredients found", "INFO")
                                    elif isinstance(json_data, dict) and 'data' in json_data:
                                        ingredients = json_data['data']
                                        log_message(f"Using json_data['data']: {len(ingredients)} ingredients found", "INFO")
                                    else:
                                        log_message(f"Unexpected JSON structure: {json_data}", "WARNING")
                                except Exception as json_error:
                                    log_message(f"Error parsing JSON response: {str(json_error)}", "ERROR")
                            else:
                                log_message(f"Could not extract ingredients from response", "WARNING")
                        else:
                            log_message("No response received from Supabase", "WARNING")
                        
                        # Update status with the results
                        if query_user_id:  # Only update status if we attempted a query
                            supabase_status = {
                                "success": True,
                                "message": f"Retrieved {len(ingredients)} ingredients from Supabase",
                                "details": {
                                    "count": len(ingredients),
                                    "timestamp": str(datetime.datetime.now())
                                }
                            }
                            log_message(f"Retrieved {len(ingredients)} ingredients from Supabase for user {query_user_id}")
                            
                            if not ingredients:
                                supabase_status = {
                                    "success": False,
                                    "message": "No ingredients found in Supabase",
                                    "details": "No ingredients found for user"
                                }
                                log_message("No ingredients found in Supabase for this user", "WARNING")
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
                
                # Return just the ingredients array as JSON
                # Check if the client wants raw data (for debugging)
                raw_data = self.headers.get('X-Raw-Data', '').lower() == 'true'
                
                if raw_data:
                    # Return a more detailed response with metadata for debugging
                    debug_response = {
                        "status": "success",
                        "count": len(ingredients),
                        "user_id": query_user_id,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data": ingredients
                    }
                    response_content = json.dumps(debug_response, indent=2)
                    log_message("Sending detailed debug response")
                else:
                    # The frontend expects a direct array, not a complex object
                    # Make sure we're sending a properly formatted JSON array
                    try:
                        # Ensure each ingredient has the expected fields
                        for ingredient in ingredients:
                            # Make sure id is a string
                            if 'id' in ingredient and ingredient['id'] is not None:
                                ingredient['id'] = str(ingredient['id'])
                            # Make sure user_id is a string
                            if 'user_id' in ingredient and ingredient['user_id'] is not None:
                                ingredient['user_id'] = str(ingredient['user_id'])
                        
                        response_content = json.dumps(ingredients)
                        log_message(f"Sending response with {len(ingredients)} ingredients")
                    except Exception as json_error:
                        log_message(f"Error formatting JSON response: {str(json_error)}", "ERROR")
                        # Fall back to a simpler response
                        response_content = json.dumps([{"name": "Error", "message": "Failed to format ingredients"}])
                
                log_message(f"Response content sample: {response_content[:200]}..." if len(response_content) > 200 else response_content)
                
            # Handle authentication verification
            elif path in ['/api/auth/me', '/api/v1/auth/me']:
                content_type = 'application/json'
                log_message(f"Processing auth verification GET request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Verifying auth for user_id: {user_id}, google_id: {google_id}")
                            
                            # For Google auth, verify the user exists in Supabase
                            if google_id and supabase_client:
                                try:
                                    # Query the users table by google_id
                                    query = supabase_client.table('users').select('*').match({'google_id': google_id})
                                    response = query.execute()
                                    
                                    if response.data and len(response.data) > 0:
                                        # User exists, return their data
                                        user_data = response.data[0]
                                        log_message(f"User verified: {user_data['email']}")
                                        response_content = json.dumps({
                                            "id": user_data['id'],
                                            "email": user_data['email'],
                                            "name": user_data['name'],
                                            "picture": user_data['picture']
                                        })
                                    else:
                                        # User not found
                                        status_code = 401
                                        log_message(f"User not found for Google ID: {google_id}", "WARNING")
                                        response_content = json.dumps({"error": "User not found"})
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error verifying user: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({"error": f"Authentication verification failed: {str(e)}"})
                            elif user_id and is_valid_uuid(user_id) and supabase_client:
                                try:
                                    # Query the users table by UUID
                                    query = supabase_client.table('users').select('*').match({'id': user_id})
                                    response = query.execute()
                                    
                                    if response.data and len(response.data) > 0:
                                        # User exists, return their data
                                        user_data = response.data[0]
                                        log_message(f"User verified: {user_data['email']}")
                                        response_content = json.dumps({
                                            "id": user_data['id'],
                                            "email": user_data['email'],
                                            "name": user_data['name'],
                                            "picture": user_data['picture']
                                        })
                                    else:
                                        # User not found
                                        status_code = 401
                                        log_message(f"User not found for ID: {user_id}", "WARNING")
                                        response_content = json.dumps({"error": "User not found"})
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error verifying user: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({"error": f"Authentication verification failed: {str(e)}"})
                            else:
                                # For development, return a mock user
                                if os.environ.get('VERCEL_ENV') != 'production':
                                    # Generate a consistent UUID for development
                                    dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                                    log_message(f"Using mock user for development with ID: {dev_user_uuid}")
                                    response_content = json.dumps({
                                        "id": dev_user_uuid,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "picture": "https://via.placeholder.com/150"
                                    })
                                else:
                                    # Invalid token
                                    status_code = 401
                                    log_message("Invalid authentication token", "WARNING")
                                    response_content = json.dumps({"error": "Invalid authentication token"})
                        except Exception as e:
                            status_code = 401
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                            response_content = json.dumps({"error": f"Invalid authentication token: {str(e)}"})
                else:
                    # Check if test mode is enabled
                    if is_test_mode_enabled(self.headers, self.path):
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
            
            # Handle saved recipes GET endpoint
            elif path in ['/api/saved-recipes', '/api/v1/saved-recipes']:
                content_type = 'application/json'
                log_message(f"Processing saved recipes GET request: {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                # Try to extract user_id from token
                                user_id = token.split('_')[0] if '_' in token else token
                                log_message(f"GET saved recipes for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                            status_code = 401
                            response_content = json.dumps({"error": "Invalid authentication token"})
                            self._send_response(status_code, content_type, response_content)
                            return
                else:
                    # Check for test mode header or query parameter
                    test_mode = self.headers.get('X-Test-Mode') == 'true'
                    
                    # Also check query parameters for test mode
                    parsed_url = urlparse(self.path)
                    query_params = dict(parse_qsl(parsed_url.query))
                    test_mode = test_mode or query_params.get('test_mode') == 'true'
                    
                    if test_mode:
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
                        self._send_response(status_code, content_type, response_content)
                        return
                
                # Parse query parameters
                skip = int(query_params.get('skip', 0))
                limit = min(int(query_params.get('limit', 100)), 100)  # Max 100 items
                
                # Try to get saved recipes from Supabase
                if supabase_client and user_id and is_valid_uuid(user_id):
                    try:
                        # Query saved_recipes for the user
                        query = supabase_client.table('saved_recipes')\
                            .select('*')\
                            .eq('user_id', user_id)\
                            .range(skip, skip + limit - 1)
                        
                        # Execute the query
                        log_message(f"Executing Supabase query for saved recipes with user_id: {user_id}")
                        response = query.execute()
                        log_message(f"Supabase query executed successfully")
                        
                        if response.data is not None:
                            saved_recipes = response.data
                            log_message(f"Retrieved {len(saved_recipes)} saved recipes from Supabase for user {user_id}")
                            
                            # Process each recipe to ensure JSON fields are properly parsed
                            for recipe in saved_recipes:
                                try:
                                    # Parse JSON fields if they're stored as strings
                                    for field in ['ingredients_required', 'missing_ingredients', 'instructions']:
                                        if field in recipe and isinstance(recipe[field], str):
                                            recipe[field] = json.loads(recipe[field])
                                except Exception as e:
                                    log_message(f"Error parsing JSON fields in recipe: {str(e)}", "WARNING")
                            
                            response_content = json.dumps(saved_recipes)
                        else:
                            # No saved recipes found
                            log_message("No saved recipes found in Supabase", "INFO")
                            response_content = json.dumps([])
                    except Exception as e:
                        status_code = 500
                        log_message(f"Error getting saved recipes from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        response_content = json.dumps({
                            "error": "Failed to retrieve saved recipes",
                            "detail": str(e)
                        })
                else:
                    if not user_id or not is_valid_uuid(user_id):
                        status_code = 401
                        log_message(f"Invalid user ID: {user_id}", "WARNING")
                        response_content = json.dumps({"error": "Invalid user ID"})
                    else:
                        status_code = 503
                        log_message("Supabase client not available", "WARNING")
                        response_content = json.dumps({"error": "Database connection error"})
            
            # Handle single saved recipe GET endpoint
            elif path.startswith('/api/saved-recipes/') or path.startswith('/api/v1/saved-recipes/'):
                content_type = 'application/json'
                
                # Extract recipe ID from path
                recipe_id = path.split('/')[-1]
                log_message(f"Processing single saved recipe GET request for ID: {recipe_id}")
                
                # Get user ID from Authorization header
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                # Try to extract user_id from token
                                user_id = token.split('_')[0] if '_' in token else token
                                log_message(f"GET saved recipe for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                            status_code = 401
                            response_content = json.dumps({"error": "Invalid authentication token"})
                            self._send_response(status_code, content_type, response_content)
                            return
                else:
                    # Check for test mode header or query parameter
                    test_mode = self.headers.get('X-Test-Mode') == 'true'
                    
                    # Also check query parameters for test mode
                    parsed_url = urlparse(self.path)
                    query_params = dict(parse_qsl(parsed_url.query))
                    test_mode = test_mode or query_params.get('test_mode') == 'true'
                    
                    if test_mode:
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
                        self._send_response(status_code, content_type, response_content)
                        return
                
                # Try to get the saved recipe from Supabase
                if supabase_client and user_id and is_valid_uuid(user_id):
                    try:
                        # Query the specific saved recipe
                        query = supabase_client.table('saved_recipes')\
                            .select('*')\
                            .eq('id', recipe_id)\
                            .eq('user_id', user_id)
                        
                        # Execute the query
                        log_message(f"Executing Supabase query for saved recipe with ID: {recipe_id}")
                        response = query.execute()
                        log_message(f"Supabase query executed successfully")
                        
                        if response.data and len(response.data) > 0:
                            saved_recipe = response.data[0]
                            log_message(f"Retrieved saved recipe: {saved_recipe['recipe_name']}")
                            
                            # Parse JSON fields if they're stored as strings
                            try:
                                for field in ['ingredients_required', 'missing_ingredients', 'instructions']:
                                    if field in saved_recipe and isinstance(saved_recipe[field], str):
                                        saved_recipe[field] = json.loads(saved_recipe[field])
                            except Exception as e:
                                log_message(f"Error parsing JSON fields in recipe: {str(e)}", "WARNING")
                            
                            response_content = json.dumps(saved_recipe)
                        else:
                            # Recipe not found
                            status_code = 404
                            log_message(f"Saved recipe not found with ID: {recipe_id}", "WARNING")
                            response_content = json.dumps({"error": "Recipe not found"})
                    except Exception as e:
                        status_code = 500
                        log_message(f"Error getting saved recipe from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        response_content = json.dumps({
                            "error": "Failed to retrieve saved recipe",
                            "detail": str(e)
                        })
                else:
                    if not user_id or not is_valid_uuid(user_id):
                        status_code = 401
                        log_message(f"Invalid user ID: {user_id}", "WARNING")
                        response_content = json.dumps({"error": "Invalid user ID"})
                    else:
                        status_code = 503
                        log_message("Supabase client not available", "WARNING")
                        response_content = json.dumps({"error": "Database connection error"})
            
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
            
            # Handle authentication verification
            if path in ['/api/auth/me', '/api/v1/auth/me']:
                log_message(f"Processing auth verification request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Verifying auth for user_id: {user_id}, google_id: {google_id}")
                            
                            # For Google auth, verify the user exists in Supabase
                            if google_id and supabase_client:
                                try:
                                    # Query the users table by google_id
                                    query = supabase_client.table('users').select('*').match({'google_id': google_id})
                                    response = query.execute()
                                    
                                    if response.data and len(response.data) > 0:
                                        # User exists, return their data
                                        user_data = response.data[0]
                                        log_message(f"User verified: {user_data['email']}")
                                        response_content = json.dumps({
                                            "id": user_data['id'],
                                            "email": user_data['email'],
                                            "name": user_data['name'],
                                            "picture": user_data['picture']
                                        })
                                    else:
                                        # User not found
                                        status_code = 401
                                        log_message(f"User not found for Google ID: {google_id}", "WARNING")
                                        response_content = json.dumps({"error": "User not found"})
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error verifying user: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({"error": f"Authentication verification failed: {str(e)}"})
                            elif user_id and is_valid_uuid(user_id) and supabase_client:
                                try:
                                    # Query the users table by UUID
                                    query = supabase_client.table('users').select('*').match({'id': user_id})
                                    response = query.execute()
                                    
                                    if response.data and len(response.data) > 0:
                                        # User exists, return their data
                                        user_data = response.data[0]
                                        log_message(f"User verified: {user_data['email']}")
                                        response_content = json.dumps({
                                            "id": user_data['id'],
                                            "email": user_data['email'],
                                            "name": user_data['name'],
                                            "picture": user_data['picture']
                                        })
                                    else:
                                        # User not found
                                        status_code = 401
                                        log_message(f"User not found for ID: {user_id}", "WARNING")
                                        response_content = json.dumps({"error": "User not found"})
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error verifying user: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({"error": f"Authentication verification failed: {str(e)}"})
                            else:
                                # For development, return a mock user
                                if os.environ.get('VERCEL_ENV') != 'production':
                                    # Generate a consistent UUID for development
                                    dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                                    log_message(f"Using mock user for development with ID: {dev_user_uuid}")
                                    response_content = json.dumps({
                                        "id": dev_user_uuid,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "picture": "https://via.placeholder.com/150"
                                    })
                                else:
                                    # Invalid token
                                    status_code = 401
                                    log_message("Invalid authentication token", "WARNING")
                                    response_content = json.dumps({"error": "Invalid authentication token"})
                        except Exception as e:
                            status_code = 401
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                            response_content = json.dumps({"error": f"Invalid authentication token: {str(e)}"})
                else:
                    # Check if test mode is enabled
                    if is_test_mode_enabled(self.headers, self.path):
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
            
            # Handle Google authentication
            elif path in ['/api/auth/google', '/api/v1/auth/google']:
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
                            # Extract Google ID from the response
                            google_id = google_response['sub']
                            user_id = f"google_{google_id}"
                            log_message(f"Authentication successful for user: {user_id}")
                            
                            # Check if user exists in database and create if not
                            db_user_id = get_user_id_from_google_id(google_id)
                            
                            if not db_user_id and supabase_client:
                                try:
                                    # User doesn't exist, create a new user record
                                    log_message(f"Creating new user record for Google ID: {google_id}")
                                    
                                    # Generate a new UUID for the user
                                    new_user_uuid = str(uuid.uuid4())
                                    
                                    # Create user object
                                    new_user = {
                                        "id": new_user_uuid,
                                        "email": google_response.get('email', ''),
                                        "name": google_response.get('name', ''),
                                        "picture": google_response.get('picture', ''),
                                        "google_id": google_id,
                                        "is_active": True,
                                        "created_at": datetime.datetime.now().isoformat(),
                                        "updated_at": datetime.datetime.now().isoformat()
                                    }
                                    
                                    # Insert into Supabase
                                    log_message(f"Inserting new user into database: {json.dumps(new_user)}")
                                    response = supabase_client.table('users').insert(new_user).execute()
                                    
                                    if response and hasattr(response, 'data') and response.data:
                                        db_user_id = new_user_uuid
                                        log_message(f"User created successfully with UUID: {db_user_id}")
                                    else:
                                        log_message("Failed to create user record", "ERROR")
                                except Exception as e:
                                    log_message(f"Error creating user: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                            elif db_user_id:
                                log_message(f"User already exists with UUID: {db_user_id}")
                            
                            # Generate a session token
                            session_token = self._generate_session_token(user_id)
                            
                            # Create user response in the format expected by the frontend
                            # Frontend expects: { access_token: string, user: { id, email, name, picture } }
                            user_data = {
                                "access_token": session_token,
                                "user": {
                                    "id": user_id,
                                    "email": google_response.get('email', ''),
                                    "name": google_response.get('name', ''),
                                    "picture": google_response.get('picture', ''),
                                    "uuid": db_user_id  # Include the database UUID for reference
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
                
            # Handle saved recipes - GET all saved recipes
            elif path in ['/api/saved-recipes', '/api/v1/saved-recipes'] and self.command == 'GET':
                log_message(f"Processing saved recipes GET request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Getting saved recipes for user_id: {user_id}, google_id: {google_id}")
                        except Exception as e:
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                
                # Get saved recipes from Supabase
                if supabase_client:
                    try:
                        # Determine the user ID to use for querying
                        query_user_id = None
                        if google_id:
                            # For Google auth, look up the corresponding UUID
                            query_user_id = get_user_id_from_google_id(google_id)
                        elif user_id and is_valid_uuid(user_id):
                            query_user_id = user_id
                        else:
                            # Generate a consistent UUID for development mode
                            dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                            log_message(f"Using generated UUID for development: {dev_user_uuid}")
                            query_user_id = dev_user_uuid
                        
                        log_message(f"Querying saved recipes for user_id: {query_user_id}")
                        
                        # Query the saved_recipes table
                        query = supabase_client.table('saved_recipes').select('*').match({'user_id': query_user_id})
                        response = query.execute()
                        
                        if response.data:
                            saved_recipes = response.data
                            log_message(f"Found {len(saved_recipes)} saved recipes")
                            response_content = json.dumps(saved_recipes)
                        else:
                            log_message("No saved recipes found for user")
                            response_content = json.dumps([])
                    except Exception as e:
                        status_code = 500
                        log_message(f"Error getting saved recipes from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                        response_content = json.dumps({
                            "error": "Failed to get saved recipes",
                            "detail": str(e)
                        })
                else:
                    log_message("Supabase client not available, returning empty array", "WARNING")
                    response_content = json.dumps([])
            
            # Handle saved recipes - POST a new saved recipe
            elif path in ['/api/saved-recipes', '/api/v1/saved-recipes'] and self.command == 'POST':
                log_message(f"Processing saved recipe POST request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Saving recipe for user_id: {user_id}, google_id: {google_id}")
                        except Exception as e:
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                
                # Validate required fields
                if not data.get("recipe_name"):
                    status_code = 400
                    response_content = json.dumps({"error": "Recipe name is required"})
                elif not data.get("ingredients_required"):
                    status_code = 400
                    response_content = json.dumps({"error": "Ingredients are required"})
                elif not data.get("instructions"):
                    status_code = 400
                    response_content = json.dumps({"error": "Instructions are required"})
                else:
                    # Generate a UUID for the recipe
                    recipe_id = str(uuid.uuid4())
                    now = datetime.datetime.now().isoformat()
                    
                    # Save the recipe to Supabase
                    if supabase_client:
                        try:
                            # Determine the user ID to use
                            query_user_id = None
                            if google_id:
                                # For Google auth, look up the corresponding UUID
                                query_user_id = get_user_id_from_google_id(google_id)
                            elif user_id and is_valid_uuid(user_id):
                                query_user_id = user_id
                            else:
                                # Generate a consistent UUID for development mode
                                dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                                log_message(f"Using generated UUID for development: {dev_user_uuid}")
                                query_user_id = dev_user_uuid
                            
                            log_message(f"Saving recipe for user_id: {query_user_id}")
                            
                            # Create a new recipe object
                            new_recipe = {
                                "id": recipe_id,
                                "recipe_name": data.get("recipe_name"),
                                "ingredients_required": json.dumps(data.get("ingredients_required")),
                                "missing_ingredients": json.dumps(data.get("missing_ingredients", [])),
                                "instructions": json.dumps(data.get("instructions")),
                                "difficulty_level": data.get("difficulty_level", ""),
                                "cooking_time": data.get("cooking_time", ""),
                                "servings": int(data.get("servings", 2)),
                                "notes": data.get("notes", ""),
                                "created_at": now,
                                "updated_at": now,
                                "user_id": query_user_id
                            }
                            
                            # Insert the recipe into Supabase
                            log_message(f"Inserting recipe into Supabase: {new_recipe['recipe_name']}")
                            response = supabase_client.table('saved_recipes').insert(new_recipe).execute()
                            
                            if response.data:
                                # Parse the response data to convert JSON strings back to objects
                                saved_recipe = response.data[0]
                                try:
                                    saved_recipe['ingredients_required'] = json.loads(saved_recipe['ingredients_required'])
                                    saved_recipe['missing_ingredients'] = json.loads(saved_recipe['missing_ingredients'])
                                    saved_recipe['instructions'] = json.loads(saved_recipe['instructions'])
                                except Exception as e:
                                    log_message(f"Error parsing JSON fields: {str(e)}", "WARNING")
                                
                                log_message(f"Recipe saved successfully: {saved_recipe['recipe_name']}")
                                response_content = json.dumps(saved_recipe)
                            else:
                                log_message("No data returned from Supabase insert", "WARNING")
                                response_content = json.dumps({
                                    "id": recipe_id,
                                    "recipe_name": data.get("recipe_name"),
                                    "message": "Recipe saved, but no data returned"
                                })
                        except Exception as e:
                            status_code = 500
                            log_message(f"Error saving recipe to Supabase: {str(e)}", "ERROR")
                            log_message(traceback.format_exc(), "ERROR")
                            response_content = json.dumps({
                                "error": "Failed to save recipe",
                                "detail": str(e)
                            })
                    else:
                        status_code = 503
                        log_message("Supabase client not available", "WARNING")
                        response_content = json.dumps({
                            "error": "Supabase client not available",
                            "detail": "Database connection error"
                        })
            
            # Handle saved recipes POST endpoint
            elif path in ['/api/saved-recipes', '/api/v1/saved-recipes'] and self.command == 'POST':
                log_message(f"Processing saved recipe POST request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                user_id = token.split('_')[0] if '_' in token else token
                            
                            log_message(f"Creating saved recipe for user: {user_id}")
                            
                            # Validate user_id
                            if not user_id or not is_valid_uuid(user_id):
                                status_code = 401
                                log_message(f"Invalid user ID: {user_id}", "WARNING")
                                response_content = json.dumps({"error": "Invalid user ID"})
                                self._send_response(status_code, content_type, response_content)
                                return
                            
                            # Validate required fields in the request
                            required_fields = ['recipe_name', 'ingredients_required', 'instructions']
                            for field in required_fields:
                                if field not in data:
                                    status_code = 400
                                    log_message(f"Missing required field: {field}", "WARNING")
                                    response_content = json.dumps({"error": f"Missing required field: {field}"})
                                    self._send_response(status_code, content_type, response_content)
                                    return
                            
                            # Create recipe in Supabase
                            if supabase_client:
                                try:
                                    # Generate a UUID for the recipe
                                    recipe_id = str(uuid.uuid4())
                                    
                                    # Prepare recipe data
                                    recipe_data = {
                                        "id": recipe_id,
                                        "recipe_name": data.get("recipe_name"),
                                        "ingredients_required": json.dumps(data.get("ingredients_required")),
                                        "missing_ingredients": json.dumps(data.get("missing_ingredients", [])),
                                        "instructions": json.dumps(data.get("instructions")),
                                        "difficulty_level": data.get("difficulty_level", "Medium"),
                                        "cooking_time": data.get("cooking_time", 30),
                                        "servings": data.get("servings", 2),
                                        "notes": data.get("notes", ""),
                                        "user_id": user_id,
                                        "created_at": datetime.datetime.now().isoformat(),
                                        "updated_at": datetime.datetime.now().isoformat()
                                    }
                                    
                                    # Insert into Supabase
                                    log_message(f"Inserting recipe into Supabase: {recipe_data['recipe_name']}")
                                    response = supabase_client.table('saved_recipes').insert(recipe_data).execute()
                                    
                                    if response.data:
                                        # Parse the response data to convert JSON strings back to objects
                                        saved_recipe = response.data[0]
                                        try:
                                            saved_recipe['ingredients_required'] = json.loads(saved_recipe['ingredients_required'])
                                            saved_recipe['missing_ingredients'] = json.loads(saved_recipe['missing_ingredients'])
                                            saved_recipe['instructions'] = json.loads(saved_recipe['instructions'])
                                        except Exception as e:
                                            log_message(f"Error parsing JSON fields: {str(e)}", "WARNING")
                                        
                                        log_message(f"Recipe saved successfully: {saved_recipe['recipe_name']}")
                                        response_content = json.dumps(saved_recipe)
                                    else:
                                        log_message("No data returned from Supabase insert", "WARNING")
                                        response_content = json.dumps({
                                            "id": recipe_id,
                                            "recipe_name": data.get("recipe_name"),
                                            "message": "Recipe saved, but no data returned"
                                        })
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error saving recipe to Supabase: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({
                                        "error": "Failed to save recipe",
                                        "detail": str(e)
                                    })
                            else:
                                status_code = 503
                                log_message("Supabase client not available", "WARNING")
                                response_content = json.dumps({
                                    "error": "Supabase client not available",
                                    "detail": "Database connection error"
                                })
                        except Exception as e:
                            status_code = 401
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                            response_content = json.dumps({"error": f"Invalid authentication token: {str(e)}"})
                else:
                    # Check if test mode is enabled
                    if is_test_mode_enabled(self.headers, self.path):
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
            
            # Handle saved recipe PUT endpoint
            elif (path.startswith('/api/saved-recipes/') or path.startswith('/api/v1/saved-recipes/')) and self.command == 'PUT':
                content_type = 'application/json'
                
                # Extract recipe ID from path
                recipe_id = path.split('/')[-1]
                log_message(f"Processing saved recipe PUT request for ID: {recipe_id}")
                
                # Get user ID from Authorization header
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                # Try to extract user_id from token
                                user_id = token.split('_')[0] if '_' in token else token
                                log_message(f"UPDATE saved recipe for user: {user_id}")
                            
                            # Validate user_id
                            if not user_id or not is_valid_uuid(user_id):
                                status_code = 401
                                log_message(f"Invalid user ID: {user_id}", "WARNING")
                                response_content = json.dumps({"error": "Invalid user ID"})
                                self._send_response(status_code, content_type, response_content)
                                return
                            
                            # Update recipe in Supabase
                            if supabase_client:
                                try:
                                    # First check if the recipe exists and belongs to the user
                                    check_query = supabase_client.table('saved_recipes')\
                                        .select('id')\
                                        .eq('id', recipe_id)\
                                        .eq('user_id', user_id)
                                    
                                    check_response = check_query.execute()
                                    
                                    if not check_response.data or len(check_response.data) == 0:
                                        status_code = 404
                                        log_message(f"Recipe not found or not owned by user: {recipe_id}", "WARNING")
                                        response_content = json.dumps({"error": "Recipe not found"})
                                        self._send_response(status_code, content_type, response_content)
                                        return
                                    
                                    # Prepare update data
                                    update_data = {}
                                    for field in ['recipe_name', 'difficulty_level', 'cooking_time', 'servings', 'notes']:
                                        if field in data:
                                            update_data[field] = data[field]
                                    
                                    # Handle JSON fields
                                    for field in ['ingredients_required', 'missing_ingredients', 'instructions']:
                                        if field in data:
                                            update_data[field] = json.dumps(data[field])
                                    
                                    # Add updated timestamp
                                    update_data['updated_at'] = datetime.datetime.now().isoformat()
                                    
                                    # Update in Supabase
                                    log_message(f"Updating recipe in Supabase: {recipe_id}")
                                    response = supabase_client.table('saved_recipes')\
                                        .update(update_data)\
                                        .eq('id', recipe_id)\
                                        .eq('user_id', user_id)\
                                        .execute()
                                    
                                    if response.data and len(response.data) > 0:
                                        # Parse the response data to convert JSON strings back to objects
                                        updated_recipe = response.data[0]
                                        try:
                                            updated_recipe['ingredients_required'] = json.loads(updated_recipe['ingredients_required'])
                                            updated_recipe['missing_ingredients'] = json.loads(updated_recipe['missing_ingredients'])
                                            updated_recipe['instructions'] = json.loads(updated_recipe['instructions'])
                                        except Exception as e:
                                            log_message(f"Error parsing JSON fields: {str(e)}", "WARNING")
                                        
                                        log_message(f"Recipe updated successfully: {updated_recipe['recipe_name']}")
                                        response_content = json.dumps(updated_recipe)
                                    else:
                                        status_code = 500
                                        log_message("No data returned from Supabase update", "WARNING")
                                        response_content = json.dumps({"error": "Failed to update recipe"})
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error updating recipe in Supabase: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({
                                        "error": "Failed to update recipe",
                                        "detail": str(e)
                                    })
                            else:
                                status_code = 503
                                log_message("Supabase client not available", "WARNING")
                                response_content = json.dumps({"error": "Database connection error"})
                        except Exception as e:
                            status_code = 401
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                            response_content = json.dumps({"error": f"Invalid authentication token: {str(e)}"})
                else:
                    # Check if test mode is enabled
                    if is_test_mode_enabled(self.headers, self.path):
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
            
            # Handle saved recipe DELETE endpoint
            elif (path.startswith('/api/saved-recipes/') or path.startswith('/api/v1/saved-recipes/')) and self.command == 'DELETE':
                content_type = 'application/json'
                
                # Extract recipe ID from path
                recipe_id = path.split('/')[-1]
                log_message(f"Processing saved recipe DELETE request for ID: {recipe_id}")
                
                # Get user ID from Authorization header
                user_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                                
                                # If no user found for this Google ID, create a new user
                                if not user_id and supabase_client and google_id:
                                    try:
                                        # Create a new user with this Google ID
                                        now = datetime.datetime.now().isoformat()
                                        new_user_id = str(uuid.uuid4())
                                        new_user = {
                                            "id": new_user_id,
                                            "google_id": google_id,
                                            "email": f"user_{google_id}@example.com",  # Placeholder
                                            "name": f"User {google_id[:8]}",  # Placeholder
                                            "is_active": True,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert the new user
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        user_id = new_user_id
                                        log_message(f"Created new user with ID {user_id} for Google ID {google_id}")
                                    except Exception as create_error:
                                        log_message(f"Error creating user for Google ID: {str(create_error)}", "ERROR")
                            else:
                                # Try to extract user_id from token
                                user_id = token.split('_')[0] if '_' in token else token
                                log_message(f"DELETE saved recipe for user: {user_id}")
                            
                            # Validate user_id
                            if not user_id or not is_valid_uuid(user_id):
                                status_code = 401
                                log_message(f"Invalid user ID: {user_id}", "WARNING")
                                response_content = json.dumps({"error": "Invalid user ID"})
                                self._send_response(status_code, content_type, response_content)
                                return
                            
                            # Delete recipe from Supabase
                            if supabase_client:
                                try:
                                    # First check if the recipe exists and belongs to the user
                                    check_query = supabase_client.table('saved_recipes')\
                                        .select('id')\
                                        .eq('id', recipe_id)\
                                        .eq('user_id', user_id)
                                    
                                    check_response = check_query.execute()
                                    
                                    if not check_response.data or len(check_response.data) == 0:
                                        status_code = 404
                                        log_message(f"Recipe not found or not owned by user: {recipe_id}", "WARNING")
                                        response_content = json.dumps({"error": "Recipe not found"})
                                        self._send_response(status_code, content_type, response_content)
                                        return
                                    
                                    # Delete from Supabase
                                    log_message(f"Deleting recipe from Supabase: {recipe_id}")
                                    delete_response = supabase_client.table('saved_recipes')\
                                        .delete()\
                                        .eq('id', recipe_id)\
                                        .eq('user_id', user_id)\
                                        .execute()
                                    
                                    # Return 204 No Content for successful deletion
                                    status_code = 204
                                    response_content = ""
                                    log_message(f"Recipe deleted successfully: {recipe_id}")
                                except Exception as e:
                                    status_code = 500
                                    log_message(f"Error deleting recipe from Supabase: {str(e)}", "ERROR")
                                    log_message(traceback.format_exc(), "ERROR")
                                    response_content = json.dumps({
                                        "error": "Failed to delete recipe",
                                        "detail": str(e)
                                    })
                            else:
                                status_code = 503
                                log_message("Supabase client not available", "WARNING")
                                response_content = json.dumps({"error": "Database connection error"})
                        except Exception as e:
                            status_code = 401
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                            response_content = json.dumps({"error": f"Invalid authentication token: {str(e)}"})
                else:
                    # Check if test mode is enabled
                    if is_test_mode_enabled(self.headers, self.path):
                        # In test mode, use a development user ID
                        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                        log_message(f"Test mode: Using default user ID: {user_id}")
                        
                        # Ensure the development user exists in the database
                        if supabase_client:
                            try:
                                # Check if the user exists
                                user_check = supabase_client.table('users').select('id').match({'id': user_id}).execute()
                                
                                # If user doesn't exist, create a new user record
                                if not user_check.data or len(user_check.data) == 0:
                                    log_message(f"Creating development user with ID {user_id} in database")
                                    
                                    # Create a new user record with minimal information
                                    now = datetime.datetime.now().isoformat()
                                    new_user = {
                                        "id": user_id,
                                        "email": "dev@example.com",
                                        "name": "Development User",
                                        "is_active": True,
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert the new user
                                    try:
                                        user_response = supabase_client.table('users').insert(new_user).execute()
                                        log_message(f"Created development user in database")
                                    except Exception as user_error:
                                        log_message(f"Error creating development user: {str(user_error)}", "WARNING")
                            except Exception as check_error:
                                log_message(f"Error checking if development user exists: {str(check_error)}", "WARNING")
                    else:
                        # No auth header and not in test mode
                        status_code = 401
                        log_message("No Authorization header provided", "WARNING")
                        response_content = json.dumps({"error": "Authentication required"})
            
            # Handle recipe suggestion
            elif path in ['/api/recipes/suggest', '/api/v1/recipes/suggest']:
                log_message(f"Processing recipe suggestion request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                            # Otherwise use the token directly as the user_id
                            else:
                                user_id = token
                            
                            log_message(f"Getting ingredients for user_id: {user_id}, google_id: {google_id}")
                        except Exception as e:
                            log_message(f"Error extracting user info from token: {str(e)}", "ERROR")
                
                # Get the servings from the request data
                servings = data.get('servings', 2)
                servings = max(1, min(10, int(servings)))
                log_message(f"Recipe request for {servings} servings")
                
                # Get ingredients for this user from Supabase
                ingredients = []
                if supabase_client:
                    try:
                        # Determine the user ID to use for querying
                        query_user_id = None
                        if google_id:
                            # For Google auth, look up the corresponding UUID
                            query_user_id = get_user_id_from_google_id(google_id)
                        elif user_id and is_valid_uuid(user_id):
                            query_user_id = user_id
                        else:
                            # Generate a consistent UUID for development mode
                            dev_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                            log_message(f"Using generated UUID for development: {dev_user_uuid}")
                            query_user_id = dev_user_uuid
                        
                        log_message(f"Querying ingredients for user_id: {query_user_id}")
                        
                        # Query the ingredients
                        query = supabase_client.table('ingredients').select('name').match({'user_id': query_user_id})
                        response = query.execute()
                        
                        if response.data:
                            ingredients = [item['name'] for item in response.data]
                            log_message(f"Found {len(ingredients)} ingredients: {', '.join(ingredients)}")
                        else:
                            log_message("No ingredients found for user")
                    except Exception as e:
                        log_message(f"Error getting ingredients from Supabase: {str(e)}", "ERROR")
                        log_message(traceback.format_exc(), "ERROR")
                
                # If no ingredients, use sample data
                if not ingredients:
                    ingredients = ["tomato", "onion", "garlic", "chicken", "rice"]
                    log_message(f"Using sample ingredients: {', '.join(ingredients)}")
                
                # Call DeepSeek API for recipe suggestion
                try:
                    # Get API key from environment
                    api_key = os.environ.get('CHEFBOT_API_KEY')
                    if not api_key:
                        log_message("CHEFBOT_API_KEY not found in environment variables", "WARNING")
                        api_key = "sk-9b6c218b1fc74804a160de966c97957a"  # Fallback key for development
                    
                    # Create the prompt for DeepSeek
                    prompt = f"""Generate a recipe using some or all of these ingredients: {', '.join(ingredients)}. 
                    Create a common dish (chinese, korean, western, indonesia) with ingredients, you dont have to use all ingredients
                    Make sure the recipe is well-known in indonesia, for example like spagethi, mie goreng, soto, etc
                    Not only main dish, you can also create a side dish or dessert
                    The recipe should serve {servings} people.
                    Format the response as a JSON object with these fields:
                    - recipe_name: A name for the recipe
                    - ingredients_required: An array of strings, each one an ingredient with quantity
                    - missing_ingredients: An array of strings for ingredients not in the original list
                    - instructions: An array of strings, each one a step in the recipe
                    - difficulty_level: Easy, Medium, or Hard
                    - cooking_time: Estimated time in minutes
                    - servings: {servings}
                    """
                    
                    log_message("Calling DeepSeek API for recipe suggestion")
                    
                    # Call DeepSeek API
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                    
                    deepseek_url = "https://api.deepseek.com/v1/chat/completions"
                    deepseek_payload = {
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a helpful cooking assistant that generates recipes based on available ingredients."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                    
                    # Make the request to DeepSeek
                    req = Request(
                        deepseek_url,
                        data=json.dumps(deepseek_payload).encode('utf-8'),
                        headers=headers,
                        method='POST'
                    )
                    
                    with urlopen(req) as response:
                        api_response = json.loads(response.read().decode('utf-8'))
                    
                    # Extract the recipe from the response
                    recipe_text = api_response['choices'][0]['message']['content']
                    log_message("Received recipe from DeepSeek API")
                    
                    # Try to parse the JSON from the response
                    try:
                        # Find JSON in the response (it might be wrapped in markdown code blocks)
                        json_start = recipe_text.find('{')
                        json_end = recipe_text.rfind('}')
                        
                        if json_start >= 0 and json_end >= 0:
                            recipe_json = recipe_text[json_start:json_end+1]
                            recipe_data = json.loads(recipe_json)
                            
                            # Ensure all required fields are present
                            required_fields = ['recipe_name', 'ingredients_required', 'instructions', 'difficulty_level', 'cooking_time']
                            for field in required_fields:
                                if field not in recipe_data:
                                    recipe_data[field] = [] if field in ['ingredients_required', 'instructions'] else ""
                            
                            # Add missing_ingredients if not present
                            if 'missing_ingredients' not in recipe_data:
                                recipe_data['missing_ingredients'] = []
                            
                            # Add servings
                            recipe_data['servings'] = servings
                            
                            # Return the recipe data
                            response_content = json.dumps(recipe_data)
                            log_message(f"Returning recipe: {recipe_data['recipe_name']}")
                        else:
                            # If JSON parsing fails, return an error
                            status_code = 500
                            response_content = json.dumps({
                                "error": "Failed to parse recipe from API response",
                                "detail": "The API response did not contain valid JSON"
                            })
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, return an error
                        status_code = 500
                        response_content = json.dumps({
                            "error": "Failed to parse recipe from API response",
                            "detail": str(e)
                        })
                except Exception as e:
                    # If API call fails, return an error
                    status_code = 500
                    log_message(f"Error calling DeepSeek API: {str(e)}", "ERROR")
                    log_message(traceback.format_exc(), "ERROR")
                    response_content = json.dumps({
                        "error": "Failed to get recipe suggestion",
                        "detail": str(e)
                    })
            
            # Handle ingredient creation with Supabase integration
            elif path in ['/api/ingredients', '/api/v1/ingredients']:
                log_message(f"Processing ingredient creation request to {path}")
                
                # Get user ID from Authorization header if available
                user_id = None
                google_id = None
                auth_header = self.headers.get('Authorization', '')
                
                # Check if test mode is enabled
                test_mode = is_test_mode_enabled(self.headers, self.path)
                
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                    # Extract user information from the token
                    if token:
                        try:
                            # Check if this is a Google token
                            if token.startswith('google_'):
                                # Extract the Google ID from the token - only the part before any underscores
                                raw_id = token.replace('google_', '')
                                google_id = raw_id.split('_')[0] if '_' in raw_id else raw_id
                                log_message(f"Extracted Google ID from token: {google_id}")
                                
                                # Get the corresponding user_id from the Google ID
                                user_id = get_user_id_from_google_id(google_id)
                                log_message(f"Retrieved user_id for Google auth: {user_id}")
                            else:
                                # Use the token directly as the user_id
                                user_id = token
                                log_message(f"Creating ingredient for user: {user_id}")
                        except Exception as e:
                            log_message(f"Error extracting user_id from token: {str(e)}", "ERROR")
                            status_code = 401
                            response_content = json.dumps({"error": "Invalid authentication token"})
                            self._send_response(status_code, content_type, response_content)
                            return
                elif test_mode or is_dev_mode:
                    # In test mode or development mode, use a development user ID
                    user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dev.example.com'))
                    log_message(f"Test/Dev mode: Using default user ID: {user_id}")
                else:
                    # No auth header and not in test/dev mode
                    status_code = 401
                    log_message("No Authorization header provided", "WARNING")
                    response_content = json.dumps({"error": "Authentication required"})
                    self._send_response(status_code, content_type, response_content)
                    return
                
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
                    }
                    
                    # The user_id column in ingredients table must be a valid UUID
                    valid_user_id = None
                    
                    if google_id:
                        # For Google authentication, look up the corresponding UUID in the users table
                        user_uuid = get_user_id_from_google_id(google_id)
                        if user_uuid and is_valid_uuid(user_uuid):
                            valid_user_id = user_uuid
                            log_message(f"Found user_id {user_uuid} for Google ID {google_id}")
                        else:
                            log_message(f"No valid user_id found for Google ID {google_id}", "WARNING")
                    
                    # If we don't have a valid user_id yet, try the direct user_id
                    if not valid_user_id and user_id and is_valid_uuid(user_id):
                        valid_user_id = user_id
                        log_message(f"Using provided UUID: {user_id}")
                    
                    # If we don't have a valid user_id, return an error
                    if not valid_user_id:
                        log_message("No valid user ID available for ingredient creation", "WARNING")
                        status_code = 401
                        response_content = json.dumps({"error": "Authentication required"})
                        self._send_response(status_code, content_type, response_content)
                        return
                    
                    # Set the user_id in the new ingredient
                    new_ingredient["user_id"] = valid_user_id
                    log_message(f"Final user_id for ingredient: {valid_user_id}")
                    
                    # Before inserting the ingredient, make sure the user exists in the database
                    if supabase_client:
                        try:
                            # Check if the user exists
                            user_check = supabase_client.table('users').select('id').match({'id': valid_user_id}).execute()
                            
                            # If user doesn't exist, create a new user record
                            if not user_check.data or len(user_check.data) == 0:
                                log_message(f"User with ID {valid_user_id} not found in database, creating new user record")
                                
                                # Create a new user record with minimal information
                                new_user = {
                                    "id": valid_user_id,
                                    "email": f"user_{valid_user_id[:8]}@example.com",  # Generate a placeholder email
                                    "name": f"User {valid_user_id[:8]}",  # Generate a placeholder name
                                    "is_active": True,
                                    "created_at": now,
                                    "updated_at": now
                                }
                                
                                # If we have a Google ID, add it to the user record
                                if google_id:
                                    new_user["google_id"] = google_id
                                
                                # Insert the new user
                                try:
                                    user_response = supabase_client.table('users').insert(new_user).execute()
                                    log_message(f"Created new user with ID: {valid_user_id}")
                                except Exception as user_error:
                                    log_message(f"Error creating user: {str(user_error)}", "ERROR")
                        except Exception as check_error:
                            log_message(f"Error checking if user exists: {str(check_error)}", "ERROR")
                    
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
                            # Try different insert syntaxes for compatibility with different Supabase versions
                            try:
                                # First try without array wrapping (for newer versions)
                                log_message("Trying insert without array wrapping")
                                response = supabase_client.table('ingredients').insert(new_ingredient).execute()
                            except Exception as syntax_error:
                                log_message(f"First insert syntax failed: {str(syntax_error)}, trying alternative syntax")
                                # If that fails, try with array wrapping (for older versions)
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
                                        "timestamp": new_ingredient.get('created_at', str(datetime.datetime.now()))
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
                    
                    # Return both the ingredient and the Supabase status for better debugging
                    response_data = {
                        "ingredient": new_ingredient,
                        "supabase_status": supabase_status
                    }
                    
                    # If Supabase insertion failed but we're still returning a response,
                    # set the appropriate status code to indicate a partial success
                    if not supabase_status["success"] and supabase_client:
                        status_code = 207  # Multi-Status
                        log_message("Returning partial success status code due to Supabase insertion failure")
                    
                    response_content = json.dumps(response_data)
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
            
            # More permissive CORS headers for development
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Max-Age', '86400')  # 24 hours
            
            # Add cache control headers to prevent caching
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            
            self.end_headers()
            
            # Ensure we're sending a properly encoded string
            if isinstance(response_content, str):
                self.wfile.write(response_content.encode('utf-8'))
                log_message(f"Sent string response, length: {len(response_content)}")
            elif isinstance(response_content, bytes):
                self.wfile.write(response_content)
                log_message(f"Sent bytes response, length: {len(response_content)}")
            else:
                # If it's not a string or bytes, convert to JSON
                json_content = json.dumps(response_content)
                self.wfile.write(json_content.encode('utf-8'))
                log_message(f"Sent JSON response, length: {len(json_content)}")
                
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
