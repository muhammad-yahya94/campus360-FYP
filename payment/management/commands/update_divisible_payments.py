from django.core.management.base import BaseCommand
from payment.models import Payment

class Command(BaseCommand):
    help = 'Updates payment status to pending where user ID is divisible by 7'

    def handle(self, *args, **options):
        updated = Payment.objects.filter(
            user__id__mod=7,
            user__id__gt=0
        ).update(status='pending')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated} payments')
        )