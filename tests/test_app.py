import pytest
from app import create_app, scale_ingredients
from models import db
from models.ingredient import Ingredient

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_ingredients_empty(client, app):
    # Clear any existing ingredients
    with app.app_context():
        Ingredient.query.delete()
        db.session.commit()
    
    response = client.get('/api/ingredients')
    assert response.status_code == 200
    assert response.json == []

def test_add_ingredient(client):
    data = {
        'name': 'Tomato',
        'quantity': 5,
        'unit': 'pieces',
        'category': 'Vegetables'
    }
    response = client.post('/api/ingredients', json=data)
    assert response.status_code == 201
    assert response.json['name'] == 'Tomato'
    
    # Verify ingredient was added
    response = client.get('/api/ingredients')
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Tomato'

def test_update_ingredient(client):
    # First add an ingredient
    data = {
        'name': 'Potato',
        'quantity': 3,
        'unit': 'pieces'
    }
    response = client.post('/api/ingredients', json=data)
    ingredient_id = response.json['id']
    
    # Update the ingredient
    update_data = {
        'quantity': 5
    }
    response = client.put(f'/api/ingredients/{ingredient_id}', json=update_data)
    assert response.status_code == 200
    assert response.json['quantity'] == 5

def test_delete_ingredient(client):
    # First add an ingredient
    data = {
        'name': 'Carrot',
        'quantity': 2,
        'unit': 'pieces'
    }
    response = client.post('/api/ingredients', json=data)
    ingredient_id = response.json['id']
    
    # Delete the ingredient
    response = client.delete(f'/api/ingredients/{ingredient_id}')
    assert response.status_code == 204
    
    # Verify ingredient was deleted
    response = client.get('/api/ingredients')
    assert len(response.json) == 0

def test_suggest_recipe_with_servings(client, monkeypatch):
    # Mock ChefBot.suggest_recipe
    def mock_suggest_recipe(self, ingredients):
        return {
            "recipe_name": "Test Recipe",
            "ingredients_required": ["2 tomatoes", "100g pasta"],
            "missing_ingredients": [],
            "instructions": ["Step 1", "Step 2"],
            "difficulty_level": "easy",
            "cooking_time": "30"
        }
    
    monkeypatch.setattr("chatbot.ChefBot.suggest_recipe", mock_suggest_recipe)
    
    # Add test ingredient
    client.post('/api/ingredients', json={
        "name": "tomato",
        "quantity": 5,
        "unit": "pieces"
    })
    
    # Test with different serving sizes
    for servings in [2, 4, 6, 8]:
        response = client.get(f'/api/suggest-recipe?servings={servings}')
        assert response.status_code == 200
        assert response.json['servings'] == servings
        
        # For servings > 2, quantities should be scaled
        if servings > 2:
            assert any(str(servings) in ing or str(servings/2) in ing for ing in response.json['ingredients_required'])

def test_scale_ingredients():
    # Test scaling with different factors
    ingredients = ["2 tomatoes", "100g pasta", "1.5 cups milk"]
    
    # Scale to 4 servings (factor of 2)
    scaled_4 = scale_ingredients(ingredients, 4)
    assert "4 tomatoes" in scaled_4
    assert "200g pasta" in scaled_4
    assert any(["3 cups milk" in ing or "3.0 cups milk" in ing for ing in scaled_4])
    
    # Scale to 6 servings (factor of 3)
    scaled_6 = scale_ingredients(ingredients, 6)
    assert "6 tomatoes" in scaled_6
    assert "300g pasta" in scaled_6
    assert any(["4.5 cups milk" in ing for ing in scaled_6])
