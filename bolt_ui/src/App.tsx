import React, { useState } from 'react';
import { X, ChevronUp, ChevronDown, Plus, ChefHat, Book } from 'lucide-react';

interface Ingredient {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  editable: boolean;
}

function App() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [activeTab, setActiveTab] = useState('inventory');

  const [newIngredient, setNewIngredient] = useState({
    name: '',
    quantity: 1,
    unit: 'pieces'
  });

  const units = ['pieces', 'ml', 'g', 'kg', 'tbsp', 'tsp', 'cup'];

  const handleQuantityChange = (id: number, increment: boolean) => {
    setIngredients(ingredients.map(ing => {
      if (ing.id === id) {
        return {
          ...ing,
          quantity: increment ? ing.quantity + 1 : Math.max(1, ing.quantity - 1)
        };
      }
      return ing;
    }));
  };

  const handleUnitChange = (id: number, newUnit: string) => {
    setIngredients(ingredients.map(ing => 
      ing.id === id ? { ...ing, unit: newUnit } : ing
    ));
  };

  const handleDelete = (id: number) => {
    setIngredients(ingredients.filter(ing => ing.id !== id));
  };

  const handleAddIngredient = () => {
    if (newIngredient.name.trim()) {
      setIngredients([
        ...ingredients,
        {
          id: Date.now(),
          ...newIngredient,
          editable: true
        }
      ]);
      setNewIngredient({ name: '', quantity: 1, unit: 'pieces' });
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

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {activeTab === 'inventory' ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Available Ingredients</h2>
              <p className="mt-1 text-sm text-gray-500">Manage your kitchen inventory</p>
            </div>

            <div className="divide-y divide-gray-200">
              {ingredients.map((ingredient) => (
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

                    {ingredient.editable && (
                      <button
                        onClick={() => handleDelete(ingredient.id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))}

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
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-center flex-col gap-4 text-gray-400 py-12">
              <Book size={48} />
              <p className="text-lg">Recipe suggestions coming soon!</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;