import pytest
from app import create_app
from models import db
from models.ingredient import Ingredient

@pytest.fixture
def app():
    app = create_app('development')
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

def test_get_ingredients_empty(client):
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
