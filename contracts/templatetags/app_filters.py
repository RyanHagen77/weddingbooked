# your_app/templatetags/app_filters.py
from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    return float(value) * float(arg)