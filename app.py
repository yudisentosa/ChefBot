from flask import Flask, request, jsonify
from models import db
from models.ingredient import Ingredient
from config import config
import os
from chatbot import ChefBot
from werkzeug.exceptions import HTTPException
import logging
import re
from typing import List

def scale_ingredients(ingredients: List[str], target_servings: int, base_servings: int = 2) -> List[str]:
    """
    Scale ingredient quantities based on serving size.
    
    Args:
        ingredients: List of ingredient strings with quantities
        target_servings: Desired number of servings
        base_servings: Base number of servings (default is 2)
        
    Returns:
        List of ingredients with scaled quantities
    """
    if target_servings == base_servings:
        return ingredients
        
    scale_factor = target_servings / base_servings
    scaled_ingredients = []
    
    # Regular expression to find numbers in ingredient strings
    quantity_pattern = re.compile(r'(\d+(?:\.\d+)?)')
    
    for ingredient in ingredients:
        # Find all numbers in the ingredient string
        matches = quantity_pattern.findall(ingredient)
        if matches:
            for match in matches:
                try:
                    original_value = float(match)
                    scaled_value = original_value * scale_factor
                    
                    # Format the scaled value (keep integers as integers)
                    if scaled_value.is_integer():
                        formatted_value = str(int(scaled_value))
                    else:
                        formatted_value = f"{scaled_value:.1f}"
                    
                    # Replace the original value with the scaled value
                    ingredient = ingredient.replace(match, formatted_value, 1)
                except ValueError:
                    # Skip if conversion fails
                    pass
        
        scaled_ingredients.append(ingredient)
    
    return scaled_ingredients

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    # Initialize chatbot
    try:
        chef_bot = ChefBot(app.config['CHEFBOT_API_KEY'])
        logger.info("ChefBot initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing ChefBot: {e}")
        chef_bot = None

    @app.errorhandler(Exception)
    def handle_error(error):
        code = 500
        if isinstance(error, HTTPException):
            code = error.code
        return jsonify({
            'error': str(error),
            'code': code
        }), code

    @app.route('/')
    def index():
        """API Documentation endpoint."""
        return {
            "name": "Chef Bot API",
            "version": "1.0.0",
            "description": "AI-powered cooking assistant that suggests recipes based on available ingredients",
            "endpoints": {
                "/": "API documentation (this endpoint)",
                "/api/health": "Health check endpoint",
                "/api/ingredients": "GET: List all ingredients, POST: Add new ingredient",
                "/api/ingredients/<id>": "GET: Get ingredient, PUT: Update ingredient, DELETE: Delete ingredient",
                "/api/suggest-recipe": "GET: Get recipe suggestions based on available ingredients"
            }
        }

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'database': 'connected' if db else 'disconnected',
            'chatbot': 'ready' if chef_bot else 'not configured'
        })

    @app.route('/api/ingredients', methods=['GET'])
    def get_ingredients():
        try:
            ingredients = Ingredient.query.all()
            return jsonify([ingredient.to_dict() for ingredient in ingredients])
        except Exception as e:
            logger.error(f"Error fetching ingredients: {e}")
            return jsonify({'error': 'Failed to fetch ingredients'}), 500

    @app.route('/api/ingredients', methods=['POST'])
    def add_ingredient():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        try:
            # Check for duplicate ingredient
            existing = Ingredient.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({'error': f'Ingredient "{data["name"]}" already exists'}), 409
            
            ingredient = Ingredient.from_dict(data)
            db.session.add(ingredient)
            db.session.commit()
            logger.info(f"Added new ingredient: {data['name']}")
            return jsonify(ingredient.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding ingredient: {e}")
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ingredients/<int:id>', methods=['PUT'])
    def update_ingredient(id):
        ingredient = Ingredient.query.get_or_404(id)
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        try:
            for key, value in data.items():
                if hasattr(ingredient, key):
                    setattr(ingredient, key, value)
            db.session.commit()
            logger.info(f"Updated ingredient {id}")
            return jsonify(ingredient.to_dict())
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ingredient {id}: {e}")
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ingredients/<int:id>', methods=['DELETE'])
    def delete_ingredient(id):
        ingredient = Ingredient.query.get_or_404(id)
        try:
            db.session.delete(ingredient)
            db.session.commit()
            logger.info(f"Deleted ingredient {id}")
            return '', 204
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting ingredient {id}: {e}")
            return jsonify({'error': str(e)}), 400

    @app.route('/api/suggest-recipe', methods=['GET'])
    def suggest_recipe():
        """Suggest a recipe based on available ingredients."""
        try:
            # Get serving size from query parameters (default to 2)
            servings = request.args.get('servings', 2, type=int)
            
            # Validate serving size
            if servings not in [2, 4, 6, 8]:
                servings = 2  # Default to 2 if invalid
            
            # Get all ingredients from the database
            ingredients = Ingredient.query.all()
            
            if not ingredients:
                return jsonify({
                    "error": "No ingredients available. Please add ingredients first."
                }), 400
                
            # Extract ingredient names for recipe suggestion
            ingredient_names = [ingredient.name for ingredient in ingredients]
            
            if not chef_bot:
                return jsonify({
                    "error": "ChefBot is not initialized. Please check API key configuration."
                }), 500
                
            # Get recipe suggestion
            recipe = chef_bot.suggest_recipe(ingredient_names)
            
            # Add serving size to the recipe
            recipe['servings'] = servings
            
            # Scale ingredient quantities based on serving size
            if 'ingredients_required' in recipe and isinstance(recipe['ingredients_required'], list):
                recipe['ingredients_required'] = scale_ingredients(recipe['ingredients_required'], servings)
            
            return jsonify(recipe)
        except Exception as e:
            logger.error(f"Error suggesting recipe: {str(e)}")
            return jsonify({
                "error": f"Failed to suggest recipe: {str(e)}"
            }), 500

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, reloader_type='stat')
