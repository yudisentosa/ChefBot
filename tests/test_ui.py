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

@patch('requests.put')
def test_update_ingredient_success(mock_put, ui):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "name": "Carrot",
        "quantity": 5,
        "unit": "pieces"
    }
    mock_put.return_value = mock_response
    
    result = ui._update_ingredient(1, "Carrot", 5, "pieces")
    assert result["name"] == "Carrot"
    assert result["quantity"] == 5

@patch('requests.delete')
def test_delete_ingredient_success(mock_delete, ui):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Ingredient deleted successfully"}
    mock_delete.return_value = mock_response
    
    result = ui._delete_ingredient(1)
    assert "message" in result

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

@patch('requests.get')
def test_get_recipe_suggestion_with_servings(mock_get, ui, mock_recipe):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_recipe
    mock_get.return_value = mock_response
    
    # Test with different serving sizes
    for servings in [2, 4, 6, 8]:
        result = ui._get_recipe_suggestion(servings)
        assert result["recipe_name"] == "Test Recipe"
        # Verify the API was called with the correct servings parameter
        mock_get.assert_called_with(f"http://localhost:5000/api/suggest-recipe?servings={servings}")

def test_format_recipe(ui, mock_recipe):
    formatted = ui._format_recipe(mock_recipe)
    assert "Test Recipe" in formatted
    assert "Required Ingredients" in formatted
    assert "Instructions" in formatted
    assert "Difficulty: easy" in formatted
    assert "Cooking Time: 30" in formatted

def test_format_recipe_with_servings(ui, mock_recipe):
    # Test with different serving sizes
    for servings in [2, 4, 6, 8]:
        formatted = ui._format_recipe(mock_recipe, servings)
        assert f"Serves {servings}" in formatted
        assert "Test Recipe" in formatted

def test_handle_add_ingredient_validation(ui):
    result = ui.handle_add_ingredient("", "3", "pieces")
    assert "Error" in result
    
    result = ui.handle_add_ingredient("Carrot", "invalid", "pieces")
    assert "Error" in result

def test_handle_update_ingredient(ui):
    with patch.object(ui, '_update_ingredient') as mock_update:
        mock_update.return_value = {"name": "Carrot", "quantity": 5, "unit": "pieces"}
        
        # Test with valid input
        result = ui.handle_update_ingredient("1: Carrot", "Carrot", "5", "pieces")
        assert "Successfully updated" in result
        
        # Test with missing ingredient ID
        result = ui.handle_update_ingredient("", "Carrot", "5", "pieces")
        assert "Error" in result
        
        # Test with invalid quantity
        result = ui.handle_update_ingredient("1: Carrot", "Carrot", "invalid", "pieces")
        assert "Error" in result

def test_handle_delete_ingredient(ui):
    with patch.object(ui, '_delete_ingredient') as mock_delete:
        mock_delete.return_value = {"message": "Ingredient deleted successfully"}
        
        # Test with valid input
        result = ui.handle_delete_ingredient("1: Carrot")
        assert "Successfully deleted" in result
        
        # Test with missing ingredient ID
        result = ui.handle_delete_ingredient("")
        assert "Error" in result
