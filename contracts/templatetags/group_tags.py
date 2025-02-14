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
    Removes a space followed by four digits at the end of the string.
    Example: "Wedding 2023" becomes "Wedding"
    """
    try:
        # Convert the value to a string.
        value_str = str(value)
        # Use a regex to remove a trailing four-digit year preceded by whitespace.
        # Adjust the regex if your format is different.
        return re.sub(r'\s\d{4}$', '', value_str)
    except Exception:
        return value  # On error, return the original valueturn value