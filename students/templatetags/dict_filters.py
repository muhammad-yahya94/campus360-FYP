from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get dictionary item by key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key)
    return ''

@register.filter(name='dict_key')
def dict_key(dictionary, key):
    """
    Template filter to get dictionary item by key.
    Usage: {{ my_dict|dict_key:key }}
    """
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
