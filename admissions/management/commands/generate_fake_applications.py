import random
from django.core.management.base import BaseCommand
from faker import Faker
from admissions.models import Applicant, AcademicSession
from academics.models import Program, Department, Faculty
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Generate fake admission applications'

    def handle(self, *args, **options):
        fake = Faker('en_PK')  # Use Pakistani locale for names
        
        # Get all active programs
        programs = Program.objects.filter(is_active=True)
        if not programs.exists():
            self.stdout.write(self.style.ERROR('No active programs found'))
            return
            
        # Get or create a test user
        user, created = CustomUser.objects.get_or_create(
            email='test@example.com',
            defaults={
                'password': 'testpass123'
            }
        )
        
        # Get or create an academic session
        session, created = AcademicSession.objects.get_or_create(
            name='2025-2029',
            defaults={
                'start_year': 2025,
                'end_year': 2029,
                'is_active': True
            }
        )
        
        for program in programs:
            self.stdout.write(f'Generating applications for {program.name}...')
            
            # Get related faculty and department
            faculty = program.department.faculty
            department = program.department
            
            # Generate 70-80 applications
            num_applications = random.randint(70, 80)
            for i in range(num_applications):
                # Generate fake personal data
                full_name = fake.name()
                cnic = str(fake.unique.random_number(digits=13, fix_len=True))
                dob = fake.date_of_birth(minimum_age=17, maximum_age=25)
                contact_no = fake.phone_number()[:15]
                
                # Generate fake father/guardian data
                father_name = fake.name_male()
                father_occupation = fake.job()
                monthly_income = random.randint(20000, 200000)
                
                # Create applicant
                Applicant.objects.create(
                    user=user,
                    session=session,
                    faculty=faculty,
                    department=department,
                    program=program,
                    status='pending',
                    full_name=full_name,
                    religion='Islam',
                    cnic=cnic,
                    dob=dob,
                    contact_no=contact_no,
                    father_name=father_name,
                    father_occupation=father_occupation,
                    monthly_income=monthly_income,
                    permanent_address=fake.address(),
                    shift=random.choice(['morning', 'evening']),
                    declaration=True,
                )
                
            self.stdout.write(self.style.SUCCESS(f'Successfully created {num_applications} applications for {program.name}'))
        
        self.stdout.write(self.style.SUCCESS('Finished generating fake applications'))