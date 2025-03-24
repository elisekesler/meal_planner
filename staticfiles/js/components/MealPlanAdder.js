import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';

const MealPlanAdder = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [recipes, setRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedDay, setSelectedDay] = useState('Day 1');
  const [servings, setServings] = useState(1);
  
  useEffect(() => {
    // Get all recipes from the all_recipes context variable
    const recipesData = window.allRecipes || [];
    setRecipes(recipesData);
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredRecipes([]);
      return;
    }

    const filtered = recipes.filter(recipe =>
      recipe.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredRecipes(filtered);
  }, [searchTerm, recipes]);

  const handleAddRecipe = async (recipe) => {
    try {
      const response = await fetch('/api/add-to-meal-plan/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: JSON.stringify({
          recipe_id: recipe.id,
          day: selectedDay.split(' ')[1], // Extract number from "Day X"
          servings: servings
        }),
      });

      if (response.ok) {
        // Refresh the page to show updated meal plan
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding recipe:', error);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div className="mb-4 flex gap-4">
        <div className="relative flex-1">
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              placeholder="Search for recipes..."
              className="w-full p-2 pr-8 border rounded shadow-sm"
            />
            <Search className="absolute right-2 top-2.5 h-5 w-5 text-gray-400" />
          </div>
          
          {showDropdown && filteredRecipes.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border rounded shadow-lg">
              {filteredRecipes.map((recipe) => (
                <div
                  key={recipe.id}
                  className="p-2 hover:bg-gray-100 cursor-pointer"
                  onClick={() => {
                    setSearchTerm(recipe.name);
                    setShowDropdown(false);
                  }}
                >
                  {recipe.name}
                </div>
              ))}
            </div>
          )}
        </div>

        <select
          value={selectedDay}
          onChange={(e) => setSelectedDay(e.target.value)}
          className="p-2 border rounded shadow-sm"
        >
          {Array.from({ length: 7 }, (_, i) => (
            <option key={i + 1} value={`Day ${i + 1}`}>
              Day {i + 1}
            </option>
          ))}
        </select>

        <input
          type="number"
          value={servings}
          onChange={(e) => setServings(parseInt(e.target.value) || 1)}
          min="1"
          className="p-2 border rounded shadow-sm w-24"
          placeholder="Servings"
        />
      </div>

      <button
        onClick={() => {
          const recipe = recipes.find(r => r.name === searchTerm);
          if (recipe) {
            handleAddRecipe(recipe);
          }
        }}
        className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        disabled={!recipes.some(r => r.name === searchTerm)}
      >
        Add Recipe to Meal Plan
      </button>
    </div>
  );
};

export default MealPlanAdder;