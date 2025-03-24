# mealapp/templatetags/myfilters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary_or_list, key):
    """
    Safely get the item from a dictionary or list by key/index.
    """
    try:
        return dictionary_or_list[key]
    except (KeyError, IndexError, TypeError):
        return ""  # or some fallback