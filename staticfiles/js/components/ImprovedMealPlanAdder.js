import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Calendar, Users } from 'lucide-react';

const ImprovedMealPlanAdder = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [recipes, setRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedDay, setSelectedDay] = useState('1');
  const [servings, setServings] = useState(1);
  const dropdownRef = useRef(null);
  const searchInputRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          searchInputRef.current && !searchInputRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    // Get all recipes from the all_recipes context variable
    const recipesData = window.allRecipes || [];
    setRecipes(recipesData);
    // Show all recipes by default
    setFilteredRecipes(recipesData);
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      // Show all recipes when search is empty
      setFilteredRecipes(recipes);
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
          day: selectedDay, // Extract number from "Day X"
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
    <div className="w-full max-w-3xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h3 className="text-xl font-bold mb-4">Add Recipe to Meal Plan</h3>

      <div className="mb-6 space-y-4">
        {/* Recipe Search */}
        <div className="relative">
          <label className="block text-sm font-medium mb-2">Select Recipe</label>
          <div className="relative" ref={searchInputRef}>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => setShowDropdown(true)}
              placeholder="Search or select a recipe..."
              className="w-full p-4 pl-12 pr-10 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
            />
            <Search className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
            <ChevronDown
              className="absolute right-4 top-4 h-6 w-6 text-gray-500 cursor-pointer"
              onClick={() => setShowDropdown(!showDropdown)}
            />
          </div>

          {showDropdown && (
            <div
              ref={dropdownRef}
              className="absolute z-10 w-full mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
            >
              {filteredRecipes.length > 0 ? (
                filteredRecipes.map((recipe) => (
                  <div
                    key={recipe.id}
                    className="p-4 hover:bg-blue-50 cursor-pointer border-b border-gray-100 text-lg"
                    onClick={() => {
                      setSearchTerm(recipe.name);
                      setShowDropdown(false);
                    }}
                  >
                    <div className="font-medium">{recipe.name}</div>
                    <div className="text-sm text-gray-500">{recipe.calories_per_serving} calories per serving</div>
                  </div>
                ))
              ) : (
                <div className="p-4 text-gray-500">No recipes found</div>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-4">
          {/* Day Selection */}
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Day</label>
            <div className="relative">
              <select
                value={selectedDay}
                onChange={(e) => setSelectedDay(e.target.value)}
                className="w-full appearance-none p-4 pl-12 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              >
                {Array.from({ length: 7 }, (_, i) => (
                  <option key={i + 1} value={String(i + 1)}>
                    Day {i + 1}
                  </option>
                ))}
              </select>
              <Calendar className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
              <ChevronDown className="absolute right-4 top-4 h-6 w-6 text-gray-500 pointer-events-none" />
            </div>
          </div>

          {/* Servings Selection */}
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Servings</label>
            <div className="relative">
              <input
                type="number"
                value={servings}
                onChange={(e) => setServings(parseInt(e.target.value) || 1)}
                min="1"
                className="w-full p-4 pl-12 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              />
              <Users className="absolute left-4 top-4 h-6 w-6 text-gray-500" />
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={() => {
          const recipe = recipes.find(r => r.name === searchTerm);
          if (recipe) {
            handleAddRecipe(recipe);
          }
        }}
        className="w-full p-4 text-lg bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
        disabled={!recipes.some(r => r.name === searchTerm)}
      >
        Add Recipe to Meal Plan
      </button>
    </div>
  );
};

export default ImprovedMealPlanAdder;