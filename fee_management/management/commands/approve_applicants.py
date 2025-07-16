from django.core.management.base import BaseCommand
from admissions.models import Applicant, Program
from django.db.models import Q

class Command(BaseCommand):
    help = 'Changes the status of applicants to "accepted" (approved).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--program_id',
            type=int,
            help='The ID of the program for which to approve applicants. If not provided, you must use --all.',
            default=None
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Approve all pending or rejected applicants across all programs.',
        )

    def handle(self, *args, **options):
        program_id = options['program_id']
        approve_all = options['all']

        if not program_id and not approve_all:
            self.stdout.write(self.style.ERROR('You must specify either a --program_id or use the --all flag.'))
            return

        # We will consider applicants who are not already accepted or admitted
        applicants_to_update = Applicant.objects.exclude(status__in=['accepted', 'admitted'])

        if program_id:
            try:
                program = Program.objects.get(pk=program_id)
                applicants_to_update = applicants_to_update.filter(program=program)
                self.stdout.write(f'Finding applicants for program: {program.name}')
            except Program.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Program with ID {program_id} does not exist.'))
                return
        
        if not approve_all and program_id is None:
             self.stdout.write(self.style.ERROR('Please specify a program ID or use the --all flag.'))
             return

        count = applicants_to_update.count()
        if count == 0:
            self.stdout.write(self.style.WARNING('No applicants found to approve.'))
            return

        # Update the status to 'accepted' and clear any previous rejection reason
        updated_count = applicants_to_update.update(status='accepted', rejection_reason='')

        self.stdout.write(self.style.SUCCESS(f'Successfully approved {updated_count} applicants.'))
