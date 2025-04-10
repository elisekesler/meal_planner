import React, { useState, useEffect, useRef } from 'react';

// This is a standalone component without external icon libraries
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
          day: selectedDay,
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
    <div className="search-container">
      <h3 className="search-title">Add Recipe to Meal Plan</h3>

      <div className="form-group">
        <label className="form-label">Select Recipe</label>
        <div className="search-input-wrapper" ref={searchInputRef}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setShowDropdown(true)}
            placeholder="Search or select a recipe..."
            className="search-input"
          />
          <button
            className="dropdown-toggle"
            onClick={() => setShowDropdown(!showDropdown)}
            type="button"
          >
            ▼
          </button>
        </div>

        {showDropdown && (
          <div
            ref={dropdownRef}
            className="search-dropdown"
          >
            {filteredRecipes.length > 0 ? (
              filteredRecipes.map((recipe) => (
                <div
                  key={recipe.id}
                  className="dropdown-item"
                  onClick={() => {
                    setSearchTerm(recipe.name);
                    setShowDropdown(false);
                  }}
                >
                  <div className="recipe-name">{recipe.name}</div>
                  <div className="recipe-calories">{recipe.calories_per_serving} calories per serving</div>
                </div>
              ))
            ) : (
              <div className="dropdown-item">No recipes found</div>
            )}
          </div>
        )}
      </div>

      <div className="form-row">
        {/* Day Selection */}
        <div className="form-col">
          <label className="form-label">Day</label>
          <select
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="select-input"
          >
            {Array.from({ length: 7 }, (_, i) => (
              <option key={i + 1} value={String(i + 1)}>
                Day {i + 1}
              </option>
            ))}
          </select>
        </div>

        {/* Servings Selection */}
        <div className="form-col">
          <label className="form-label">Servings</label>
          <input
            type="number"
            value={servings}
            onChange={(e) => setServings(parseInt(e.target.value) || 1)}
            min="1"
            className="number-input"
          />
        </div>
      </div>

      <div className="form-group" style={{marginTop: '16px'}}>
        <button
          onClick={() => {
            const recipe = recipes.find(r => r.name === searchTerm);
            if (recipe) {
              handleAddRecipe(recipe);
            }
          }}
          className="submit-button"
          disabled={!recipes.some(r => r.name === searchTerm)}
          type="button"
        >
          Add Recipe to Meal Plan
        </button>
      </div>
    </div>
  );
};

export default ImprovedMealPlanAdder;