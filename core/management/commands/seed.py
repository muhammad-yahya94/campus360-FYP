import random
from django_seed import Seed
from faker import Faker
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from academics.models import *
from admissions.models import *
from site_elements.models import *
from announcements.models import *
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **options):
        fake = Faker()
        seeder = Seed.seeder()

        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        # Delete in proper order to avoid foreign key constraints
        News.objects.all().delete()
        Event.objects.all().delete()
        Gallery.objects.all().delete()
        Alumni.objects.all().delete()
        Slider.objects.all().delete()
        Applicant.objects.all().delete()
        AdmissionCycle.objects.all().delete()
        AcademicSession.objects.all().delete()
        Program.objects.all().delete()
        Department.objects.all().delete()
        Faculty.objects.all().delete()
        DegreeType.objects.all().delete()
        
        
        
        # Only delete non-admin users
        CustomUser.objects.filter(is_superuser=False).delete()
        
                # ===== News =====
        self.stdout.write("Creating news...")
        for _ in range(10):
            News.objects.create(
                title=fake.sentence(nb_words=6),
                content=fake.paragraph(nb_sentences=10),
                is_published=random.choice([True, False])
            )

        # ===== Events =====
        self.stdout.write("Creating events...")
        for _ in range(10):
            start_date = timezone.now() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(hours=random.randint(1, 4))
            Event.objects.create(
                title=fake.sentence(nb_words=6),
                description=fake.paragraph(nb_sentences=8),
                event_start_date=start_date,
                event_end_date=end_date,
                created_at = datetime.now(),
                location=fake.address()
            )

        # ===== Sliders =====
        self.stdout.write("Creating sliders...")
        for _ in range(5):
            Slider.objects.create(
                title=fake.sentence(nb_words=4),
                image=None,  # Image field left empty (or you can set a default later)
                is_active=random.choice([True, False])
            )

        # ===== Alumni =====
        self.stdout.write("Creating alumni...")
        for _ in range(15):
            Alumni.objects.create(
                name=fake.name(),
                graduation_year=random.randint(2000, 2023),
                profession=fake.job(),
                testimonial=fake.paragraph(nb_sentences=5),
                image=None  # Same here, you can add default images if you want
            )

        # ===== Gallery =====
        self.stdout.write("Creating gallery images...")
        for _ in range(20):
            Gallery.objects.create(
                title=fake.sentence(nb_words=5),
                image=None  # Same, or add test images
            )


        # ===== Degree Types =====
        self.stdout.write("Creating degree types...")
        DegreeType.objects.create(code='BS', name='Bachelor of Science')
        DegreeType.objects.create(code='MS', name='Master of Science')
        DegreeType.objects.create(code='PhD', name='Doctor of Philosophy')
        DegreeType.objects.create(code='BBA', name='Bachelor of Business Administration')
        DegreeType.objects.create(code='MBA', name='Master of Business Administration')

        # ===== Faculties =====
        self.stdout.write("Creating faculties...")
        faculties = [
            {'name': 'Faculty of Engineering and Computing', 'description': fake.text()},
            {'name': 'Faculty of Languages', 'description': fake.text()},
            {'name': 'Faculty of Management Sciences', 'description': fake.text()},
            {'name': 'Faculty of Social Sciences', 'description': fake.text()},
            {'name': 'Faculty of Arts and Humanities', 'description': fake.text()},
        ]
        for faculty in faculties:
            Faculty.objects.create(**faculty)

        # ===== Departments =====
        self.stdout.write("Creating departments...")
        departments = [
            {'name': 'Computer Science', 'code': 'CS', 'faculty': Faculty.objects.get(name='Faculty of Engineering and Computing')},
            {'name': 'Electrical Engineering', 'code': 'EE', 'faculty': Faculty.objects.get(name='Faculty of Engineering and Computing')},
            {'name': 'Software Engineering', 'code': 'SE', 'faculty': Faculty.objects.get(name='Faculty of Engineering and Computing')},
            {'name': 'Mathematics', 'code': 'MATH', 'faculty': Faculty.objects.get(name='Faculty of Engineering and Computing')},
            {'name': 'Business Administration', 'code': 'BA', 'faculty': Faculty.objects.get(name='Faculty of Management Sciences')},
            {'name': 'English', 'code': 'ENG', 'faculty': Faculty.objects.get(name='Faculty of Languages')},
        ]
        for dept in departments:
            Department.objects.create(**dept)

        # ===== Programs =====
        self.stdout.write("Creating programs...")
        programs = [
            {'name': 'BS Computer Science', 'department': Department.objects.get(name='Computer Science'), 'degree_type': DegreeType.objects.get(code='BS'), 'duration_years': 4},
            {'name': 'MS Computer Science', 'department': Department.objects.get(name='Computer Science'), 'degree_type': DegreeType.objects.get(code='MS'), 'duration_years': 2},
            {'name': 'BS Electrical Engineering', 'department': Department.objects.get(name='Electrical Engineering'), 'degree_type': DegreeType.objects.get(code='BS'), 'duration_years': 4},
            {'name': 'BBA', 'department': Department.objects.get(name='Business Administration'), 'degree_type': DegreeType.objects.get(code='BBA'), 'duration_years': 4},
            {'name': 'MBA', 'department': Department.objects.get(name='Business Administration'), 'degree_type': DegreeType.objects.get(code='MBA'), 'duration_years': 2},
        ]
        for prog in programs:
            Program.objects.create(**prog)

        # ===== Academic Sessions =====
        self.stdout.write("Creating academic sessions...")
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 1):
            for season in ['Spring', 'Fall']:
                start_month = 1 if season == 'Spring' else 8
                AcademicSession.objects.create(
                    name=f"{season} {year}",
                    start_date=datetime(year, start_month, 1),
                    end_date=datetime(year, start_month + 4, 30),
                    is_active=(year == current_year)
                )

          

        # ===== Users =====
        self.stdout.write("Creating users...")
        user_types = ['student'] * 50 + ['faculty'] * 10 + ['admin'] * 2
        created_count = 0
        duplicate_count = 0

        for i, user_type in enumerate(user_types):
            email = f"{user_type}{i+1}@ggcj.edu.pk"
            
            # Skip if user with this email already exists
            if CustomUser.objects.filter(email=email).exists():
                duplicate_count += 1
                continue
            
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password='password123',
                    is_staff=(user_type in ['faculty', 'admin']),
                    is_superuser=(user_type == 'admin'),
                    is_active=True
                )
                created_count += 1
            except IntegrityError:
                duplicate_count += 1
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} users. "
                f"Skipped {duplicate_count} duplicate emails."
            )
        )

        # Ensure at least one admin exists
        if not CustomUser.objects.filter(is_superuser=True).exists():
            admin_email = "admin1@ggcj.edu.pk"
            if not CustomUser.objects.filter(email=admin_email).exists():
                CustomUser.objects.create_superuser(
                    email=admin_email,
                    first_name="Admin",
                    last_name="User",
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('Created default admin user'))

        # ===== Admission Cycles =====
        self.stdout.write("Creating admission cycles...")
        for program in Program.objects.all():
            for session in AcademicSession.objects.filter(is_active=True):
                AdmissionCycle.objects.create(
                    program=program,
                    session=session,
                    application_start=session.start_date - timedelta(days=60),
                    application_end=session.start_date - timedelta(days=30),
                    is_open=False
                )

        # ===== Applicants =====
        self.stdout.write("Creating applicants...")
        students = CustomUser.objects.filter(is_staff=False)

        # List of possible religions and castes for random selection
        religions = ['Islam', 'Christianity', 'Hinduism', 'Sikhism', 'Buddhism']
        castes = ['Arain', 'Jutt', 'Rajput', 'Sheikh', 'Mughal', 'Syed', 'Qureshi']

        for cycle in AdmissionCycle.objects.all():
            for _ in range(random.randint(5, 15)):
                # Generate random date of birth between 18-25 years ago
                dob = timezone.now().date() - timedelta(days=random.randint(365*18, 365*25))
                
                # Generate random CNIC (format: XXXXX-XXXXXXX-X)
                cnic = f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(0,9)}"
                
                applicant_data = {
                    'user': random.choice(students),
                    'faculty': cycle.program.department.faculty,
                    'department': cycle.program.department,
                    'program': cycle.program,
                    'status': random.choice(['pending', 'accepted', 'rejected']),
                    'full_name': f"{random.choice(['Ali', 'Ahmed', 'Fatima', 'Ayesha'])} {random.choice(['Khan', 'Malik', 'Raza', 'Akhtar'])}",
                    'religion': random.choice(religions),
                    'caste': random.choice(castes),
                    'cnic': cnic,
                    'dob': dob,
                    'contact_no': f"03{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                    'identification_mark': random.choice(['Mole on left cheek', 'Scar on right arm', 'Birthmark on neck', '']),
                    'father_name': f"Mr. {random.choice(['Abdul', 'Muhammad', 'Tariq', 'Usman'])} {random.choice(['Khan', 'Malik', 'Raza', 'Akhtar'])}",
                    'father_occupation': random.choice(['Business', 'Teacher', 'Farmer', 'Government Employee']),
                    'father_cnic': f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(0,9)}",
                    'monthly_income': random.randint(15000, 150000),
                    'relationship': random.choice(['father', 'guardian']),
                    'permanent_address': f"{random.randint(1, 100)} {random.choice(['Main Street', 'Model Town', 'Gulberg', 'Cantt'])} {random.choice(['Lahore', 'Karachi', 'Islamabad', 'Faisalabad'])}",
                    'declaration': random.choice([True, False]),
                }
                
                try:
                    applicant = Applicant.objects.create(**applicant_data)
                    
                    # Create academic qualifications
                    for level in ['matric', 'intermediate']:
                        AcademicQualification.objects.create(
                            applicant=applicant,
                            level=level,
                            exam_passed=f"{level.capitalize()} in Science",
                            passing_year=random.randint(2015, 2020),
                            roll_no=f"{random.randint(100000, 999999)}",
                            marks_obtained=random.randint(600, 900),
                            total_marks=1100,
                            division=random.choice(['First', 'Second', 'Third']),
                            subjects="Physics, Chemistry, Mathematics, English",
                            institute=f"{random.choice(['Government', 'Punjab', 'Islamabad'])} {level.capitalize()} School",
                            board=f"{random.choice(['Lahore', 'Rawalpindi', 'Federal'])} Board",
                        )
                    
                    # Create extracurricular activities (0-3 per applicant)
                    for _ in range(random.randint(0, 3)):
                        ExtraCurricularActivity.objects.create(
                            applicant=applicant,
                            activity=random.choice(['Sports', 'Debate', 'Music', 'Art']),
                            position=random.choice(['Captain', 'Member', 'Leader']),
                            achievement=random.choice(['Won competition', 'Participated', 'Received award']),
                            activity_year=random.randint(2018, 2020),
                        )
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to create applicant: {str(e)}"))
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))