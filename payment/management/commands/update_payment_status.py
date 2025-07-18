from django.core.management.base import BaseCommand
from payment.models import Payment

class Command(BaseCommand):
    help = 'Updates payment status to pending where user ID is divisible by 7'

    def handle(self, *args, **options):
        # Get all payments where user.id is divisible by 7
        payments = Payment.objects.filter(user__id__mod=7)
        
        # Update status to pending
        updated_count = payments.update(status='pending')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} payments to pending status')
        )