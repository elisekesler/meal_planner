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
        """
        Convert an ingredient amount from one unit to the base unit.
        Enhanced with better debugging.

        Args:
            amount: float, the amount to convert
            from_unit: string, the unit to convert from

        Returns:
            float: the converted amount in the ingredient's base unit
        """
        from_unit = from_unit.lower().strip()
        base_unit = self.base_unit.lower().strip()

        print(f"DEBUG: {self.name}: Converting {amount} {from_unit} to {base_unit}")

        # If units are the same, no conversion needed
        if from_unit == base_unit:
            print(f"DEBUG: Units are the same, no conversion needed")
            return amount

        # Try direct conversion
        try:
            conversion = UnitConversion.objects.get(
                from_unit=from_unit,
                to_unit=base_unit
            )
            print(f"DEBUG: Found direct conversion: 1 {from_unit} = {conversion.conversion_factor} {base_unit}")
            converted = amount * conversion.conversion_factor
            print(f"DEBUG: Converted {amount} {from_unit} to {converted} {base_unit}")
            return converted
        except UnitConversion.DoesNotExist:
            print(f"DEBUG: No direct conversion found from {from_unit} to {base_unit}")

            # Try to find all possible conversions from the source unit
            from_conversions = UnitConversion.objects.filter(from_unit=from_unit)
            print(f"DEBUG: Found {from_conversions.count()} possible intermediate conversions from {from_unit}")

            # Then, for each intermediate unit, check if we can convert to the base unit
            for intermediate in from_conversions:
                intermediate_unit = intermediate.to_unit
                print(f"DEBUG: Trying conversion via {intermediate_unit}")

                try:
                    to_base = UnitConversion.objects.get(
                        from_unit=intermediate_unit,
                        to_unit=base_unit
                    )

                    # If we found a two-step conversion, use it
                    print(f"DEBUG: Found two-step conversion path: {from_unit} → {intermediate_unit} → {base_unit}")
                    print(f"DEBUG: Step 1: 1 {from_unit} = {intermediate.conversion_factor} {intermediate_unit}")
                    print(f"DEBUG: Step 2: 1 {intermediate_unit} = {to_base.conversion_factor} {base_unit}")

                    intermediate_amount = amount * intermediate.conversion_factor
                    final_amount = intermediate_amount * to_base.conversion_factor

                    print(f"DEBUG: Converted {amount} {from_unit} to {intermediate_amount} {intermediate_unit} to {final_amount} {base_unit}")
                    return final_amount

                except UnitConversion.DoesNotExist:
                    print(f"DEBUG: No conversion found from {intermediate_unit} to {base_unit}")
                    continue

            # If we get here, no conversion path was found
            print(f"DEBUG: No conversion path found from {from_unit} to {base_unit}")
            print(f"DEBUG: Returning original amount as fallback")
            return amount  # Return unconverted as a fallback

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='recipe_ingredients',)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    amount = models.FloatField()
    unit = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.amount} {self.unit} of {self.ingredient.name} for {self.recipe.name}"