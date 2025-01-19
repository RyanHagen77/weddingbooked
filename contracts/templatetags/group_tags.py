from django import template
import re
register = template.Library()


@register.filter(name='in_group')
def in_group(user, group_name):
    """
    Check if the user belongs to a specific group.
    """
    return user.groups.filter(name=group_name).exists()


@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiply two numbers and return the result.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='strip_year')
def strip_year(value):
    """
    Removes the year (e.g., 2024, 2025) from a string.
    """
    return re.sub(r'\b(19|20)\d{2}\b', '', value).strip()
