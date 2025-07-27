from django import template
from django.apps import apps

register = template.Library()

@register.filter
def get_attribute(obj, attr_name):
    try:
        if '__' in attr_name:
            # Handle related fields (e.g., course__code)
            related_field, sub_attr = attr_name.split('__', 1)
            related_obj = getattr(obj, related_field)
            return get_attribute(related_obj, sub_attr) if related_obj else ''
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        return ''