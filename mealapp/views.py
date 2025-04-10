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
from .models import UnitConversion

MEAL_PLAN = MealPlan()

def home(request):
    """
    A simple home page with links to other views.
    """
    return render(request, "base.html")

def test_conversion(request):
    """
    Simple page to test unit conversions directly.
    """
    return render(request, "test_conversion.html")
def manage_unit_conversions(request):
    """
    View for managing unit conversions - adding, viewing, and deleting.
    """
    context = {}

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            from_unit = request.POST.get("from_unit", "").strip().lower()
            to_unit = request.POST.get("to_unit", "").strip().lower()
            conversion_factor = request.POST.get("conversion_factor")

            if not from_unit or not to_unit or not conversion_factor:
                context["error"] = "All fields are required."
            else:
                try:
                    conversion_factor = float(conversion_factor)

                    # Check if the conversion already exists
                    existing = UnitConversion.objects.filter(
                        from_unit=from_unit,
                        to_unit=to_unit
                    ).exists()

                    if existing:
                        context["error"] = f"A conversion from {from_unit} to {to_unit} already exists."
                    else:
                        # Create the conversion
                        UnitConversion.objects.create(
                            from_unit=from_unit,
                            to_unit=to_unit,
                            conversion_factor=conversion_factor
                        )

                        # Create the reverse conversion automatically
                        if from_unit != to_unit:  # Avoid creating self-references
                            UnitConversion.objects.create(
                                from_unit=to_unit,
                                to_unit=from_unit,
                                conversion_factor=1.0/conversion_factor
                            )

                        context["success"] = f"Conversion added: 1 {from_unit} = {conversion_factor} {to_unit}"
                except ValueError:
                    context["error"] = "Conversion factor must be a number."

        elif action == "delete":
            conversion_id = request.POST.get("conversion_id")
            try:
                conversion = UnitConversion.objects.get(id=conversion_id)

                # Try to find and delete the reverse conversion too
                try:
                    reverse_conversion = UnitConversion.objects.get(
                        from_unit=conversion.to_unit,
                        to_unit=conversion.from_unit
                    )
                    reverse_conversion.delete()
                except UnitConversion.DoesNotExist:
                    pass  # No reverse conversion found

                conversion.delete()
                context["success"] = "Conversion deleted successfully."
            except UnitConversion.DoesNotExist:
                context["error"] = "Conversion not found."

    # Get all conversions for display
    context["conversions"] = UnitConversion.objects.all()

    return render(request, "unit_conversions.html", context)

