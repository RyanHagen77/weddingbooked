from django import template
import re
register = template.Library()


@register.filter
def pretty_role(role_code):
    """
    Converts a role code (e.g. "PHOTOGRAPHER1") into a pretty, human-friendly format (e.g. "Photographer 1").
    """
    mapping = {
        'PHOTOGRAPHER1': 'Photographer 1',
        'PHOTOGRAPHER2': 'Photographer 2',
        'ENGAGEMENT': 'Engagement',
        'VIDEOGRAPHER1': 'Videographer 1',
        'VIDEOGRAPHER2': 'Videographer 2',
        'DJ1': 'DJ 1',
        'DJ2': 'DJ 2',
        'PHOTOBOOTH_OP1': 'Photobooth Operator 1',
        'PHOTOBOOTH_OP2': 'Photobooth Operator 2',
    }
    return mapping.get(role_code, role_code.title())

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


@register.filter
def sum_overtime(overtime_entries, role_code):
    """
    Sums the overtime hours from a list of overtime entries for a given role.
    If an overtime entry has an overtime_option attribute, it uses that option's role.
    """
    total = 0
    for entry in overtime_entries:
        # If the entry is a dict, try to get its 'role' key.
        if isinstance(entry, dict):
            entry_role = entry.get('role')
        # Otherwise, if it has an overtime_option attribute, use that.
        elif hasattr(entry, 'overtime_option'):
            entry_role = entry.overtime_option.role
        else:
            entry_role = getattr(entry, 'role', None)
        if entry_role == role_code:
            try:
                total += float(entry.hours)
            except (TypeError, ValueError):
                continue
    return total
@register.filter
def add_float(value, arg):
    """
    Converts both value and arg to float and returns their sum.
    """
    try:
        return float(value) + float(arg)
    except (TypeError, ValueError):
        return value
