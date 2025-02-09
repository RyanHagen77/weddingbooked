# your_app/templatetags/app_filters.py
from django import template
from decimal import Decimal
import json
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="multiply")
def multiply(value, arg):
    """Multiplies the given value by the argument, handling None and empty values."""
    try:
        # Convert empty or None values to 0
        value = float(value) if value not in [None, ""] else 0
        arg = float(arg) if arg not in [None, ""] else 0
        return value * arg
    except (ValueError, TypeError):
        return 0  # Return 0 if multiplication fails

@register.filter
def get_location_name(locations, selected_location):
    for location in locations:
        if location.id == int(selected_location):
            return location.name
    return ''

@register.filter
def sum_values(queryset, attr):
    total = Decimal('0.00')
    for item in queryset:
        total += getattr(item, attr, Decimal('0.00'))
    return total

@register.filter(name='in_group')
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(is_safe=True)
def to_json(value):
    return mark_safe(json.dumps(value))

@register.filter
def get_item(dictionary, key):
    """Safely retrieves an item from a dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None


