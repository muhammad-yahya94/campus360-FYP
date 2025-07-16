from django.core.management.base import BaseCommand
from admissions.models import Applicant

class Command(BaseCommand):
    help = 'Change status of applications to accepted, optionally filtered by shift'

    def add_arguments(self, parser):
        parser.add_argument(
            '--shift',
            type=str,
            choices=['morning', 'evening'],
            help='Filter applications by shift (morning or evening)'
        )

    def handle(self, *args, **options):
        shift = options.get('shift')
        queryset = Applicant.objects.all()
        if shift:
            queryset = queryset.filter(shift__iexact=shift)
        updated_count = queryset.update(status='accepted')
        if shift:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} {shift} shift applications to accepted.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} applications to accepted.'))
