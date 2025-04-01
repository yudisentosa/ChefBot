import pytest
from unittest.mock import patch, MagicMock
from ui import ChefBotUI

@pytest.fixture
def ui():
    return ChefBotUI("http://localhost:5000")

@pytest.fixture
def mock_ingredients():
    return [
        {
            "id": 1,
            "name": "Tomato",
            "quantity": 5,
            "unit": "pieces"
        },
        {
            "id": 2,
            "name": "Onion",
            "quantity": 2,
            "unit": "pieces"
        }
    ]

@pytest.fixture
def mock_recipe():
    return {
        "recipe_name": "Test Recipe",
        "ingredients_required": ["Tomato", "Onion"],
        "missing_ingredients": [],
        "instructions": ["Step 1", "Step 2"],
        "difficulty_level": "easy",
        "cooking_time": "30"
    }

@patch('requests.get')
def test_get_ingredients_success(mock_get, ui, mock_ingredients):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_ingredients
    mock_get.return_value = mock_response
    
    result = ui._get_ingredients()
    assert len(result) == 2
    assert result[0]["name"] == "Tomato"
    assert result[1]["name"] == "Onion"

@patch('requests.get')
def test_get_ingredients_failure(mock_get, ui):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response
    
    result = ui._get_ingredients()
    assert result == []

@patch('requests.post')
def test_add_ingredient_success(mock_post, ui):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 1,
        "name": "Carrot",
        "quantity": 3,
        "unit": "pieces"
    }
    mock_post.return_value = mock_response
    
    result = ui._add_ingredient("Carrot", 3, "pieces")
    assert result["name"] == "Carrot"
    assert result["quantity"] == 3

@patch('requests.get')
def test_get_recipe_suggestion_success(mock_get, ui, mock_recipe):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_recipe
    mock_get.return_value = mock_response
    
    result = ui._get_recipe_suggestion()
    assert result["recipe_name"] == "Test Recipe"
    assert len(result["ingredients_required"]) == 2

@patch('requests.get')
def test_get_recipe_suggestion_failure(mock_get, ui):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response
    
    result = ui._get_recipe_suggestion()
    assert "error" in result

def test_format_recipe(ui, mock_recipe):
    formatted = ui._format_recipe(mock_recipe)
    assert "Test Recipe" in formatted
    assert "Required Ingredients" in formatted
    assert "Instructions" in formatted
    assert "Difficulty: easy" in formatted
    assert "Cooking Time: 30" in formatted

def test_handle_add_ingredient_validation(ui):
    result = ui.handle_add_ingredient("", "3", "pieces")
    assert "Error" in result
    
    result = ui.handle_add_ingredient("Carrot", "invalid", "pieces")
    assert "Error" in result
