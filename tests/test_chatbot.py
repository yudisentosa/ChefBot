import pytest
from unittest.mock import patch, MagicMock
from chatbot import ChefBot

def test_chef_bot_initialization():
    # Test successful initialization
    bot = ChefBot(api_key="test-key")
    assert bot.api_key == "test-key"
    
    # Test initialization without API key
    with pytest.raises(ValueError) as exc_info:
        ChefBot(api_key="")
    assert "API key is required" in str(exc_info.value)

@patch('requests.post')
def test_suggest_recipe_success(mock_post):
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '''
                {
                    "recipe_name": "Tomato Pasta",
                    "ingredients_required": ["200g pasta", "2 tomatoes"],
                    "missing_ingredients": ["basil"],
                    "instructions": ["Boil pasta", "Add sauce"],
                    "difficulty_level": "easy",
                    "cooking_time": "20"
                }
                '''
            }
        }]
    }
    mock_post.return_value = mock_response
    
    bot = ChefBot(api_key="test-key")
    ingredients = ["pasta", "tomato"]
    result = bot.suggest_recipe(ingredients)
    
    assert result["recipe_name"] == "Tomato Pasta"
    assert len(result["ingredients_required"]) == 2
    assert len(result["instructions"]) == 2
    assert result["difficulty_level"] == "easy"
    assert result["cooking_time"] == "20"

@patch('requests.post')
def test_suggest_recipe_api_error(mock_post):
    # Mock API error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "API Error"
    mock_post.return_value = mock_response
    
    bot = ChefBot(api_key="test-key")
    ingredients = ["tomato", "onion"]
    
    # The updated ChefBot now returns a fallback recipe instead of raising an exception
    result = bot.suggest_recipe(ingredients)
    assert result["recipe_name"] == "Error"
    assert "Failed to generate recipe" in result["instructions"][0]

def test_create_recipe_prompt():
    bot = ChefBot(api_key="test-key")
    ingredients = ["tomato", "onion", "garlic"]
    prompt = bot._create_recipe_prompt(ingredients)
    
    assert "tomato, onion, garlic" in prompt
    assert "JSON" in prompt
    assert "recipe_name" in prompt
    assert "ingredients_required" in prompt
    assert "instructions" in prompt
