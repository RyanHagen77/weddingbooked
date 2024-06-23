# your_app/templatetags/app_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    return float(value) * float(arg)


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