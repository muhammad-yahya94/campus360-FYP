# myapp/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='dictattribute')
def dictattribute(dictionary, key):
    """Returns the value of a dictionary for a given key."""
    return dictionary.get(key)
