from django import template
from django.db.models import QuerySet
from django.db.models.functions import Coalesce
from django.db.models import Sum, FloatField
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

@register.filter
def get_payment_for_fund(payments, fund_id):
    """
    Filter to get a payment from a queryset where payment.fund_id matches the given fund_id.
    Returns the first matching payment or None if not found.
    """
    try:
        return payments.filter(fund_id=fund_id).first()
    except (AttributeError, KeyError, ValueError):
        return None




@register.filter
def to_json(value):
    """
    Convert a Python object to a JSON string, ensuring safe serialization.
    """
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return json.dumps([])


@register.filter
def absolute(value):
    """Return the absolute value of the input."""
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return value

@register.filter
def sum_queryset(queryset, field_name):
    """
    Sum the values of a specific field in a queryset or list of dictionaries.
    """
    if not queryset:
        return 0
        
    if isinstance(queryset, QuerySet):
        # Handle Django querysets
        return queryset.aggregate(
            total=Coalesce(Sum(field_name, output_field=FloatField()), 0.0)
        )['total']
    elif hasattr(queryset, '__iter__'):
        # Handle lists of dictionaries
        try:
            return sum(float(item.get(field_name, 0)) for item in queryset if item.get(field_name) is not None)
        except (TypeError, ValueError):
            return 0
    return 0
