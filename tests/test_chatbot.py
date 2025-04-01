import pytest
from unittest.mock import patch, MagicMock
from chatbot import ChefBot

@pytest.fixture
def mock_api_response():
    return {
        "recipe_name": "Test Recipe",
        "possible_with_ingredients": True,
        "ingredients_required": ["ingredient1", "ingredient2"],
        "missing_ingredients": [],
        "instructions": ["Step 1", "Step 2"],
        "difficulty_level": "easy",
        "cooking_time": "30"
    }

def test_chef_bot_initialization():
    with pytest.raises(ValueError):
        ChefBot(api_key=None)
    
    bot = ChefBot(api_key="test-key")
    assert bot.api_key == "test-key"

@patch('requests.post')
def test_suggest_recipe_success(mock_post, mock_api_response):
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": str(mock_api_response)
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    bot = ChefBot(api_key="test-key")
    ingredients = ["tomato", "onion"]
    result = bot.suggest_recipe(ingredients)
    
    assert result["recipe_name"] == "Test Recipe"
    assert isinstance(result["ingredients_required"], list)
    assert isinstance(result["instructions"], list)

@patch('requests.post')
def test_suggest_recipe_api_error(mock_post):
    # Mock API error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "API Error"
    mock_post.return_value = mock_response
    
    bot = ChefBot(api_key="test-key")
    ingredients = ["tomato", "onion"]
    
    with pytest.raises(Exception) as exc_info:
        bot.suggest_recipe(ingredients)
    assert "API call failed" in str(exc_info.value)

def test_create_recipe_prompt():
    bot = ChefBot(api_key="test-key")
    ingredients = ["tomato", "onion", "garlic"]
    prompt = bot._create_recipe_prompt(ingredients)
    
    assert "tomato, onion, garlic" in prompt
    assert "recipe_name" in prompt
    assert "instructions" in prompt
