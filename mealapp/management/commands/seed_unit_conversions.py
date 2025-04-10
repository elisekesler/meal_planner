# mealapp/management/commands/seed_unit_conversions.py

from django.core.management.base import BaseCommand
from mealapp.models import UnitConversion

class Command(BaseCommand):
    help = 'Seeds the database with common unit conversions'

    def handle(self, *args, **options):
        # Define common conversions
        # Format: (from_unit, to_unit, conversion_factor)
        conversions = [
            # Weight conversions
            ('pound', 'gram', 453.59237),
            ('ounce', 'gram', 28.349523125),
            ('gram', 'kilogram', 0.001),

            # Volume conversions
            ('cup', 'milliliter', 236.588),
            ('tablespoon', 'milliliter', 14.7868),
            ('teaspoon', 'milliliter', 4.92892),
            ('fluid_ounce', 'milliliter', 29.5735),
            ('cup', 'tablespoon', 16),
            ('tablespoon', 'teaspoon', 3),

            # Common ingredient specific conversions
            ('cup', 'gram', 240),  # Generic approximation, varies by ingredient
            ('stick', 'tablespoon', 8),  # For butter
            ('stick', 'cup', 0.5),  # For butter
            ('clove', 'teaspoon', 1),  # For garlic
        ]

        # Count successes and skips
        created = 0
        skipped = 0

        # Create each conversion
        for from_unit, to_unit, factor in conversions:
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()

            # Check if conversion already exists
            if UnitConversion.objects.filter(from_unit=from_unit, to_unit=to_unit).exists():
                self.stdout.write(self.style.WARNING(
                    f'Skipping existing conversion: {from_unit} → {to_unit}'
                ))
                skipped += 1
                continue

            # Create the conversion
            UnitConversion.objects.create(
                from_unit=from_unit,
                to_unit=to_unit,
                conversion_factor=factor
            )

            # Create the reverse conversion
            UnitConversion.objects.create(
                from_unit=to_unit,
                to_unit=from_unit,
                conversion_factor=1.0/factor
            )

            self.stdout.write(self.style.SUCCESS(
                f'Created conversions: {from_unit} ↔ {to_unit}'
            ))
            created += 1

        # Report results
        self.stdout.write(self.style.SUCCESS(
            f'Finished seeding unit conversions. Created: {created}, Skipped: {skipped}'
        ))