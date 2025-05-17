import random
from django_seed import Seed
from faker import Faker
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.utils import IntegrityError

from academics.models import *
from admissions.models import *
from site_elements.models import *
from announcements.models import *
from users.models import *
from faculty_staff.models import *  
from students.models import *
from courses.models import *


class Command(BaseCommand):
    help = 'Seeds the database with comprehensive test data for BS programs with 8 semesters, focusing on Fall 2021-2025 and other cycles'

    def handle(self, *args, **options):
        fake = Faker('en_PK')
        seeder = Seed.seeder()

        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        # Delete in reverse order to avoid foreign key constraints
        StudentEnrollment.objects.all().delete()
        Submission.objects.all().delete()
        Assignment.objects.all().delete()
        CourseOfferingTeacherChange.objects.all().delete()
        CourseOffering.objects.all().delete()
        Semester.objects.all().delete()
        Course.objects.all().delete()
        Teacher.objects.all().delete()
        Student.objects.all().delete()
        AcademicQualification.objects.all().delete()
        ExtraCurricularActivity.objects.all().delete()
        Applicant.objects.all().delete()
        AdmissionCycle.objects.all().delete()
        AcademicSession.objects.all().delete()
        Program.objects.all().delete()
        Department.objects.all().delete()
        Faculty.objects.all().delete()
        News.objects.all().delete()
        Event.objects.all().delete()
        Gallery.objects.all().delete()
        Alumni.objects.all().delete()
        Slider.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()

        # ===== Faculties =====
        self.stdout.write("Creating faculties...")
        faculties_data = [
            {'name': 'Faculty of Engineering and Computing', 'description': 'Technology and innovation hub.'},
            {'name': 'Faculty of Management Sciences', 'description': 'Business and leadership excellence.'},
            {'name': 'Faculty of Languages', 'description': 'Linguistic and literary studies.'},
        ]
        faculties = [Faculty.objects.create(**faculty) for faculty in faculties_data]

        # ===== Departments =====
        self.stdout.write("Creating departments...")
        departments_data = [
            {'name': 'Computer Science', 'code': 'CS', 'faculty': faculties[0]},
            {'name': 'Electrical Engineering', 'code': 'EE', 'faculty': faculties[0]},
            {'name': 'Software Engineering', 'code': 'SE', 'faculty': faculties[0]},
            {'name': 'Business Administration', 'code': 'BA', 'faculty': faculties[1]},
            {'name': 'English', 'code': 'ENG', 'faculty': faculties[2]},
            {'name': 'Linguistics', 'code': 'LING', 'faculty': faculties[2]},
        ]
        departments = [Department.objects.create(**dept) for dept in departments_data]

        # ===== Programs =====
        self.stdout.write("Creating programs...")
        programs_data = [
            {'name': 'BS Computer Science', 'department': departments[0], 'degree_type': 'BS', 'duration_years': 4},
            {'name': 'MS Computer Science', 'department': departments[0], 'degree_type': 'MS', 'duration_years': 2},
            {'name': 'BS Electrical Engineering', 'department': departments[1], 'degree_type': 'BS', 'duration_years': 4},
            {'name': 'BS Software Engineering', 'department': departments[2], 'degree_type': 'BS', 'duration_years': 4},
            {'name': 'BBA', 'department': departments[3], 'degree_type': 'BBA', 'duration_years': 4},
            {'name': 'MPhil Business Administration', 'department': departments[3], 'degree_type': 'MPhil', 'duration_years': 2},
            {'name': 'BA English', 'department': departments[4], 'degree_type': 'BA', 'duration_years': 4},
            {'name': 'MA Linguistics', 'department': departments[5], 'degree_type': 'MA', 'duration_years': 2},
        ]
        programs = [Program.objects.create(**prog) for prog in programs_data]
        bs_programs = [p for p in programs if p.degree_type in ['BS', 'BBA']]

        # ===== Academic Sessions =====
        self.stdout.write("Creating academic sessions...")
        academic_sessions = []
        for year in range(2021, 2026):
            for season, start_month, end_month in [('Fall', 8, 1), ('Spring', 2, 7)]:
                session = AcademicSession.objects.create(
                    name=f"{season} {year}",
                    start_date=timezone.datetime(year, start_month, 1).date(),
                    end_date=timezone.datetime(year + (end_month // 12), end_month % 12 or 12, 31).date()
                )
                academic_sessions.append(session)

        # ===== Admission Cycles =====
        self.stdout.write("Creating admission cycles...")
        admission_cycles = []
        for program in bs_programs:
            for start_year in range(2021, 2026):
                is_open = (start_year == 2025 and program.name in ['BS Computer Science', 'BBA'])
                session = next((s for s in academic_sessions if s.start_date.year == start_year and s.name.startswith('Fall')), academic_sessions[0])
                cycle = AdmissionCycle.objects.create(
                    program=program,
                    session=session,
                    application_start=timezone.datetime(start_year, 6, 1),
                    application_end=timezone.datetime(start_year, 7, 15),
                    is_open=is_open
                )
                admission_cycles.append(cycle)

        # ===== Semesters =====
        self.stdout.write("Creating semesters...")
        semesters = []
        cycle_progress = {
            2021: 8,  # 2021-2025: Semester 8 (Fall 2025)
            2022: 6,  # 2022-2026: Semester 6 (Fall 2025)
            2023: 4,  # 2023-2027: Semester 4 (Fall 2025)
            2024: 2,  # 2024-2028: Semester 2 (Fall 2025)
            2025: 1,  # 2025-2029: Semester 1 (Fall 2025)
        }
        for program in bs_programs:
            for start_year in range(2021, 2026):
                max_semester = cycle_progress[start_year]
                for semester_num in range(1, max_semester + 1):
                    year = start_year + (semester_num - 1) // 2
                    season = 'Fall' if semester_num % 2 == 1 else 'Spring'
                    start_month = 8 if season == 'Fall' else 2
                    end_month = 1 if season == 'Fall' else 7
                    start_date = timezone.datetime(year, start_month, 1).date()
                    end_date = timezone.datetime(year + (end_month // 12), end_month % 12 or 12, 31).date()
                    semester_name = f"{season} {year} - Semester {semester_num}"
                    is_current = (year == 2025 and season == 'Fall' and semester_num == max_semester)
                    semester = Semester.objects.create(
                        program=program,
                        name=semester_name,
                        start_date=start_date,
                        end_date=end_date,
                        is_current=is_current
                    )
                    semesters.append(semester)

        # ===== Courses =====
        self.stdout.write("Creating courses...")
        courses_data = [
            {'department': departments[0], 'program': programs[0], 'code': 'CS101', 'name': 'Introduction to Programming', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[0], 'program': programs[0], 'code': 'CS201', 'name': 'Data Structures', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[0], 'program': programs[0], 'code': 'CS301', 'name': 'Algorithms', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[1], 'program': programs[2], 'code': 'EE101', 'name': 'Circuit Analysis', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[1], 'program': programs[2], 'code': 'EE201', 'name': 'Electronics', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[2], 'program': programs[3], 'code': 'SE101', 'name': 'Software Design', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[2], 'program': programs[3], 'code': 'SE201', 'name': 'Software Testing', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[3], 'program': programs[4], 'code': 'BA101', 'name': 'Principles of Management', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[3], 'program': programs[4], 'code': 'BA201', 'name': 'Marketing', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[4], 'program': programs[6], 'code': 'ENG101', 'name': 'English Literature', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
            {'department': departments[4], 'program': programs[6], 'code': 'ENG201', 'name': 'Creative Writing', 'credits': 3, 'course_type': 'core', 'description': fake.paragraph()},
        ]
        courses = [Course.objects.create(**course) for course in courses_data]

        # ===== Users and Teachers =====
        self.stdout.write("Creating users and teachers...")
        user_types = ['student'] * 100 + ['faculty'] * 20 + ['admin'] * 3
        users = []
        teachers = []
        created_count = 0
        duplicate_count = 0
        # Distribute teachers across departments in a round-robin fashion
        department_cycle = list(departments) * 4  # Ensure enough departments for 20 teachers
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
                users.append(user)
                created_count += 1
                if user_type == 'faculty':
                    department = department_cycle[i % len(department_cycle)]  # Round-robin assignment
                    teacher = Teacher.objects.create(
                        user=user,
                        department=department,
                        designation=random.choice(['professor', 'associate_professor', 'assistant_professor', 'lecturer']),
                        contact_no=f"+92{random.randint(300, 399)}{random.randint(1000000, 9999999)}",
                        qualification=f"{random.choice(['PhD', 'MS'])} in {department.name}",
                        hire_date=timezone.now().date() - timedelta(days=random.randint(365, 365*10)),
                        is_active=True
                    )
                    teachers.append(teacher)
            except IntegrityError:
                duplicate_count += 1
                continue
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} users, skipped {duplicate_count} duplicates"))

        # Log teacher distribution
        for dept in departments:
            dept_teachers = [t for t in teachers if t.department == dept]
            self.stdout.write(f"Department {dept.name}: {len(dept_teachers)} teachers")

        # Ensure default admin
        if not CustomUser.objects.filter(is_superuser=True).exists():
            CustomUser.objects.create_superuser(
                email="admin@ggcj.edu.pk",
                first_name="Admin",
                last_name="User",
                password='admin123'
            )

        # ===== Applicants and Students =====
        self.stdout.write("Creating applicants and students...")
        student_users = [u for u in users if not u.is_staff]
        religions = ['Islam', 'Christianity', 'Hinduism']
        castes = ['Arain', 'Jutt', 'Rajput']
        students = []
        for cycle in admission_cycles:
            student_count = 20 if cycle.is_open else random.randint(10, 15)
            for _ in range(student_count):
                if not student_users:
                    break
                user = random.choice(student_users)
                student_users.remove(user)
                applicant = Applicant.objects.create(
                    user=user,
                    faculty=cycle.program.department.faculty,
                    department=cycle.program.department,
                    program=cycle.program,
                    status=random.choice(['pending', 'accepted', 'rejected']),
                    full_name=fake.name(),
                    religion=random.choice(religions),
                    caste=random.choice(castes),
                    cnic=f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(0,9)}",
                    dob=timezone.now().date() - timedelta(days=random.randint(365*18, 365*22)),
                    contact_no=f"+92{random.randint(300, 399)}{random.randint(1000000, 9999999)}",
                    identification_mark=fake.sentence(nb_words=3),
                    father_name=fake.name(),
                    father_occupation=fake.job(),
                    father_cnic=f"{random.randint(10000, 99999)}-{random.randint(1000000, 9999999)}-{random.randint(0,9)}",
                    monthly_income=random.randint(30000, 150000),
                    relationship='father',
                    permanent_address=fake.address(),
                    declaration=True
                )
                if applicant.status == 'accepted':
                    student = Student.objects.create(
                        applicant=applicant,
                        user=user,
                        university_roll_no=f"{random.randint(100000, 999999)}",
                        college_roll_no=f"{random.randint(1000, 9999)}",
                        enrollment_date=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                        current_status='active',
                        emergency_contact=fake.name(),
                        emergency_phone=f"+92{random.randint(300, 399)}{random.randint(1000000, 9999999)}"
                    )
                    students.append(student)
                for level in ['matric', 'intermediate']:
                    AcademicQualification.objects.create(
                        applicant=applicant,
                        exam_passed=level.capitalize(),
                        passing_year=random.randint(2019, 2024),
                        marks_obtained=random.randint(700, 1000),
                        total_marks=1100,
                        division=random.choice(['First', 'Second']),
                        subjects="Physics, Chemistry, Mathematics, English",
                        institute=fake.company(),
                        board=random.choice(['Lahore', 'Karachi', 'Federal'])
                    )

        # ===== Course Offerings =====
        self.stdout.write("Creating course offerings...")
        course_offerings = []
        for semester in semesters:
            for course in courses:
                if course.program == semester.program:
                    available_teachers = [t for t in teachers if t.department == course.department]
                    if not available_teachers:
                        self.stdout.write(self.style.WARNING(f"No teachers available for department {course.department.name} (course {course.code})"))
                        continue
                    teacher = random.choice(available_teachers)
                    offering = CourseOffering.objects.create(
                        semester=semester,
                        course=course,
                        teacher=teacher,
                    )
                    course_offerings.append(offering)

        # ===== Teacher Changes =====
        self.stdout.write("Simulating teacher changes...")
        fall_2025_offerings = [o for o in course_offerings if o.semester.is_current]
        for offering in random.sample(fall_2025_offerings, min(8, len(fall_2025_offerings))):
            old_teacher = offering.teacher
            available_teachers = [t for t in teachers if t.department == old_teacher.department and t != old_teacher]
            if not available_teachers:
                continue
            new_teacher = random.choice(available_teachers)
            CourseOfferingTeacherChange.objects.create(
                course_offering=offering,
                old_teacher=old_teacher,
                new_teacher=new_teacher,
                reason=random.choice([
                    "Teacher resigned mid-semester",
                    "Teacher on medical leave",
                    "Teacher transferred to another department"
                ])
            )
            offering.teacher = new_teacher
            offering.save()

        # ===== Assignments =====
        self.stdout.write("Creating assignments...")
        assignment_types = ['homework', 'project', 'quiz', 'lab', 'essay']
        for offering in course_offerings:
            semester_year = offering.semester.start_date.year
            semester_month = offering.semester.start_date.month
            for _ in range(random.randint(3, 5)):
                due_month = 10 if semester_month == 8 else 4
                due_date = timezone.datetime(semester_year, due_month, random.randint(1, 28), tzinfo=timezone.get_current_timezone())
                Assignment.objects.create(
                    course_offering=offering,
                    title=f"{offering.course.name} {random.choice(['Assignment', 'Project', 'Quiz'])} {random.randint(1, 5)}",
                    description=fake.paragraph(nb_sentences=5),
                    due_date=due_date,
                    max_points=random.choice([50, 100, 150]),
                    assignment_type=random.choice(assignment_types)
                )

        # ===== Submissions =====
        self.stdout.write("Creating submissions...")
        for assignment in Assignment.objects.all():
            enrolled_students = StudentEnrollment.objects.filter(course_offering=assignment.course_offering)
            for enrollment in random.sample(list(enrolled_students), min(random.randint(8, 12), len(enrolled_students))):
                Submission.objects.create(
                    assignment=assignment,
                    student=enrollment.student.user,
                    file=None,
                    text=fake.paragraph(nb_sentences=8),
                    grade=random.randint(60, assignment.max_points) if random.choice([True, False]) else None,
                    feedback=fake.sentence(nb_words=12) if random.choice([True, False]) else ""
                )

        # ===== Student Enrollments =====
        self.stdout.write("Creating student enrollments...")
        for student in students:
            current_semester = next((s for s in semesters if s.program == student.applicant.program and s.is_current), None)
            if not current_semester:
                continue
            available_offerings = list(CourseOffering.objects.filter(semester=current_semester))
            if not available_offerings:
                self.stdout.write(self.style.WARNING(f"No course offerings for semester {current_semester.name}"))
                continue
            num_offerings = min(random.randint(2, 4), len(available_offerings))
            if num_offerings <= 0:
                continue
            offerings = random.sample(available_offerings, num_offerings)
            for offering in offerings:
                try:
                    StudentEnrollment.objects.create(
                        student=student.applicant,
                        course_offering=offering,
                        status='enrolled'
                    )
                except IntegrityError:
                    continue

        # ===== News, Events, Sliders, Alumni, Gallery =====
        self.stdout.write("Creating additional site elements...")
        for _ in range(12):
            News.objects.create(
                title=fake.sentence(nb_words=6),
                content=fake.paragraph(nb_sentences=10),
                is_published=True
            )
        for _ in range(10):
            start_date = timezone.datetime(2025, random.randint(8, 11), random.randint(1, 30), tzinfo=timezone.get_current_timezone())
            Event.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=8),
                event_start_date=start_date,
                event_end_date=start_date + timedelta(hours=random.randint(2, 6)),
                created_at=timezone.now(),
                location=fake.address()
            )
        for _ in range(5):
            Slider.objects.create(
                title=fake.sentence(nb_words=4),
                image=None,
                is_active=True
            )
        for _ in range(15):
            Alumni.objects.create(
                name=fake.name(),
                graduation_year=random.randint(2015, 2024),
                profession=fake.job(),
                testimonial=fake.paragraph(nb_sentences=5),
                image=None
            )
        for _ in range(20):
            Gallery.objects.create(
                title=fake.sentence(nb_words=5),
                image=None
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with BS programs for Fall 2021-2025 and other cycles!'))