def ingredient_detail(request, ingredient_name):
    """
    API endpoint to get ingredient details with unit conversion.
    Enhanced with more detailed debug information.
    """
    try:
        # Try to find the ingredient by name (case-insensitive)
        ingredient = Ingredient.objects.get(name__iexact=ingredient_name.strip())

        # Get the unit and amount from query parameters
        unit = request.GET.get('unit', ingredient.base_unit).lower().strip()
        try:
            amount = float(request.GET.get('amount', 1))
        except (ValueError, TypeError):
            amount = 1.0

        # Print debug info to server logs
        print(f"DEBUG: Converting {amount} {unit} of {ingredient.name} (base unit: {ingredient.base_unit})")

        # Try to find a direct conversion
        direct_conversion = None
        try:
            direct_conversion = UnitConversion.objects.get(
                from_unit=unit,
                to_unit=ingredient.base_unit
            )
            print(f"DEBUG: Found direct conversion: 1 {unit} = {direct_conversion.conversion_factor} {ingredient.base_unit}")
        except UnitConversion.DoesNotExist:
            print(f"DEBUG: No direct conversion found from {unit} to {ingredient.base_unit}")

        # Convert the amount
        try:
            converted_amount = ingredient.get_converted_amount(amount, unit)
            print(f"DEBUG: Converted amount: {converted_amount} {ingredient.base_unit}")

            # Prepare the response data
            data = {
                "success": True,
                "name": ingredient.name,
                "base_unit": ingredient.base_unit,
                "original_unit": unit,
                "original_amount": amount,
                "converted_amount": converted_amount,
                "calories": float(ingredient.calories_per_unit or 0) * converted_amount,
                "protein": float(ingredient.protein_per_unit or 0) * converted_amount,
                "carbs": float(ingredient.carbs_per_unit or 0) * converted_amount,
                "fat": float(ingredient.fat_per_unit or 0) * converted_amount,
            }

            # Add conversion path info
            if direct_conversion:
                data["conversion_info"] = f"Using direct conversion: 1 {unit} = {direct_conversion.conversion_factor} {ingredient.base_unit}"
            elif unit != ingredient.base_unit:
                data["conversion_info"] = "Used multi-step conversion or fallback"

        except Exception as e:
            # Log the conversion error but still return a response with defaults
            print(f"DEBUG: Conversion error: {str(e)}")
            data = {
                "success": True,
                "name": ingredient.name,
                "base_unit": ingredient.base_unit,
                "original_unit": unit,
                "original_amount": amount,
                "warning": "Conversion unavailable, using unconverted values",
                "calories": float(ingredient.calories_per_unit or 0) * amount,
                "protein": float(ingredient.protein_per_unit or 0) * amount,
                "carbs": float(ingredient.carbs_per_unit or 0) * amount,
                "fat": float(ingredient.fat_per_unit or 0) * amount,
            }

    except Ingredient.DoesNotExist:
        data = {
            "success": False,
            "error": f"Ingredient '{ingredient_name}' not found"
        }
    except Exception as e:
        data = {
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }

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
    """
    Handles the creation of a new ingredient in the database.
    Fixed to properly save the base_unit.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        aisle = request.POST.get("aisle", "").strip()
        base_unit = request.POST.get("base_unit", "unit").strip()  # Get base_unit

        calories = request.POST.get("calories_per_unit", "")
        protein = request.POST.get("protein_per_unit", "")
        carbs = request.POST.get("carbs_per_unit", "")
        fat = request.POST.get("fat_per_unit", "")

        # Validate input
        if not name:
            return render(request, "add_ingredient.html", {
                "error": "Ingredient name is required.",
                "aisles_list": aisles_list.items(),  # Pass aisle names
            })

        try:
            # Convert aisle name back to index for storage
            aisle_index = next((index for index, value in aisles_list.items() if value == aisle), 0)
            # Convert nutrition values to float if they're not empty
            defaults = {
                "aisle": aisle_index,
                "base_unit": base_unit,  # Include base_unit here
                "calories_per_unit": float(calories) if calories.strip() else None,
                "protein_per_unit": float(protein) if protein.strip() else None,
                "carbs_per_unit": float(carbs) if carbs.strip() else None,
                "fat_per_unit": float(fat) if fat.strip() else None,
            }

            # Print debug info to server logs
            print(f"DEBUG: Adding ingredient {name} with base_unit: {base_unit}")
            print(f"DEBUG: Defaults: {defaults}")

            ingredient, created = Ingredient.objects.get_or_create(name=name, defaults=defaults)

            # If the ingredient already existed, update the base unit and other fields
            if not created:
                # Update the base unit and other fields
                ingredient.base_unit = base_unit
                ingredient.aisle = aisle_index
                if calories.strip():
                    ingredient.calories_per_unit = float(calories)
                if protein.strip():
                    ingredient.protein_per_unit = float(protein)
                if carbs.strip():
                    ingredient.carbs_per_unit = float(carbs)
                if fat.strip():
                    ingredient.fat_per_unit = float(fat)
                ingredient.save()

                print(f"DEBUG: Updated existing ingredient {name}, base_unit is now: {ingredient.base_unit}")

            return redirect("view_ingredients")
        except ValueError:
            return render(request, "add_ingredient.html", {
                "error": "Invalid input values.",
                "aisles_list": aisles_list.items(),  # Pass aisle names
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


def view_ingredients(request):
    if request.method == "POST":
        if "delete" in request.POST:
            ingredient_id = request.POST.get("ingredient_id")
            Ingredient.objects.filter(id=ingredient_id).delete()
        else:
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = Ingredient.objects.get(id=ingredient_id)

            # Update all fields including base_unit
            base_unit = request.POST.get("base_unit", "unit")
            ingredient.base_unit = base_unit

            # Update nutrition values
            calories = request.POST.get("calories_per_unit", "")
            protein = request.POST.get("protein_per_unit", "")
            carbs = request.POST.get("carbs_per_unit", "")
            fat = request.POST.get("fat_per_unit", "")

            if calories.strip():
                ingredient.calories_per_unit = float(calories)
            if protein.strip():
                ingredient.protein_per_unit = float(protein)
            if carbs.strip():
                ingredient.carbs_per_unit = float(carbs)
            if fat.strip():
                ingredient.fat_per_unit = float(fat)

            ingredient.save()

            # Print debug info
            print(f"DEBUG: Updated ingredient {ingredient.name}, base_unit is now: {ingredient.base_unit}")

    ingredients = Ingredient.objects.all()
    return render(request, "view_ingredients.html", {"ingredients": ingredients})

def generate_grocery_list(request):
    if request.method == "POST":
        num_people = int(request.POST.get("num_people", 1))
        g_list = GroceryList()

        # Get meal plan from session
        meal_plan = get_meal_plan(request)

        # Process each day in the meal plan
        for day, recipes_data in meal_plan.items():
            for recipe_data in recipes_data:
                try:
                    recipe_id = recipe_data['recipe_id']
                    recipe_servings = recipe_data['servings']
                    recipe = Recipe.objects.get(id=recipe_id)
                    g_list.add_recipe(recipe, servings=recipe_servings * num_people)
                except (KeyError, Recipe.DoesNotExist):
                    continue

        # Organize grocery items by aisle
        categorized = {}
        for item in g_list.grocery_items.values():
            ing = item["ingredient"]
            aisle = ing.aisle
            if aisle not in categorized:
                categorized[aisle] = []
            categorized[aisle].append((ing.name, item["units"]))

        return render(request, "grocery_list_partial.html", {
            "categorized": categorized,
            "aisles_list": aisles_list,
            "num_people": num_people,
        })

    return redirect("meal_plan")
# def generate_grocery_list(request):
#     if request.method == "POST":
#         num_people = int(request.POST.get("num_people", 1))
#         g_list = GroceryList()

#         for day_recipes in MEAL_PLAN.days.values():
#             for recipe in day_recipes:
#                 g_list.add_recipe(recipe, servings=recipe.servings)

#         categorized = {}
#         for item in g_list.grocery_items.values():
#             ing = item["ingredient"]
#             aisle = ing.aisle
#             if aisle not in categorized:
#                 categorized[aisle] = []
#             categorized[aisle].append((ing.name, {unit: amount * num_people for unit, amount in item["units"].items()}))

#         return render(request, "grocery_list_partial.html", {
#             "categorized": categorized,
#             "aisles_list": aisles_list,
#             "num_people": num_people,
#         })

#     return redirect("meal_plan_view")


# def generate_grocery_list(request):
#     if request.method == "POST":
#         num_people = int(request.POST.get("num_people", 1))
#         g_list = GroceryList()

#         for day_recipes in MEAL_PLAN.days.values():
#             for recipe in day_recipes:
#                 g_list.add_recipe(recipe, servings=recipe.servings * num_people)

#         categorized = {}
#         for item in g_list.grocery_items.values():
#             ing = item["ingredient"]
#             aisle = ing.aisle
#             if aisle not in categorized:
#                 categorized[aisle] = []
#             categorized[aisle].append((ing.name, {unit: amount * num_people for unit, amount in item["units"].items()}))

#         return render(request, "grocery_list_partial.html", {
#             "categorized": categorized,
#             "aisles_list": aisles_list,
#             "num_people": num_people,
#         })

#     return redirect("meal_plan_view")


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
