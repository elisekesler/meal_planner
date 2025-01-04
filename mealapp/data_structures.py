# mealapp/data_structures.py

aisles_list = ['N/A', 'Produce', 'Pantry', 'Grains', 'Eggs/Dairy', 'Spreads', 'Frozen', 'Spices']

class Ingredient:
    def __init__(self, name, aisle):
        self.name = name
        self.aisle = aisle

    def __str__(self):
        return f"{self.name} (Aisle: {self.aisle})"


class Recipe:
    def __init__(
        self,
        name,
        ingredients,
        instructions,
        calories_per_serving,
        servings,
        fat_per_serving=0,
        carbs_per_serving=0,
        protein_per_serving=0
    ):
        self.name = name
        self.ingredients = ingredients  # {Ingredient: "2 unit", ...}
        self.instructions = instructions
        self.calories_per_serving = calories_per_serving
        self.fat_per_serving = fat_per_serving
        self.carbs_per_serving = carbs_per_serving
        self.protein_per_serving = protein_per_serving
        self.servings = servings


class MealPlan:
    def __init__(self):
        self.days = {f"Day {i}": [] for i in range(1, 8)}

    def add_recipe(self, recipe, day):
        day_key = f"Day {day}"
        self.days[day_key].append(recipe)

    def calculate_nutrition(self):
        totals = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        for day_recipes in self.days.values():
            for recipe in day_recipes:
                totals["calories"] += recipe.calories_per_serving * recipe.servings
                totals["protein"] += recipe.protein_per_serving * recipe.servings
                totals["fat"] += recipe.fat_per_serving * recipe.servings
                totals["carbs"] += recipe.carbs_per_serving * recipe.servings
        return totals


class GroceryList:
    def __init__(self):
        self.recipes = []
        self.grocery_items = {}

    def add_recipe(self, recipe, servings):
        self.recipes.append((recipe, servings))
        factor = servings / recipe.servings

        for ingredient, measurement in recipe.ingredients.items():
            amount_str, unit = measurement.split(" ", 1)  # e.g., "2 unit" -> ["2", "unit"]
            amount = float(amount_str) * factor

            if ingredient.name not in self.grocery_items:
                self.grocery_items[ingredient.name] = {
                    "ingredient": ingredient,
                    "units": {}
                }
            if unit in self.grocery_items[ingredient.name]["units"]:
                self.grocery_items[ingredient.name]["units"][unit] += amount
            else:
                self.grocery_items[ingredient.name]["units"][unit] = amount
