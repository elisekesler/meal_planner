# mealapp/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .data_structures import (
    aisles_list, Ingredient, Recipe, MealPlan, GroceryList
)

# Global in-memory storage:
RECIPES = {}        # {recipe_name: Recipe}
MEAL_PLAN = MealPlan()


def home(request):
    """
    A simple home page with links to other views.
    """
    return render(request, "base.html")


def add_recipe(request):
    """
    GET: Show form to add a new recipe.
    POST: Process form data and create a Recipe object in memory.
    """
    if request.method == "POST":
        recipe_name = request.POST.get("recipe_name", "")
        ingredients_input = request.POST.get("ingredients", "")
        instructions = request.POST.get("instructions", "")
        calories = float(request.POST.get("calories", 0.0))
        fat = float(request.POST.get("fat", 0.0))
        carbs = float(request.POST.get("carbs", 0.0))
        protein = float(request.POST.get("protein", 0.0))
        servings = int(request.POST.get("servings", 1))

        # Parse ingredients
        ing_dict = {}
        if ingredients_input.strip():
            items = ingredients_input.split(",")
            for item in items:
                item = item.strip()
                parts = item.split("-", 2)  # e.g. "Onion-1-2 unit"
                if len(parts) == 3:
                    ing_name = parts[0].strip()
                    ing_aisle = int(parts[1].strip())
                    measurement = parts[2].strip()
                    ing_dict[Ingredient(ing_name, ing_aisle)] = measurement

        # Create and store the Recipe
        new_recipe = Recipe(
            name=recipe_name,
            ingredients=ing_dict,
            instructions=instructions,
            calories_per_serving=calories,
            servings=servings,
            fat_per_serving=fat,
            carbs_per_serving=carbs,
            protein_per_serving=protein
        )
        RECIPES[recipe_name] = new_recipe

        # Redirect to a page that shows all recipes, or back to the form
        return redirect("view_recipes")

    return render(request, "add_recipe.html")


def view_recipes(request):
    """
    Show all saved recipes and their details.
    """
    context = {
        "recipes": RECIPES
    }
    return render(request, "view_recipes.html", context)


def meal_plan(request):
    """
    GET: Show a form with a dropdown of recipes and day selection.
    POST: Add selected recipe to selected day in the meal plan.
    """
    if request.method == "POST":
        recipe_name = request.POST.get("recipe_name", "")
        day_str = request.POST.get("day", "1")

        if recipe_name in RECIPES:
            day_num = int(day_str)
            MEAL_PLAN.add_recipe(RECIPES[recipe_name], day_num)

        return redirect("meal_plan")  # Refresh the page

    # Calculate total nutrition
    totals = MEAL_PLAN.calculate_nutrition()

    context = {
        "recipes_list": list(RECIPES.keys()),
        "meal_plan": MEAL_PLAN.days,
        "totals": totals
    }
    return render(request, "meal_plan.html", context)


def grocery_list(request):
    """
    Build a GroceryList from the meal plan and display it by aisle.
    """
    g_list = GroceryList()

    # Add all recipes in the meal plan
    for day_recipes in MEAL_PLAN.days.values():
        for recipe in day_recipes:
            g_list.add_recipe(recipe, servings=recipe.servings)

    # Group by aisle for display
    categorized = {}
    for item in g_list.grocery_items.values():
        ingredient = item["ingredient"]
        aisle = ingredient.aisle
        if aisle not in categorized:
            categorized[aisle] = []
        categorized[aisle].append((ingredient.name, item["units"]))

    context = {
        "categorized": categorized,
        "aisles_list": aisles_list,
    }
    return render(request, "grocery_list.html", context)
