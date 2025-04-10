# mealapp/templatetags/myfilters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Safely get the item from a dictionary by key.
    Works with numeric keys too.
    """
    try:
        # Try to convert key to int if it's a string but represents a number
        if isinstance(key, str) and key.isdigit():
            key = int(key)
        return dictionary.get(key, f"Aisle {key}")
    except (KeyError, AttributeError):
        return f"Aisle {key}"