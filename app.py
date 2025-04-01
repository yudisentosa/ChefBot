from flask import Flask, request, jsonify
from models import db
from models.ingredient import Ingredient
from config import config
import os
from chatbot import ChefBot

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    chef_bot = ChefBot(app.config['DEEPSEEK_API_KEY'])

    @app.route('/api/ingredients', methods=['GET'])
    def get_ingredients():
        ingredients = Ingredient.query.all()
        return jsonify([ingredient.to_dict() for ingredient in ingredients])

    @app.route('/api/ingredients', methods=['POST'])
    def add_ingredient():
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        try:
            ingredient = Ingredient.from_dict(data)
            db.session.add(ingredient)
            db.session.commit()
            return jsonify(ingredient.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ingredients/<int:id>', methods=['PUT'])
    def update_ingredient(id):
        ingredient = Ingredient.query.get_or_404(id)
        data = request.get_json()
        
        try:
            for key, value in data.items():
                if hasattr(ingredient, key):
                    setattr(ingredient, key, value)
            db.session.commit()
            return jsonify(ingredient.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ingredients/<int:id>', methods=['DELETE'])
    def delete_ingredient(id):
        ingredient = Ingredient.query.get_or_404(id)
        try:
            db.session.delete(ingredient)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/suggest-recipe', methods=['GET'])
    def suggest_recipe():
        ingredients = Ingredient.query.all()
        ingredient_names = [ingredient.name for ingredient in ingredients]
        
        try:
            recipe_suggestion = chef_bot.suggest_recipe(ingredient_names)
            return jsonify(recipe_suggestion)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True)
