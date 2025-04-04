import React, { useState, useEffect } from 'react';
import { X, ChevronUp, ChevronDown, Plus, ChefHat, Book } from 'lucide-react';
import axios from 'axios';

interface Ingredient {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  created_at: string;
  updated_at: string;
}

interface NewIngredient {
  name: string;
  quantity: number;
  unit: string;
}

interface Recipe {
  recipe_name: string;
  ingredients_required: string[];
  missing_ingredients: string[];
  instructions: string[];
  difficulty_level: string;
  cooking_time: string;
  servings: number;
}

function App() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [activeTab, setActiveTab] = useState('inventory');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [servings, setServings] = useState<number>(2);

  const [newIngredient, setNewIngredient] = useState<NewIngredient>({
    name: '',
    quantity: 1,
    unit: 'pieces'
  });

  const units = ['pieces', 'ml', 'g', 'kg', 'tbsp', 'tsp', 'cup'];

  // Fetch ingredients on component mount
  useEffect(() => {
    fetchIngredients();
  }, []);

  const fetchIngredients = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/v1/ingredients');
      setIngredients(response.data);
    } catch (err) {
      console.error('Error fetching ingredients:', err);
      setError('Failed to load ingredients. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuantityChange = async (id: number, increment: boolean) => {
    const ingredient = ingredients.find(ing => ing.id === id);
    if (!ingredient) return;

    const newQuantity = increment 
      ? ingredient.quantity + 1 
      : Math.max(0.1, ingredient.quantity - 1);

    try {
      await axios.put(`/api/v1/ingredients/${id}`, {
        quantity: newQuantity
      });
      
      // Update local state
      setIngredients(ingredients.map(ing => 
        ing.id === id ? { ...ing, quantity: newQuantity } : ing
      ));
    } catch (err) {
      console.error('Error updating ingredient quantity:', err);
      setError('Failed to update quantity. Please try again.');
    }
  };

  const handleUnitChange = async (id: number, newUnit: string) => {
    try {
      await axios.put(`/api/v1/ingredients/${id}`, {
        unit: newUnit
      });
      
      // Update local state
      setIngredients(ingredients.map(ing => 
        ing.id === id ? { ...ing, unit: newUnit } : ing
      ));
    } catch (err) {
      console.error('Error updating ingredient unit:', err);
      setError('Failed to update unit. Please try again.');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/v1/ingredients/${id}`);
      
      // Update local state
      setIngredients(ingredients.filter(ing => ing.id !== id));
    } catch (err) {
      console.error('Error deleting ingredient:', err);
      setError('Failed to delete ingredient. Please try again.');
    }
  };

  const handleAddIngredient = async () => {
    if (!newIngredient.name.trim()) return;
    
    try {
      const response = await axios.post('/api/v1/ingredients', newIngredient);
      
      // Add to local state
      setIngredients([...ingredients, response.data]);
      
      // Reset form
      setNewIngredient({ name: '', quantity: 1, unit: 'pieces' });
    } catch (err) {
      console.error('Error adding ingredient:', err);
      setError('Failed to add ingredient. Please try again.');
    }
  };

  const handleGetRecipe = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`/api/v1/recipes/suggest?servings=${servings}`);
      setRecipe(response.data);
      setActiveTab('suggestions');
    } catch (err) {
      console.error('Error getting recipe suggestion:', err);
      setError('Failed to get recipe suggestions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <ChefHat className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Chef Bot</h1>
              <p className="text-sm text-gray-500">Your AI-powered cooking assistant</p>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('inventory')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'inventory'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Kitchen Inventory
            </button>
            <button
              onClick={() => setActiveTab('suggestions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'suggestions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Recipe Suggestions
            </button>
          </div>
        </div>
      </nav>

      {/* Error message */}
      {error && (
        <div className="max-w-5xl mx-auto px-4 py-2 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {activeTab === 'inventory' ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Available Ingredients</h2>
              <p className="mt-1 text-sm text-gray-500">Manage your kitchen inventory</p>
            </div>

            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading ingredients...</div>
            ) : (
              <div className="divide-y divide-gray-200">
                {ingredients.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    No ingredients yet. Add some to get started!
                  </div>
                ) : (
                  ingredients.map((ingredient) => (
                    <div 
                      key={ingredient.id}
                      className="flex items-center p-4 hover:bg-gray-50 transition-colors"
                    >
                      <span className="flex-1 text-gray-900">{ingredient.name}</span>
                      
                      <div className="flex items-center gap-3">
                        <div className="flex items-center bg-gray-50 rounded-lg border">
                          <button
                            onClick={() => handleQuantityChange(ingredient.id, false)}
                            className="p-1 hover:bg-gray-100 rounded-l-lg transition-colors"
                          >
                            <ChevronDown size={16} />
                          </button>
                          
                          <span className="w-12 text-center text-gray-700">{ingredient.quantity}</span>
                          
                          <button
                            onClick={() => handleQuantityChange(ingredient.id, true)}
                            className="p-1 hover:bg-gray-100 rounded-r-lg transition-colors"
                          >
                            <ChevronUp size={16} />
                          </button>
                        </div>

                        <select
                          value={ingredient.unit}
                          onChange={(e) => handleUnitChange(ingredient.id, e.target.value)}
                          className="border rounded-lg px-3 py-1.5 text-sm bg-white text-gray-700 appearance-none cursor-pointer hover:bg-gray-50 transition-colors"
                        >
                          {units.map(unit => (
                            <option key={unit} value={unit}>{unit}</option>
                          ))}
                        </select>

                        <button
                          onClick={() => handleDelete(ingredient.id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    </div>
                  ))
                )}

                <div className="p-4">
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={newIngredient.name}
                      onChange={(e) => setNewIngredient({ ...newIngredient, name: e.target.value })}
                      placeholder="Add new ingredient"
                      className="flex-1 border rounded-lg px-4 py-2 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={handleAddIngredient}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                    >
                      <Plus size={20} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Recipe Suggestions</h2>
              <p className="mt-1 text-sm text-gray-500">Get recipe ideas based on your ingredients</p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">Number of Servings</label>
              <div className="flex gap-3 items-center">
                <select
                  value={servings}
                  onChange={(e) => setServings(parseInt(e.target.value))}
                  className="border rounded-lg px-3 py-2 text-gray-700 bg-white"
                >
                  {[2, 4, 6, 8].map(num => (
                    <option key={num} value={num}>{num} servings</option>
                  ))}
                </select>
                <button
                  onClick={handleGetRecipe}
                  disabled={loading || ingredients.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Loading...' : 'Get Recipe Suggestion'}
                </button>
              </div>
              {ingredients.length === 0 && (
                <p className="mt-2 text-sm text-amber-600">Add some ingredients first to get recipe suggestions</p>
              )}
            </div>

            {recipe ? (
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-blue-50 p-4 border-b">
                  <h3 className="text-xl font-bold text-gray-900">{recipe.recipe_name}</h3>
                  <p className="text-sm text-gray-500">Serves {recipe.servings} • {recipe.cooking_time} min • {recipe.difficulty_level} difficulty</p>
                </div>
                
                <div className="p-4 space-y-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Ingredients</h4>
                    <ul className="space-y-1">
                      {recipe.ingredients_required.map((ingredient, idx) => (
                        <li key={idx} className="text-gray-700">• {ingredient}</li>
                      ))}
                    </ul>
                  </div>
                  
                  {recipe.missing_ingredients.length > 0 && (
                    <div>
                      <h4 className="font-medium text-amber-600 mb-2">Missing Ingredients</h4>
                      <ul className="space-y-1">
                        {recipe.missing_ingredients.map((ingredient, idx) => (
                          <li key={idx} className="text-amber-600">• {ingredient}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Instructions</h4>
                    <ol className="space-y-2 list-decimal list-inside">
                      {recipe.instructions.map((step, idx) => (
                        <li key={idx} className="text-gray-700">{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center flex-col gap-4 text-gray-400 py-12">
                <Book size={48} />
                <p className="text-lg">Get recipe suggestions based on your ingredients</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
