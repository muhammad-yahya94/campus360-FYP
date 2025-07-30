from django import template

register = template.Library()

@register.filter
def get_payment_for_fund(payments, fund_id):
    """
    Filter to get a payment from a list where payment.fund_id matches the given fund_id.
    Returns the first matching payment or None if not found.
    """
    if not payments or not hasattr(payments, '__iter__'):
        print(f"No payments or not iterable: {payments}")
        return None
        
    try:
        # Convert to list if it's a queryset
        payments_list = list(payments) if hasattr(payments, 'all') else payments
        print(f"Processing {len(payments_list)} payments for fund_id {fund_id}")
        
        # Find the first payment that matches the fund_id
        for payment in payments_list:
            payment_fund_id = getattr(payment, 'fund_id', None)
            if payment_fund_id is not None and str(payment_fund_id) == str(fund_id):
                print(f"Matched payment for fund_id {fund_id}: {payment}")
                return payment
        print(f"No matching payment found for fund_id {fund_id}")
        return None
    except Exception as e:
        print(f"Error in get_payment_for_fund: {str(e)}")
        return None