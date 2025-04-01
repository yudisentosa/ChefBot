from flask import Flask, request, jsonify
from models import db
from models.ingredient import Ingredient
from config import config
import os
from chatbot import ChefBot
from werkzeug.exceptions import HTTPException
import logging

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
        chef_bot = ChefBot(app.config['DEEPSEEK_API_KEY'])
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
        if not chef_bot:
            return jsonify({'error': 'ChefBot is not configured'}), 503
            
        try:
            ingredients = Ingredient.query.all()
            if not ingredients:
                return jsonify({'error': 'No ingredients available'}), 404
                
            ingredient_names = [ingredient.name for ingredient in ingredients]
            recipe_suggestion = chef_bot.suggest_recipe(ingredient_names)
            return jsonify(recipe_suggestion)
        except Exception as e:
            logger.error(f"Error suggesting recipe: {e}")
            return jsonify({'error': 'Failed to generate recipe suggestion'}), 500

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True)
