import React, { useState } from 'react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';

const AddRecipeForm = () => {
  const [showNewIngredientDialog, setShowNewIngredientDialog] = useState(false);
  const [pendingIngredient, setPendingIngredient] = useState({ name: '', amount: '', unit: '' });
  const [newIngredientForm, setNewIngredientForm] = useState({
    name: '',
    aisle: '0',
    calories_per_unit: '',
    protein_per_unit: '',
    carbs_per_unit: '',
    fat_per_unit: ''
  });

  const checkIngredient = async (name) => {
    try {
      const response = await fetch(`/api/check-ingredient/${encodeURIComponent(name)}`);
      const exists = await response.json();
      if (!exists) {
        setShowNewIngredientDialog(true);
      }
    } catch (error) {
      console.error('Error checking ingredient:', error);
    }
  };

  const handleIngredientBlur = (e) => {
    const ingredientName = e.target.value;
    if (ingredientName) {
      checkIngredient(ingredientName);
    }
  };

  const handleAddNewIngredient = async () => {
    try {
      const response = await fetch('/api/ingredients/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newIngredientForm)
      });

      if (response.ok) {
        setShowNewIngredientDialog(false);
        // Reset form
        setNewIngredientForm({
          name: '',
          aisle: '0',
          calories_per_unit: '',
          protein_per_unit: '',
          carbs_per_unit: '',
          fat_per_unit: ''
        });
      }
    } catch (error) {
      console.error('Error adding ingredient:', error);
    }
  };

  return (
    <div className="p-4">
      <div className="ingredient-row space-x-2">
        <input
          type="text"
          className="border p-2 rounded"
          placeholder="Ingredient name"
          onBlur={handleIngredientBlur}
        />
        <input
          type="number"
          className="border p-2 rounded"
          placeholder="Amount"
        />
        <select className="border p-2 rounded">
          <option value="" disabled selected>Select unit</option>
          <option value="g">g</option>
          <option value="ml">ml</option>
          <option value="cup">cup</option>
          <option value="tbsp">tbsp</option>
        </select>
      </div>

      <AlertDialog open={showNewIngredientDialog} onOpenChange={setShowNewIngredientDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>New Ingredient</AlertDialogTitle>
            <AlertDialogDescription>
              This ingredient is not in the database. Would you like to add it?
            </AlertDialogDescription>
          </AlertDialogHeader>
          {showNewIngredientDialog && (
            <div className="space-y-4 mt-4">
              <input
                type="text"
                className="w-full border p-2 rounded"
                placeholder="Ingredient name"
                value={newIngredientForm.name}
                onChange={e => setNewIngredientForm({...newIngredientForm, name: e.target.value})}
              />
              <select
                className="w-full border p-2 rounded"
                value={newIngredientForm.aisle}
                onChange={e => setNewIngredientForm({...newIngredientForm, aisle: e.target.value})}
              >
                <option value="0">N/A</option>
                <option value="1">Produce</option>
                <option value="2">Pantry</option>
                <option value="3">Grains</option>
                <option value="4">Eggs/Dairy</option>
                <option value="5">Spreads</option>
                <option value="6">Frozen</option>
                <option value="7">Spices</option>
                <option value="8">Meats</option>
              </select>
              <input
                type="number"
                className="w-full border p-2 rounded"
                placeholder="Calories per unit"
                value={newIngredientForm.calories_per_unit}
                onChange={e => setNewIngredientForm({...newIngredientForm, calories_per_unit: e.target.value})}
              />
              <input
                type="number"
                className="w-full border p-2 rounded"
                placeholder="Protein per unit"
                value={newIngredientForm.protein_per_unit}
                onChange={e => setNewIngredientForm({...newIngredientForm, protein_per_unit: e.target.value})}
              />
              <input
                type="number"
                className="w-full border p-2 rounded"
                placeholder="Carbs per unit"
                value={newIngredientForm.carbs_per_unit}
                onChange={e => setNewIngredientForm({...newIngredientForm, carbs_per_unit: e.target.value})}
              />
              <input
                type="number"
                className="w-full border p-2 rounded"
                placeholder="Fat per unit"
                value={newIngredientForm.fat_per_unit}
                onChange={e => setNewIngredientForm({...newIngredientForm, fat_per_unit: e.target.value})}
              />
            </div>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleAddNewIngredient}>Add Ingredient</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AddRecipeForm;