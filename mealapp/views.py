from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Recipe, Ingredient, RecipeIngredient
from django.db.models import Sum
from .data_structures import MealPlan, GroceryList, aisles_list
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
import json
from django.views.decorators.http import require_http_methods
from django.core.serializers import serialize

MEAL_PLAN = MealPlan()

def home(request):
    """
    A simple home page with links to other views.
    """
    return render(request, "base.html")

# mealapp/views.py - modify ingredient_detail
def ingredient_detail(request, ingredient_name):
    try:
        ingredient = Ingredient.objects.get(name__iexact=ingredient_name.strip())
        unit = request.GET.get('unit', ingredient.base_unit)
        amount = float(request.GET.get('amount', 1))

        converted_amount = ingredient.get_converted_amount(amount, unit)

        data = {
            "success": True,
            "calories": float(ingredient.calories_per_unit or 0) * converted_amount,
            "protein": float(ingredient.protein_per_unit or 0) * converted_amount,
            "carbs": float(ingredient.carbs_per_unit or 0) * converted_amount,
            "fat": float(ingredient.fat_per_unit or 0) * converted_amount,
        }
    except Ingredient.DoesNotExist:
        data = {"success": False, "error": "Ingredient not found"}
    return JsonResponse(data)

def check_ingredient(request, name):
    exists = Ingredient.objects.filter(name__iexact=name).exists()
    return JsonResponse(exists, safe=False)

def get_meal_plan(request):
    """Get the meal plan from the session, or create a new one if it doesn't exist"""
    if 'meal_plan' not in request.session:
        # Update the structure to store both recipe_id and servings
        request.session['meal_plan'] = {str(i): [] for i in range(1, 8)}
    return request.session['meal_plan']

@require_http_methods(["POST"])
def add_to_meal_plan(request):
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')
        day = str(data.get('day', '1'))  # Convert to string for consistency
        servings = int(data.get('servings', 1))
        recipe = Recipe.objects.get(id=recipe_id)
        print(f"Adding recipe: {recipe.name} (ID: {recipe_id}) to day {day} with {servings} servings")

        # Get the meal plan from session
        meal_plan = get_meal_plan(request)
        print(f"Current meal plan before adding: {meal_plan}")

        # Store recipe ID and servings as a dictionary
        if day not in meal_plan:
            meal_plan[day] = []
        meal_plan[day].append({
            'recipe_id': recipe_id,
            'servings': servings
        })

        # Save back to session
        request.session['meal_plan'] = meal_plan
        request.session.modified = True
        print(f"Updated meal plan: {meal_plan}")

        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error in add_to_meal_plan: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def meal_plan_view(request):
    print("\n--- Starting meal_plan_view ---")
    num_people = int(request.POST.get("num_people", 1)) if request.method == "POST" else 1

    # Get meal plan from session
    meal_plan = get_meal_plan(request)
    print(f"Retrieved meal plan from session: {meal_plan}")

    meal_plan_with_details = {}
    totals = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

    # Process each day
    for day, recipes in meal_plan.items():
        day_key = f"Day {day}"
        print(f"\nProcessing {day_key} with recipes: {recipes}")
        meal_plan_with_details[day_key] = []

        for recipe_data in recipes:
            try:
                recipe_id = recipe_data['recipe_id']
                recipe_servings = recipe_data['servings']
                recipe = Recipe.objects.get(id=recipe_id)
                print(f"Found recipe: {recipe.name} with {recipe_servings} servings")

                # Calculate serving multiplier
                serving_multiplier = (recipe_servings * num_people) / recipe.servings

                ingredients = []
                for ri in recipe.recipe_ingredients.all():
                    # Scale ingredient amounts by serving multiplier
                    scaled_amount = ri.amount * serving_multiplier
                    ingredients.append({
                        "name": ri.ingredient.name,
                        "amount": scaled_amount,
                        "unit": ri.unit,
                    })

                meal_plan_with_details[day_key].append({
                    "recipe": recipe,
                    "ingredients": ingredients,
                    "servings": recipe_servings * num_people  # Total servings for all people
                })

                # Update totals with scaled nutrition values
                totals["calories"] += recipe.calories_per_serving * recipe_servings * num_people
                totals["protein"] += recipe.protein_per_serving * recipe_servings * num_people
                totals["fat"] += recipe.fat_per_serving * recipe_servings * num_people
                totals["carbs"] += recipe.carbs_per_serving * recipe_servings * num_people

            except Recipe.DoesNotExist:
                print(f"Recipe with id {recipe_id} not found")
                continue
            except KeyError as e:
                print(f"Missing key in recipe data: {e}")
                continue

    print(f"\nFinal meal_plan_with_details: {meal_plan_with_details}")

    # Get all recipes for the dropdown
    all_recipes = Recipe.objects.all()
    recipes_data = []
    for recipe in all_recipes:
        recipes_data.append({
            'id': recipe.id,
            'name': recipe.name,
            'servings': recipe.servings,
            'calories_per_serving': recipe.calories_per_serving,
        })

    context = {
        "meal_plan": meal_plan_with_details,
        "totals": totals,
        "all_recipes": json.dumps(recipes_data),
        "num_people": num_people,
    }

    print(f"\nRendering template with context: {context}")
    return render(request, "meal_plan.html", context)
