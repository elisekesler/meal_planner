# mealapp/models.py

from django.db import models

# mealapp/models.py - add new model
class UnitConversion(models.Model):
    from_unit = models.CharField(max_length=20)
    to_unit = models.CharField(max_length=20)
    conversion_factor = models.FloatField()

    class Meta:
        unique_together = ('from_unit', 'to_unit')

    def __str__(self):
        return f"1 {self.from_unit} = {self.conversion_factor} {self.to_unit}"

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    instructions = models.TextField()
    calories_per_serving = models.FloatField(default=0)
    fat_per_serving = models.FloatField(default=0)
    carbs_per_serving = models.FloatField(default=0)
    protein_per_serving = models.FloatField(default=0)
    servings = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

# mealapp/models.py - modify Ingredient model
class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    aisle = models.IntegerField(default=0)
    calories_per_unit = models.FloatField(null=True, blank=True)
    protein_per_unit = models.FloatField(null=True, blank=True)
    carbs_per_unit = models.FloatField(null=True, blank=True)
    fat_per_unit = models.FloatField(null=True, blank=True)
    base_unit = models.CharField(max_length=20, default='unit')  # Add this

    def get_converted_amount(self, amount, from_unit):
        if from_unit == self.base_unit:
            return amount
        try:
            conversion = UnitConversion.objects.get(
                from_unit=from_unit,
                to_unit=self.base_unit
            )
            return amount * conversion.conversion_factor
        except UnitConversion.DoesNotExist:
            return amount

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='recipe_ingredients',)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    amount = models.FloatField()
    unit = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.amount} {self.unit} of {self.ingredient.name} for {self.recipe.name}"