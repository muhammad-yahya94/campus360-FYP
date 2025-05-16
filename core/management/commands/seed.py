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
from faculty_staff.models import Teacher
from courses.models import Course, CourseOffering, Semester
from students.models import Student, StudentEnrollment
from django.utils import timezone
from django.db.utils import IntegrityError
import uuid

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **options):
        fake = Faker()
        seeder = Seed.seeder()

        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        # Delete in proper order to avoid foreign key constraints
        StudentEnrollment.objects.all().delete()
        CourseOffering.objects.all().delete()
        Semester.objects.all().delete()
        Course.objects.all().delete()
        Teacher.objects.all().delete()
        Student.objects.all().delete()
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
                created_at=datetime.now(),
                location=fake.address()
            )

        # ===== Sliders =====
        self.stdout.write("Creating sliders...")
        for _ in range(5):
            Slider.objects.create(
                title=fake.sentence(nb_words=4),
                image=None,
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
                image=None
            )

        # ===== Gallery =====
        self.stdout.write("Creating gallery images...")
        for _ in range(20):
            Gallery.objects.create(
                title=fake.sentence(nb_words=5),
                image=None
            )

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
            {'name': 'BS Computer Science', 'department': Department.objects.get(name='Computer Science'), 'degree_type': 'BS', 'duration_years': 4, 'total_semesters': 8},
            {'name': 'MS Computer Science', 'department': Department.objects.get(name='Computer Science'), 'degree_type': 'MS', 'duration_years': 2, 'total_semesters': 8},
            {'name': 'BS Electrical Engineering', 'department': Department.objects.get(name='Electrical Engineering'), 'degree_type': 'BS', 'duration_years': 4, 'total_semesters': 8},
            {'name': 'BBA', 'department': Department.objects.get(name='Business Administration'), 'degree_type': 'BBA', 'duration_years': 4, 'total_semesters': 8},
            {'name': 'MBA', 'department': Department.objects.get(name='Business Administration'), 'degree_type': 'MBA', 'duration_years': 2, 'total_semesters': 8},
        ]
        for prog in programs:
            Program.objects.create(**prog)

        # ===== Semesters =====
        self.stdout.write("Creating semesters...")
        base_year = 2022  # Start year for semesters
        for program in Program.objects.all():
            for i in range(1, 9):  # Create 8 semesters per program
                year = base_year + (i - 1) // 2  # Alternate years (e.g., 2022, 2023, 2024, 2025)
                season = "Fall" if i % 2 == 1 else "Spring"  # Alternate Fall and Spring
                semester_name = f"{season} {year} - Semester {i}"
                start_month = 8 if season == "Fall" else 1  # Fall starts in August, Spring in January
                start_date = datetime(year, start_month, 1).date()
                end_date = start_date + timedelta(days=120)  # Approx 4-month semester

                Semester.objects.create(
                    program=program,
                    name=semester_name,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=(i == 8 and year == 2025)  # Set the last semester of 2025 as current
                )

        # ===== Courses =====
        self.stdout.write("Creating courses...")
        courses = [
            {
                'department': Department.objects.get(name='Computer Science'),
                'program': Program.objects.get(name='BS Computer Science'),
                'code': 'CS101',
                'name': 'Introduction to Programming',
                'credits': 3,
                'course_type': 'core',
                'description': fake.paragraph(nb_sentences=3)
            },
            {
                'department': Department.objects.get(name='Computer Science'),
                'program': Program.objects.get(name='BS Computer Science'),
                'code': 'CS201',
                'name': 'Data Structures',
                'credits': 3,
                'course_type': 'core',
                'description': fake.paragraph(nb_sentences=3)
            },
            {
                'department': Department.objects.get(name='Electrical Engineering'),
                'program': Program.objects.get(name='BS Electrical Engineering'),
                'code': 'EE101',
                'name': 'Circuit Analysis',
                'credits': 3,
                'course_type': 'core',
                'description': fake.paragraph(nb_sentences=3)
            },
            {
                'department': Department.objects.get(name='Business Administration'),
                'program': Program.objects.get(name='BBA'),
                'code': 'BA101',
                'name': 'Principles of Management',
                'credits': 3,
                'course_type': 'core',
                'description': fake.paragraph(nb_sentences=3)
            },
        ]
        for course in courses:
            Course.objects.create(**course)

        # ===== Users and Teachers =====
        self.stdout.write("Creating users and teachers...")
        user_types = ['student'] * 50 + ['faculty'] * 10 + ['admin'] * 2
        created_count = 0
        duplicate_count = 0
        departments_list = list(Department.objects.all())

        for i, user_type in enumerate(user_types):
            email = f"{user_type}{i+1}@ggcj.edu.pk"
            
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
                
                # Create Teacher profile for faculty users, ensuring each department has teachers
                if user_type == 'faculty':
                    # Distribute teachers across departments
                    department = departments_list[i % len(departments_list)]
                    Teacher.objects.create(
                        user=user,
                        department=department,
                        designation=random.choice([
                            'head_of_department', 'professor', 'associate_professor',
                            'assistant_professor', 'lecturer', 'visiting'
                        ]),
                        contact_no=f"03{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                        qualification=fake.paragraph(nb_sentences=2),
                        hire_date=timezone.now().date() - timedelta(days=random.randint(365, 365*5)),
                        is_active=True
                    )
            except IntegrityError as e:
                duplicate_count += 1
                self.stdout.write(self.style.WARNING(f"Skipped user creation due to IntegrityError: {str(e)}"))
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
            for year in range(2022, 2026):  # 4 years of cycles
                for season in ['Fall', 'Spring']:
                    AdmissionCycle.objects.create(
                        program=program,
                        session=None,  # No AcademicSession, so set to None
                        application_start=datetime(year, 1 if season == 'Spring' else 8, 1) - timedelta(days=60),
                        application_end=datetime(year, 1 if season == 'Spring' else 8, 1) - timedelta(days=30),
                        is_open=(year == 2025 and season == 'Spring')  # Only 2025 Spring is open
                    )

        # ===== Applicants and Students =====
        self.stdout.write("Creating applicants and students...")
        available_students = list(CustomUser.objects.filter(is_staff=False, student_profile__isnull=True))
        religions = ['Islam', 'Christianity', 'Hinduism', 'Sikhism', 'Buddhism']
        castes = ['Arain', 'Jutt', 'Rajput', 'Sheikh', 'Mughal', 'Syed', 'Qureshi']

        for cycle in AdmissionCycle.objects.all():
            for _ in range(random.randint(5, 15)):
                if not available_students:
                    self.stdout.write(self.style.WARNING("No more available users for student profiles."))
                    break
                
                dob = timezone.now().date() - timedelta(days=random.randint(365*18, 365*25))
                cnic = f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(0,9)}"
                
                user = random.choice(available_students)
                available_students.remove(user)
                
                applicant_data = {
                    'user': user,
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
                    'permanent_address': f"{random.randint(1, 100)} {random.choice(['Main Street', 'Model Town', 'Gulberg', 'Cantt'])} {random.choice(['Lahore', 'Karachi', 'Faisalabad'])}",
                    'declaration': random.choice([True, False]),
                }
                
                try:
                    applicant = Applicant.objects.create(**applicant_data)
                    
                    if applicant.status == 'accepted':
                        Student.objects.create(
                            applicant=applicant,
                            user=user,
                            university_roll_no=random.randint(100000, 999999),
                            college_roll_no=random.randint(1000, 9999),
                            enrollment_date=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                            current_status='active',
                            emergency_contact=fake.name(),
                            emergency_phone=f"03{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
                        )
                    
                    for level in ['matric', 'intermediate', 'bachelor']:
                        AcademicQualification.objects.create(
                            applicant=applicant,
                            exam_passed=f"{level.capitalize()} in Science",
                            passing_year=random.randint(2015, 2020),
                            marks_obtained=random.randint(600, 900),
                            total_marks=1100,
                            division=random.choice(['First', 'Second', 'Third']),
                            subjects="Physics, Chemistry, Mathematics, English",
                            institute=f"{random.choice(['Government', 'Punjab', 'Islamabad'])} {level.capitalize()} School",
                            board=f"{random.choice(['Lahore', 'Rawalpindi', 'Federal'])} Board",
                        )
                    
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

        # ===== Course Offerings =====
        self.stdout.write("Creating course offerings...")
        for semester in Semester.objects.filter(is_current=True):
            for course in Course.objects.filter(program=semester.program):
                teachers = list(Teacher.objects.filter(department=course.department))
                if not teachers:
                    self.stdout.write(self.style.WARNING(f"No teachers found for department {course.department.name}. Creating a default teacher."))
                    user = CustomUser.objects.create_user(
                        email=f"faculty_default_{course.department.code}@ggcj.edu.pk",
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        password='password123',
                        is_staff=True,
                        is_active=True
                    )
                    teacher = Teacher.objects.create(
                        user=user,
                        department=course.department,
                        designation='lecturer',
                        contact_no=f"03{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                        qualification=fake.paragraph(nb_sentences=2),
                        hire_date=timezone.now().date() - timedelta(days=365),
                        is_active=True
                    )
                    teachers = [teacher]
                
                teacher = random.choice(teachers)
                CourseOffering.objects.create(
                    semester=semester,
                    course=course,
                    teacher=teacher,
                    schedule=f"{random.choice(['Mon/Wed', 'Tue/Thu'])} {random.choice(['10:00-11:30', '13:00-14:30'])}",
                    room=f"Room {random.choice(['A', 'B', 'C'])}-{random.randint(100, 999)}"
                )

        # ===== Student Enrollments =====
        self.stdout.write("Creating student enrollments...")
        for student in Student.objects.all():
            semester = Semester.objects.filter(program=student.applicant.program, is_current=True).first()
            if not semester:
                self.stdout.write(self.style.WARNING(f"No current semester found for {student.applicant.full_name}'s program. Skipping enrollment."))
                continue

            course_offerings = CourseOffering.objects.filter(semester=semester, course__program=student.applicant.program)[:random.randint(1, 3)]
            for offering in course_offerings:
                try:
                    StudentEnrollment.objects.create(
                        student=student.applicant,
                        course_offering=offering,
                        status=random.choice(['enrolled', 'completed']),
                    )
                except IntegrityError as e:
                    self.stdout.write(self.style.WARNING(f"Skipped enrollment due to IntegrityError: {str(e)}"))
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))