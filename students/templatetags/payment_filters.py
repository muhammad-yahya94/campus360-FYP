from django import template

register = template.Library()

@register.filter
def get_payment_for_fund(payments, fund_id):
    """
    Filter to get a payment from a queryset where payment.fund_id matches the given fund_id.
    Returns the first matching payment or None if not found.
    """
    try:
        return payments.get(fund_id=fund_id)
    except (AttributeError, KeyError, ValueError):
        return None
