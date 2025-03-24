# mealapp/management/commands/import_recipes.py
from django.core.management.base import BaseCommand
from mealapp.models import Recipe, Ingredient, RecipeIngredient
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Import recipes and ingredients from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        # Get the absolute path to the JSON file
        json_path = os.path.join(settings.BASE_DIR, options['json_file'])
        
        try:
            with open(json_path) as f:
                data = json.load(f)
            
            # Keep track of statistics
            recipes_created = 0
            ingredients_created = 0
            
            for recipe_data in data:
                try:
                    # Create the recipe
                    recipe = Recipe.objects.create(
                        name=recipe_data['name'],
                        instructions=recipe_data['instructions'],
                        calories_per_serving=recipe_data.get('calories_per_serving', 0),
                        fat_per_serving=recipe_data.get('fat_per_serving', 0),
                        carbs_per_serving=recipe_data.get('carbs_per_serving', 0),
                        protein_per_serving=recipe_data.get('protein_per_serving', 0),
                        servings=recipe_data.get('servings', 1)
                    )
                    recipes_created += 1
                    
                    # Process ingredients
                    for ingredient_data in recipe_data['ingredients']:
                        # Try to get existing ingredient or create new one
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=ingredient_data['name'].lower(),  # Normalize ingredient names
                            defaults={
                                'aisle': ingredient_data.get('aisle', 0),
                                'calories_per_unit': ingredient_data.get('calories_per_unit'),
                                'protein_per_unit': ingredient_data.get('protein_per_unit'),
                                'carbs_per_unit': ingredient_data.get('carbs_per_unit'),
                                'fat_per_unit': ingredient_data.get('fat_per_unit')
                            }
                        )
                        
                        if created:
                            ingredients_created += 1
                        
                        # Create the recipe-ingredient relationship
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=ingredient,
                            quantity=ingredient_data['quantity'],
                            unit=ingredient_data['unit']
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully imported recipe: {recipe.name}')
                    )
                
                except KeyError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping recipe due to missing field: {e}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing recipe: {str(e)}')
                    )
            
            # Print final statistics
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nImport completed:\n'
                    f'- Recipes created: {recipes_created}\n'
                    f'- Ingredients created: {ingredients_created}'
                )
            )
            
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Could not find file: {json_path}')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Invalid JSON format in the input file')
            )