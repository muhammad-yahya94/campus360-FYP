import random
from django_seed import Seed
from faker import Faker
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from main.models import *
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **options):
        fake = Faker()
        seeder = Seed.seeder()

        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        # Delete in proper order to avoid foreign key constraints
        Enrollment.objects.all().delete()
        Applicant.objects.all().delete()
        AdmissionCycle.objects.all().delete()
        Course.objects.all().delete()
        Semester.objects.all().delete()
        AcademicSession.objects.all().delete()
        Program.objects.all().delete()
        Department.objects.all().delete()
        Faculty.objects.all().delete()
        DegreeType.objects.all().delete()
        
        # Only delete non-admin users
        CustomUser.objects.filter(is_superuser=False).delete()

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

        # ===== Semesters =====
        self.stdout.write("Creating semesters...")
        for session in AcademicSession.objects.all():
            for sem_num in range(1, 3):
                start_date = session.start_date + timedelta(days=(sem_num-1)*90)
                Semester.objects.create(
                    name=f"Semester {sem_num}",
                    session=session,
                    start_date=start_date,
                    end_date=start_date + timedelta(days=90)
                )

        # ===== Courses =====
        self.stdout.write("Creating courses...")
        courses = [
            {'code': 'CS101', 'title': 'Introduction to Programming', 'department': Department.objects.get(name='Computer Science'), 'credits': 3},
            {'code': 'CS201', 'title': 'Data Structures', 'department': Department.objects.get(name='Computer Science'), 'credits': 3},
            {'code': 'EE101', 'title': 'Basic Electronics', 'department': Department.objects.get(name='Electrical Engineering'), 'credits': 3},
            {'code': 'MATH101', 'title': 'Calculus I', 'department': Department.objects.get(name='Mathematics'), 'credits': 3},
            {'code': 'BA101', 'title': 'Principles of Management', 'department': Department.objects.get(name='Business Administration'), 'credits': 3},
        ]
        for course in courses:
            Course.objects.create(**course)

        # ===== Users =====
        self.stdout.write("Creating users...")
        user_types = ['student'] * 50 + ['faculty'] * 10 + ['admin'] * 2
        for i, user_type in enumerate(user_types):
            email = f"{user_type}{i+1}@ggcj.edu.pk"
            user = CustomUser.objects.create_user(
                email=email,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='password123',
                is_staff=(user_type in ['faculty', 'admin']),
                is_superuser=(user_type == 'admin')
            )

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
        # ===== Applicants =====
        self.stdout.write("Creating applicants...")
        students = CustomUser.objects.filter(is_staff=False)

        try:
            # Test which field name works
            test_applicant = Applicant.objects.create(
                CustomUser=random.choice(students),
                program=Program.objects.first(),
                admission_cycle=AdmissionCycle.objects.first(),
                status='pending'
            )
            test_applicant.delete()  # Clean up test record
            field_name = 'CustomUser'
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating applicant: {str(e)}"))
            field_name = 'user'  # Fallback to common field names
            try:
                test_applicant = Applicant.objects.create(
                    user=random.choice(students),
                    program=Program.objects.first(),
                    admission_cycle=AdmissionCycle.objects.first(),
                    status='pending'
                )
                test_applicant.delete()
            except Exception as e:
                field_name = 'student'  # Final fallback

        for cycle in AdmissionCycle.objects.all():
            for _ in range(random.randint(5, 15)):
                applicant_data = {
                    field_name: random.choice(students),
                    'program': cycle.program,
                    'admission_cycle': cycle,
                    'status': random.choice(['pending', 'accepted', 'rejected']),
                }
                try:
                    Applicant.objects.create(**applicant_data)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to create applicant: {str(e)}"))
                    continue

        # ===== Enrollments =====
        self.stdout.write("Creating enrollments...")
        for semester in Semester.objects.all():
            for course in Course.objects.all():
                for _ in range(random.randint(5, 20)):
                    Enrollment.objects.create(
                        student=random.choice(students),
                        course=course,
                        semester=semester,
                        grade=random.choice(['A', 'B', 'C', 'D', 'F', None])
                    )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))