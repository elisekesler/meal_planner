# mealapp/data_structures.py

# aisles_list = ['N/A', 'Produce', 'Pantry', 'Grains', 'Eggs/Dairy', 'Spreads', 'Frozen', 'Spices']

aisles_list = {
    0: "N/A",
    1: "Produce",
    2: "Pantry",
    3: "Grains",
    4: "Eggs/Dairy",
    5: "Spreads",
    6: "Frozen",
    7: "Spices",
    8: "Meats",
}
# class Ingredient:
#     def __init__(self, name, aisle):
#         self.name = name
#         self.aisle = aisle

#     def __str__(self):
#         return f"{self.name} (Aisle: {self.aisle})"


# class Recipe:
#     def __init__(
#         self,
#         name,
#         ingredients,
#         instructions,
#         calories_per_serving,
#         servings,
#         fat_per_serving=0,
#         carbs_per_serving=0,
#         protein_per_serving=0
#     ):
#         self.name = name
#         self.ingredients = ingredients  # {Ingredient: "2 unit", ...}
#         self.instructions = instructions
#         self.calories_per_serving = calories_per_serving
#         self.fat_per_serving = fat_per_serving
#         self.carbs_per_serving = carbs_per_serving
#         self.protein_per_serving = protein_per_serving
#         self.servings = servings


# data_structures.py

class MealPlan:
    def __init__(self):
        self.days = {f"Day {i}": [] for i in range(1, 8)}

    def add_recipe(self, recipe_obj, day):
        day_key = f"Day {day}"
        print(f"Adding recipe {recipe_obj.name} to {day_key}")
        if day_key in self.days:
            self.days[day_key].append(recipe_obj)
            print(f"Current recipes for {day_key}: {[r.name for r in self.days[day_key]]}")
        else:
            print(f"Invalid day key: {day_key}")

    def calculate_nutrition(self):
        totals = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        for day_recipes in self.days.values():
            for recipe_obj in day_recipes:
                totals["calories"] += recipe_obj.calories_per_serving * recipe_obj.servings
                totals["protein"] += recipe_obj.protein_per_serving * recipe_obj.servings
                totals["fat"] += recipe_obj.fat_per_serving * recipe_obj.servings
                totals["carbs"] += recipe_obj.carbs_per_serving * recipe_obj.servings
        return totals


class GroceryList:
    def __init__(self):
        self.recipes = []
        self.grocery_items = {}  # { "Flour": {"ingredient": <DB Ingredient>, "units": {"cup": 2.0} }, ... }

    def add_recipe(self, recipe_obj, servings):
        # recipe_obj is a DB recipe, but you still need to gather
        # ingredients from its ManyToMany or RecipeIngredient table
        self.recipes.append((recipe_obj, servings))

        # e.g., factor = servings / recipe_obj.servings if you want scaling
        factor = servings / recipe_obj.servings

        # Then get all the related ingredients from your many-to-many approach:
        # e.g., recipe_obj.recipe_ingredients.all()
        # each has .ingredient, .amount, .unit
        for ri in recipe_obj.recipe_ingredients.all():
            ing = ri.ingredient  # a DB Ingredient object
            # e.g. parse ri.amount if needed. For now, assume it's numeric:
            try:
                base_amount = float(ri.amount)
            except ValueError:
                base_amount = 1.0
            scaled_amount = base_amount * factor

            if ing.name not in self.grocery_items:
                self.grocery_items[ing.name] = {
                    "ingredient": ing,
                    "units": {}
                }

            # If you're storing "unit" in ri.unit
            if ri.unit in self.grocery_items[ing.name]["units"]:
                self.grocery_items[ing.name]["units"][ri.unit] += scaled_amount
            else:
                self.grocery_items[ing.name]["units"][ri.unit] = scaled_amount