@csrf_exempt
def add_ingredient(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ingredient = Ingredient.objects.create(
            name=data['name'],
            aisle=int(data['aisle']),
            calories_per_unit=float(data['calories_per_unit'] or 0),
            protein_per_unit=float(data['protein_per_unit'] or 0),
            carbs_per_unit=float(data['carbs_per_unit'] or 0),
            fat_per_unit=float(data['fat_per_unit'] or 0)
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def add_ingredient(request):
    """
    Handles the creation of a new ingredient in the database.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        aisle = request.POST.get("aisle", "").strip()


        calories = request.POST.get("calories_per_unit", "")
        protein = request.POST.get("protein_per_unit", "")
        carbs = request.POST.get("carbs_per_unit", "")
        fat = request.POST.get("fat_per_unit", "")

        # Validate input
        if not name:
            return render(request, "add_ingredient.html", {
                "error": "Ingredient name is required.",
                "aisles_list": aisles_list.values(),  # Pass aisle names
            })

        try:
            # Convert aisle name back to index for storage
            aisle_index = next((index for index, value in aisles_list.items() if value == aisle), 0)
            # Convert nutrition values to float if they're not empty
            defaults = {
                "aisle": aisle_index,
                "calories_per_unit": float(calories) if calories.strip() else None,
                "protein_per_unit": float(protein) if protein.strip() else None,
                "carbs_per_unit": float(carbs) if carbs.strip() else None,
                "fat_per_unit": float(fat) if fat.strip() else None,
            }

            Ingredient.objects.get_or_create(name=name, defaults=defaults)
            return redirect("view_ingredients")
        except ValueError:
            return render(request, "add_ingredient.html", {
                "error": "Invalid aisle selected.",
                "aisles_list": aisles_list.values(),  # Pass aisle names
            })

    # Pass aisle names for dropdown
    return render(request, "add_ingredient.html", {"aisles_list": aisles_list.items()})


# mealapp/views.py
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe.delete()
    return redirect('view_recipes')
# mealapp/views.py - add this function
def delete_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    ingredient.delete()
    return redirect('view_ingredients')
# mealapp/views.py - modify view_ingredients function
def view_ingredients(request):
    if request.method == "POST":
        if "delete" in request.POST:
            ingredient_id = request.POST.get("ingredient_id")
            Ingredient.objects.filter(id=ingredient_id).delete()
        else:
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = Ingredient.objects.get(id=ingredient_id)
            ingredient.calories_per_unit = request.POST.get("calories_per_unit")
            ingredient.protein_per_unit = request.POST.get("protein_per_unit")
            ingredient.carbs_per_unit = request.POST.get("carbs_per_unit")
            ingredient.fat_per_unit = request.POST.get("fat_per_unit")
            ingredient.save()

    ingredients = Ingredient.objects.all()
    return render(request, "view_ingredients.html", {"ingredients": ingredients})

def generate_grocery_list(request):
    if request.method == "POST":
        num_people = int(request.POST.get("num_people", 1))
        g_list = GroceryList()

        for day_recipes in MEAL_PLAN.days.values():
            for recipe in day_recipes:
                g_list.add_recipe(recipe, servings=recipe.servings)

        categorized = {}
        for item in g_list.grocery_items.values():
            ing = item["ingredient"]
            aisle = ing.aisle
            if aisle not in categorized:
                categorized[aisle] = []
            categorized[aisle].append((ing.name, {unit: amount * num_people for unit, amount in item["units"].items()}))

        return render(request, "grocery_list_partial.html", {
            "categorized": categorized,
            "aisles_list": aisles_list,
            "num_people": num_people,
        })

    return redirect("meal_plan_view")


def generate_grocery_list(request):
    if request.method == "POST":
        num_people = int(request.POST.get("num_people", 1))
        g_list = GroceryList()

        for day_recipes in MEAL_PLAN.days.values():
            for recipe in day_recipes:
                g_list.add_recipe(recipe, servings=recipe.servings * num_people)

        categorized = {}
        for item in g_list.grocery_items.values():
            ing = item["ingredient"]
            aisle = ing.aisle
            if aisle not in categorized:
                categorized[aisle] = []
            categorized[aisle].append((ing.name, {unit: amount * num_people for unit, amount in item["units"].items()}))

        return render(request, "grocery_list_partial.html", {
            "categorized": categorized,
            "aisles_list": aisles_list,
            "num_people": num_people,
        })

    return redirect("meal_plan_view")


def add_recipe(request):
    """
    Handles adding a recipe with separate ingredient fields.
    """
    if request.method == "POST":
        try:
            recipe_name = request.POST.get("recipe_name", "").strip()
            instructions = request.POST.get("instructions", "").strip()
            servings = int(request.POST.get("servings", 1))

            # Get nutrition values, defaulting to 0 if not provided
            calories = float(request.POST.get("calories") or 0)
            fat = float(request.POST.get("fat") or 0)
            carbs = float(request.POST.get("carbs") or 0)
            protein = float(request.POST.get("protein") or 0)

            if not recipe_name:
                raise ValueError("Recipe name is required")

            # Create the recipe
            new_recipe = Recipe.objects.create(
                name=recipe_name,
                instructions=instructions,
                calories_per_serving=calories,
                fat_per_serving=fat,
                carbs_per_serving=carbs,
                protein_per_serving=protein,
                servings=servings,
            )

            # Process ingredients
            ingredient_names = request.POST.getlist("ingredient_name[]")
            ingredient_amounts = request.POST.getlist("ingredient_amount[]")
            ingredient_units = request.POST.getlist("ingredient_unit[]")

            for i, (name, amount, unit) in enumerate(zip(ingredient_names, ingredient_amounts, ingredient_units)):
                try:
                    if not name.strip():
                        continue
                    ingredient_obj, created = Ingredient.objects.get_or_create(
                        name=name.strip(),
                        defaults={"aisle": 0}
                    )
                    RecipeIngredient.objects.create(
                        recipe=new_recipe,
                        ingredient=ingredient_obj,
                        amount=float(amount),
                        unit=unit,
                    )
                    print(f"Recipe Created: {new_recipe}")
                    print(f"Ingredients: {ingredient_names}, {ingredient_amounts}, {ingredient_units}")

                except ValueError:
                    print(f"Invalid ingredient data: {name}, {amount}, {unit}")
            return redirect("view_recipes")

        except (ValueError, TypeError) as e:
            return render(request, "add_recipe.html", {
                "error": str(e),
                "units": ["cups", "ounces", "teaspoons", "tablespoons", "units", "slices"],
                "ingredients": Ingredient.objects.all(),
            })

    # GET request - display empty form
    return render(request, "add_recipe.html", {
        "units": ["cups", "ounces", "teaspoons", "tablespoons", "units", "slices"],
        "ingredients": Ingredient.objects.all(),
    })

# def meal_plan_view(request):
#     print("\n--- Starting meal_plan_view ---")
#     num_people = int(request.POST.get("num_people", 1)) if request.method == "POST" else 1

#     # Get meal plan from session
#     meal_plan = get_meal_plan(request)
#     print(f"Retrieved meal plan from session: {meal_plan}")

#     meal_plan_with_details = {}
#     totals = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

#     # Process each day
#     for day, recipe_ids in meal_plan.items():
#         print(f"\nProcessing day {day} with recipe IDs: {recipe_ids}")
#         meal_plan_with_details[f"Day {day}"] = []

#         for recipe_id in recipe_ids:
#             try:
#                 recipe = Recipe.objects.get(id=recipe_id)
#                 print(f"Found recipe: {recipe.name}")

#                 ingredients = []
#                 for ri in recipe.recipe_ingredients.all():
#                     ingredients.append({
#                         "name": ri.ingredient.name,
#                         "amount": ri.amount,
#                         "unit": ri.unit,
#                     })

#                 meal_plan_with_details[f"Day {day}"].append({
#                     "recipe": recipe,
#                     "ingredients": ingredients,
#                 })

#                 # Update totals
#                 totals["calories"] += recipe.calories_per_serving * recipe.servings
#                 totals["protein"] += recipe.protein_per_serving * recipe.servings
#                 totals["fat"] += recipe.fat_per_serving * recipe.servings
#                 totals["carbs"] += recipe.carbs_per_serving * recipe.servings

#             except Recipe.DoesNotExist:
#                 print(f"Recipe with id {recipe_id} not found")
#                 continue

#     print(f"\nFinal meal_plan_with_details: {meal_plan_with_details}")

#     # Get all recipes for the dropdown
#     all_recipes = Recipe.objects.all()
#     recipes_data = []
#     for recipe in all_recipes:
#         recipes_data.append({
#             'id': recipe.id,
#             'name': recipe.name,
#             'servings': recipe.servings,
#             'calories_per_serving': recipe.calories_per_serving,
#         })

#     context = {
#         "meal_plan": meal_plan_with_details,
#         "totals": totals,
#         "all_recipes": json.dumps(recipes_data),
#         "num_people": num_people,
#     }
#     print(f"\nRendering template with context: {context}")

#     return render(request, "meal_plan.html", context)
def view_recipes(request):
    """
    Show all saved recipes and their details.
    """
    all_recipes = Recipe.objects.all()
    return render(request, "view_recipes.html", {"recipes": all_recipes})
