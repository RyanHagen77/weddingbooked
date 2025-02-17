from django import template
import re
register = template.Library()


@register.filter(name='in_group')
def in_group(user, group_name):
    """
    Check if the user belongs to a specific group.
    """
    return user.groups.filter(name=group_name).exists()


@register.filter
def subtract(value, arg):
    """
    Subtracts the argument from the value.
    Usage in template: {{ value|subtract:arg }}
    Both value and arg are converted to floats.
    Returns an empty string on error.
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiply two numbers and return the result.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0



@register.filter
def strip_year(value):
    """
    Removes a four-digit year followed by a space at the start of the string.
    Example: "2024 name of product" becomes "name of product"
    """
    try:
        value_str = str(value)
        # Remove a 4-digit year followed by a space at the start of the string
        return re.sub(r'^\d{4}\s', '', value_str)
    except Exception:
        return value  # Return the original value if something goes wrong
