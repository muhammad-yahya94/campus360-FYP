from django.core.management.base import BaseCommand
from django.conf import settings
from admissions.models import Applicant, AcademicQualification, ExtraCurricularActivity
from users.models import CustomUser
import sys

class Command(BaseCommand):
    help = 'Deletes all admission applications and their associated user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        if not options['force']:
            confirm = input(
                "WARNING: This will delete ALL admission applications AND their user accounts. Continue? [y/N] "
            )
            if confirm.lower() != 'y':
                self.stdout.write("Operation cancelled")
                sys.exit(0)

        # Get counts before deletion
        app_count = Applicant.objects.count()
        user_count = CustomUser.objects.filter(applications__isnull=False).count()

        # Delete related records first
        AcademicQualification.objects.all().delete()
        ExtraCurricularActivity.objects.all().delete()
        
        # Delete applicants
        Applicant.objects.all().delete()
        
        # Delete associated user accounts
        CustomUser.objects.filter(applications__isnull=False).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {app_count} applications and {user_count} user accounts')
        )
