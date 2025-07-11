import os
import django
import random
from datetime import datetime, timedelta
from faker import Faker
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.db import transaction, IntegrityError
import sys
import time
import logging
from io import StringIO
from contextlib import redirect_stdout

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress Faker provider logs
logging.getLogger('faker.factory').setLevel(logging.ERROR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import models
from users.models import CustomUser
from academics.models import Faculty, Department, Program, Semester
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from faculty_staff.models import Teacher, TeacherDetails, Office, OfficeStaff
from courses.models import Course, CourseOffering, Venue, TimetableSlot, StudyMaterial, Assignment, AssignmentSubmission, Notice, ExamResult, Attendance, Quiz, Question, Option, QuizSubmission
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment

# Initialize Faker
fake = Faker()

# Muslim names
MUSLIM_MALE_NAMES = [
    'Ahmed', 'Mohammad', 'Ali', 'Hassan', 'Hussain', 'Abdullah', 'Omar', 'Ibrahim', 'Yusuf', 'Bilal',
    'Khalid', 'Usman', 'Saad', 'Faisal', 'Zain', 'Hamza', 'Ammar', 'Tahir', 'Sami', 'Rashid'
]
MUSLIM_FEMALE_NAMES = [
    'Fatima', 'Ayesha', 'Maryam', 'Zainab', 'Hafsa', 'Khadija', 'Sumaya', 'Asma', 'Rukhsar', 'Sana',
    'Amna', 'Sadia', 'Bushra', 'Fiza', 'Noor', 'Iqra', 'Mahnoor', 'Amina', 'Saba', 'Hina'
]
MUSLIM_LAST_NAMES = [
    'Khan', 'Ahmed', 'Malik', 'Siddiqui', 'Rahman', 'Hussain', 'Sheikh', 'Ali', 'Mahmood', 'Qureshi',
    'Abdullah', 'Sayed', 'Farooqi', 'Ansari', 'Chaudhry', 'Mirza', 'Baig', 'Raza', 'Iqbal', 'Zafar'
]

# Configuration
FACULTIES = [
    {'name': 'Faculty of Engineering and Technology', 'departments': [
        {'name': 'Department of Computer Science', 'code': 'CS', 'programs': [
            ('BS Computer Science', 'BS'), ('MS Computer Science', 'MS')
        ]},
        {'name': 'Department of Electrical Engineering', 'code': 'EE', 'programs': [
            ('BS Electrical Engineering', 'BS'), ('MS Electrical Engineering', 'MS')
        ]}
    ]}
]
BS_SESSIONS = [
    {'name': '2021-2025', 'start_year': 2021, 'end_year': 2025, 'semesters': 8},
    {'name': '2022-2026', 'start_year': 2022, 'end_year': 2026, 'semesters': 6},
    {'name': '2023-2027', 'start_year': 2023, 'end_year': 2027, 'semesters': 4},
    {'name': '2024-2028', 'start_year': 2024, 'end_year': 2028, 'semesters': 2},
]
MS_SESSIONS = [
    {'name': '2023-2025', 'start_year': 2023, 'end_year': 2025, 'semesters': 4},
    {'name': '2024-2026', 'start_year': 2024, 'end_year': 2026, 'semesters': 2},
]
STUDENTS_PER_SESSION = 5
TEACHERS_PER_DEPARTMENT = 10
ATTENDANCE_PER_STUDENT_PER_SEMESTER = 5
ASSIGNMENTS_PER_STUDENT_PER_SEMESTER = 3
QUIZZES_PER_STUDENT_PER_SEMESTER = 3
NOTICES_PER_SESSION = 5
NUM_OFFICES = 3
NUM_OFFICE_STAFF_PER_OFFICE = 3
NUM_VENUES_PER_DEPARTMENT = 3
NUM_COURSES_PER_DEPARTMENT = 5

def create_fake_image():
    """Create a dummy image file for testing."""
    logger.debug("Generating fake image")
    return SimpleUploadedFile(
        name=f"fake_image_{uuid.uuid4()}.jpg",
        content=b'',
        content_type='image/jpeg'
    )

def create_fake_file(extension='pdf'):
    """Create a dummy file for testing."""
    logger.debug(f"Generating fake file with extension {extension}")
    return SimpleUploadedFile(
        name=f"fake_file_{uuid.uuid4()}.{extension}",
        content=b'',
        content_type=f'application/{extension}'
    )

def generate_muslim_name():
    """Generate a Muslim full name."""
    logger.debug("Generating Muslim name")
    gender = random.choice(['male', 'female'])
    first_name = random.choice(MUSLIM_MALE_NAMES if gender == 'male' else MUSLIM_FEMALE_NAMES)
    last_name = random.choice(MUSLIM_LAST_NAMES)
    return first_name, last_name

def create_users(num_users, existing_emails):
    """Create CustomUser records, skipping existing emails."""
    users = []
    user_objects = []
    user_count = 0
    now = timezone.now()
    output = StringIO()
    emails = set()
    
    with redirect_stdout(output):
        # Pre-generate emails and names
        names = [generate_muslim_name() for _ in range(num_users)]
        for i in range(num_users):
            first_name, last_name = names[i]
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
            attempts = 0
            while email in existing_emails or email in emails:
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 1000)}@{fake.domain_name()}"
                attempts += 1
                if attempts > 100:
                    print(f"Skipping User due to email generation failure")
                    logger.warning(f"Skipping User due to email generation failure")
                    continue
            # Check if email already exists in the database
            if CustomUser.objects.filter(email=email).exists():
                print(f"Skipping existing user: {email}")
                logger.debug(f"Skipping existing user: {email}")
                users.append(CustomUser.objects.get(email=email))
                continue
            emails.add(email)
            user = CustomUser(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=random.choice([True, False]),
                is_active=True,
                date_joined=now,
                last_login=now,
                info=fake.text(max_nb_chars=200),
                profile_picture=create_fake_image()
            )
            user.set_password('password123')
            user_objects.append(user)
            user_count += 1
            print(f"{user_count} user created: {email}")
            logger.debug(f"User {user_count}: {email}")
            if user_count % 100 == 0:
                print(output.getvalue(), end='', flush=True)
                output.truncate(0)
                output.seek(0)
        
        try:
            with transaction.atomic():
                CustomUser.objects.bulk_create(user_objects, ignore_conflicts=True)
                users.extend(list(CustomUser.objects.filter(email__in=emails)))
                print(f"Created {len(user_objects)} new users successfully")
                logger.debug(f"Created {len(user_objects)} new users")
        except IntegrityError as e:
            print(f"Error during bulk user creation: {str(e)}")
            logger.error(f"Error during bulk user creation: {str(e)}")
            for user in user_objects:
                try:
                    user.save()
                    users.append(user)
                except IntegrityError:
                    print(f"Skipping User '{user.email}' due to conflict")
                    logger.warning(f"Skipping User '{user.email}' due to conflict")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return users

def create_faculties_departments_programs():
    """Create Faculty, Department, and Program records, skipping existing ones."""
    faculties = []
    departments = []
    programs = []
    faculty_count = 0
    department_count = 0
    program_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for faculty_data in FACULTIES:
                # Check if faculty exists
                slug = fake.slug(faculty_data['name'])
                if Faculty.objects.filter(slug=slug).exists():
                    print(f"Skipping existing Faculty '{faculty_data['name']}'")
                    logger.debug(f"Skipping existing Faculty '{faculty_data['name']}'")
                    faculties.append(Faculty.objects.get(slug=slug))
                    faculty_count += 1
                    continue
                try:
                    faculty = Faculty(
                        name=faculty_data['name'],
                        slug=slug,
                        description=fake.text(max_nb_chars=500)
                    )
                    faculty.save()
                    faculties.append(faculty)
                    faculty_count += 1
                    print(f"{faculty_count} faculty created: {faculty_data['name']}")
                    logger.debug(f"Faculty {faculty_count}: {faculty_data['name']}")
                except IntegrityError:
                    print(f"Skipping Faculty '{faculty_data['name']}' due to conflict")
                    logger.warning(f"Skipping Faculty '{faculty_data['name']}' due to conflict")
                    continue
                for dept_data in faculty_data['departments']:
                    # Check if department exists
                    dept_slug = fake.slug(dept_data['name'])
                    if Department.objects.filter(slug=dept_slug, code=dept_data['code']).exists():
                        print(f"Skipping existing Department '{dept_data['name']}'")
                        logger.debug(f"Skipping existing Department '{dept_data['name']}'")
                        departments.append(Department.objects.get(slug=dept_slug, code=dept_data['code']))
                        department_count += 1
                        continue
                    try:
                        department = Department(
                            faculty=faculty,
                            name=dept_data['name'],
                            slug=dept_slug,
                            code=dept_data['code'],
                            image=create_fake_image(),
                            introduction=fake.text(max_nb_chars=300),
                            details=fake.text(max_nb_chars=1000)
                        )
                        department.save()
                        departments.append(department)
                        department_count += 1
                        print(f"{department_count} department created: {dept_data['name']}")
                        logger.debug(f"Department {department_count}: {dept_data['name']}")
                    except IntegrityError:
                        print(f"Skipping Department '{dept_data['name']}' due to conflict")
                        logger.warning(f"Skipping Department '{dept_data['name']}' due to conflict")
                        continue
                    for program_name, degree_type in dept_data['programs']:
                        # Check if program exists
                        if Program.objects.filter(name=program_name, department=department).exists():
                            print(f"Skipping existing Program '{program_name}'")
                            logger.debug(f"Skipping existing Program '{program_name}'")
                            programs.append(Program.objects.get(name=program_name, department=department))
                            program_count += 1
                            continue
                        try:
                            program = Program(
                                department=department,
                                name=program_name,
                                degree_type=degree_type,
                                duration_years=4 if degree_type == 'BS' else 2,
                                total_semesters=8 if degree_type == 'BS' else 4,
                                start_year=2021 if degree_type == 'BS' else 2023,
                                end_year=None,
                                is_active=True,
                                created_at=now,
                                updated_at=now
                            )
                            program.save()
                            programs.append(program)
                            program_count += 1
                            print(f"{program_count} program created: {program_name}")
                            logger.debug(f"Program {program_count}: {program_name}")
                        except IntegrityError:
                            print(f"Skipping Program '{program_name}' due to conflict")
                            logger.warning(f"Skipping Program '{program_name}' due to conflict")
                            continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return faculties, departments, programs

def create_sessions_semesters(programs):
    """Create AcademicSession and Semester records, skipping existing ones."""
    sessions = []
    semesters = []
    session_count = 0
    semester_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session_data in BS_SESSIONS + MS_SESSIONS:
                # Check if session exists
                if AcademicSession.objects.filter(name=session_data['name']).exists():
                    print(f"Skipping existing Session '{session_data['name']}'")
                    logger.debug(f"Skipping existing Session '{session_data['name']}'")
                    sessions.append(AcademicSession.objects.get(name=session_data['name']))
                    session_count += 1
                    continue
                try:
                    session = AcademicSession(
                        name=session_data['name'],
                        start_year=session_data['start_year'],
                        end_year=session_data['end_year'],
                        is_active=(session_data['start_year'] == 2024),
                        description=fake.text(max_nb_chars=500),
                        created_at=now,
                        updated_at=now
                    )
                    session.save()
                    sessions.append(session)
                    session_count += 1
                    print(f"{session_count} session created: {session_data['name']}")
                    logger.debug(f"Session {session_count}: {session_data['name']}")
                except IntegrityError:
                    print(f"Skipping Session '{session_data['name']}' due to conflict")
                    logger.warning(f"Skipping Session '{session_data['name']}' due to conflict")
                    continue
            for session in sessions:
                session_info = next(s for s in (BS_SESSIONS + MS_SESSIONS) if s['name'] == session.name)
                num_semesters = session_info['semesters']
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for program in applicable_programs:
                    for number in range(1, num_semesters + 1):
                        # Check if semester exists
                        if Semester.objects.filter(program=program, session=session, number=number).exists():
                            print(f"Skipping existing Semester {number} for {program.name} in {session.name}")
                            logger.debug(f"Skipping existing Semester {number} for {program.name}")
                            semesters.append(Semester.objects.get(program=program, session=session, number=number))
                            semester_count += 1
                            continue
                        try:
                            start_date = datetime(session.start_year, 1 + 6 * ((number - 1) % 2), 1)
                            end_date = start_date + timedelta(days=180)
                            semester = Semester(
                                program=program,
                                session=session,
                                number=number,
                                name=f"Semester {number}",
                                description=fake.text(max_nb_chars=300),
                                start_time=start_date,
                                end_time=end_date,
                                is_active=(number == session_info['semesters'] and session.start_year == 2024)
                            )
                            semester.save()
                            semesters.append(semester)
                            semester_count += 1
                            print(f"{semester_count} semester created: Semester {number} for {program.name}")
                            logger.debug(f"Semester {semester_count}: Semester {number} for {program.name}")
                        except IntegrityError:
                            print(f"Skipping Semester {number} for {program.name} in {session.name}")
                            logger.warning(f"Skipping Semester {number} for {program.name} in {session.name}")
                            continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return sessions, semesters

def create_teachers(departments, users, start_index):
    """Create Teacher and TeacherDetails records, skipping existing ones."""
    teachers = []
    teacher_details = []
    user_index = start_index
    teacher_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            # Create Teacher objects first
            teacher_objects = []
            for department in departments:
                hod_created = False
                for _ in range(TEACHERS_PER_DEPARTMENT):
                    if user_index >= len(users):
                        print("Not enough users for teachers")
                        logger.warning("Not enough users for teachers")
                        break
                    user = users[user_index]
                    user_index += 1
                    designation = 'head_of_department' if not hod_created else 'professor'
                    hod_created = True if designation == 'head_of_department' else hod_created
                    # Check if teacher exists
                    if Teacher.objects.filter(user=user, department=department).exists():
                        print(f"Skipping existing Teacher for user '{user.email}'")
                        logger.debug(f"Skipping existing Teacher for user '{user.email}'")
                        teachers.append(Teacher.objects.get(user=user, department=department))
                        teacher_count += 1
                        continue
                    try:
                        teacher = Teacher(
                            user=user,
                            department=department,
                            designation=designation,
                            contact_no=fake.phone_number()[:15],
                            qualification=fake.sentence(),
                            hire_date=fake.date_this_decade(),
                            is_active=True,
                            linkedin_url=fake.url(),
                            twitter_url=fake.url(),
                            personal_website=fake.url(),
                            experience=fake.text(max_nb_chars=500)
                        )
                        teacher_objects.append(teacher)
                        teacher_count += 1
                        print(f"{teacher_count} teacher created: {user.email}")
                        logger.debug(f"Teacher {teacher_count}: {user.email}")
                    except IntegrityError:
                        print(f"Skipping Teacher for user '{user.email}' due to conflict")
                        logger.warning(f"Skipping Teacher for user '{user.email}' due to conflict")
                        user_index -= 1
                        continue
            # Save Teachers to get IDs
            Teacher.objects.bulk_create(teacher_objects, ignore_conflicts=True)
            teachers.extend(list(Teacher.objects.filter(user__in=[u.id for u in users[start_index:user_index]])))
            # Create TeacherDetails with saved Teachers
            for teacher in teachers:
                # Check if TeacherDetails exists
                if TeacherDetails.objects.filter(teacher=teacher).exists():
                    print(f"Skipping existing TeacherDetails for teacher '{teacher.user.email}'")
                    logger.debug(f"Skipping existing TeacherDetails for teacher '{teacher.user.email}'")
                    teacher_details.append(TeacherDetails.objects.get(teacher=teacher))
                    continue
                try:
                    teacher_detail = TeacherDetails(
                        teacher=teacher,
                        employment_type=random.choice(['visitor', 'contract', 'permanent']),
                        salary_per_lecture=random.uniform(50.0, 200.0),
                        fixed_salary=random.uniform(5000.0, 20000.0),
                        status=random.choice(['on_break', 'on_lecture', 'on_leave', 'available']),
                        last_updated=now
                    )
                    teacher_details.append(teacher_detail)
                except IntegrityError:
                    print(f"Skipping TeacherDetails for teacher '{teacher.user.email}' due to conflict")
                    logger.warning(f"Skipping TeacherDetails for teacher '{teacher.user.email}' due to conflict")
                    continue
            TeacherDetails.objects.bulk_create(teacher_details, ignore_conflicts=True)
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return teachers, user_index

def create_courses(departments, existing_course_codes):
    """Create Course records, skipping existing ones."""
    courses = []
    course_objects = []
    course_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for department in departments:
                for i in range(NUM_COURSES_PER_DEPARTMENT):
                    code = f"{department.code}{100 + i}"
                    attempts = 0
                    while code in existing_course_codes:
                        code = f"{department.code}{100 + i + random.randint(1, 1000)}"
                        attempts += 1
                        if attempts > 100:
                            print(f"Skipping Course due to code generation failure")
                            logger.warning(f"Skipping Course due to code generation failure")
                            continue
                    # Check if course exists
                    if Course.objects.filter(code=code).exists():
                        print(f"Skipping existing Course '{code}'")
                        logger.debug(f"Skipping existing Course '{code}'")
                        courses.append(Course.objects.get(code=code))
                        course_count += 1
                        continue
                    existing_course_codes.add(code)
                    course = Course(
                        opt=random.choice([True, False]),
                        code=code,
                        name=fake.catch_phrase(),
                        credits=random.randint(1, 4),
                        lab_work=random.randint(0, 2),
                        is_active=True,
                        description=fake.text(max_nb_chars=500)
                    )
                    course_objects.append(course)
                    course_count += 1
                    print(f"{course_count} course created: {code}")
                    logger.debug(f"Course {course_count}: {code}")
            Course.objects.bulk_create(course_objects, ignore_conflicts=True)
            courses.extend(list(Course.objects.filter(code__in=[c.code for c in course_objects])))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return courses

def create_course_offerings(semesters, courses, teachers):
    """Create exactly 3 CourseOffering records per semester with shuffled teachers, skipping existing ones."""
    course_offerings = []
    offering_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for semester in semesters:
                # Select up to 3 random courses (no department filtering)
                if len(courses) < 3:
                    print(f"Warning: Not enough courses ({len(courses)}) to assign 3 offerings for {semester.program.department.name}")
                    logger.warning(f"Not enough courses ({len(courses)}) for {semester.program.department.name}")
                    continue
                selected_courses = random.sample(courses, min(3, len(courses)))
                # Filter teachers by department
                department_teachers = [t for t in teachers if t.department == semester.program.department]
                if not department_teachers:
                    print(f"No teachers available for {semester.program.department.name}")
                    logger.warning(f"No teachers available for {semester.program.department.name}")
                    continue
                for course in selected_courses:
                    # Check if course offering exists
                    if CourseOffering.objects.filter(course=course, semester=semester).exists():
                        print(f"Skipping existing CourseOffering for {course.code} in {semester.name}")
                        logger.debug(f"Skipping existing CourseOffering for {course.code} in {semester.name}")
                        course_offerings.append(CourseOffering.objects.get(course=course, semester=semester))
                        offering_count += 1
                        continue
                    try:
                        offering = CourseOffering(
                            course=course,
                            teacher=random.choice(department_teachers),
                            department=semester.program.department,
                            program=semester.program,
                            academic_session=semester.session,
                            semester=semester,
                            is_active=True,
                            current_enrollment=STUDENTS_PER_SESSION,
                            shift=random.choice(['morning', 'evening', 'both']),
                            offering_type=random.choice([choice[0] for choice in CourseOffering.OFFERING_TYPES])
                        )
                        offering.save()
                        course_offerings.append(offering)
                        offering_count += 1
                        print(f"{offering_count} course offering created: {course.code} in {semester.name}")
                        logger.debug(f"Course offering {offering_count}: {course.code} in {semester.name}")
                    except IntegrityError:
                        print(f"Skipping CourseOffering for {course.code} in {semester.name}")
                        logger.warning(f"Skipping CourseOffering for {course.code} in {semester.name}")
                        continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return course_offerings

def create_venues(departments):
    """Create Venue records, skipping existing ones."""
    venues = []
    venue_objects = []
    venue_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for department in departments:
                for i in range(NUM_VENUES_PER_DEPARTMENT):
                    name = f"Room {department.code}-{i + 1}"
                    # Check if venue exists
                    if Venue.objects.filter(name=name, department=department).exists():
                        print(f"Skipping existing Venue '{name}'")
                        logger.debug(f"Skipping existing Venue '{name}'")
                        venues.append(Venue.objects.get(name=name, department=department))
                        venue_count += 1
                        continue
                    venue = Venue(
                        name=name,
                        department=department,
                        capacity=random.randint(20, 100),
                        is_active=True
                    )
                    venue_objects.append(venue)
                    venue_count += 1
                    print(f"{venue_count} venue created: {name}")
                    logger.debug(f"Venue {venue_count}: {name}")
            Venue.objects.bulk_create(venue_objects, ignore_conflicts=True)
            venues.extend(list(Venue.objects.filter(name__in=[v.name for v in venue_objects])))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return venues

def create_timetable_slots(course_offerings, venues):
    """Create TimetableSlot records, skipping existing ones."""
    timetable_slots = []
    slot_count = 0
    output = StringIO()
    days = [choice[0] for choice in TimetableSlot.DAYS_OF_WEEK]
    
    with redirect_stdout(output):
        with transaction.atomic():
            for offering in course_offerings:
                for _ in range(random.randint(1, 3)):
                    start_time = fake.time_object()
                    start_datetime = datetime.combine(datetime.today(), start_time)
                    end_time = (start_datetime + timedelta(hours=1)).time()
                    day = random.choice(days)
                    venue = random.choice([v for v in venues if v.department == offering.department])
                    # Check if timetable slot exists
                    if TimetableSlot.objects.filter(course_offering=offering, day=day, start_time=start_time, venue=venue).exists():
                        print(f"Skipping existing TimetableSlot for {offering.course.code} on {day}")
                        logger.debug(f"Skipping existing TimetableSlot for {offering.course.code} on {day}")
                        timetable_slots.append(TimetableSlot.objects.filter(course_offering=offering, day=day, start_time=start_time, venue=venue).first())
                        slot_count += 1
                        continue
                    try:
                        slot = TimetableSlot(
                            course_offering=offering,
                            day=day,
                            start_time=start_time,
                            end_time=end_time,
                            venue=venue
                        )
                        slot.save()
                        timetable_slots.append(slot)
                        slot_count += 1
                        print(f"{slot_count} timetable slot created: {offering.course.code} on {day}")
                        logger.debug(f"Timetable slot {slot_count}: {offering.course.code} on {day}")
                    except (IntegrityError, ValueError) as e:
                        print(f"Skipping TimetableSlot for {offering.course.code} due to {str(e)}")
                        logger.warning(f"Skipping TimetableSlot for {offering.course.code} due to {str(e)}")
                        continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return timetable_slots

def create_admission_cycles(sessions, programs):
    """Create AdmissionCycle records, skipping existing ones."""
    admission_cycles = []
    cycle_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for program in applicable_programs:
                    # Check if admission cycle exists
                    if AdmissionCycle.objects.filter(program=program, session=session).exists():
                        print(f"Skipping existing AdmissionCycle for {program.name} in {session.name}")
                        logger.debug(f"Skipping existing AdmissionCycle for {program.name} in {session.name}")
                        admission_cycles.append(AdmissionCycle.objects.get(program=program, session=session))
                        cycle_count += 1
                        continue
                    try:
                        cycle = AdmissionCycle(
                            program=program,
                            session=session,
                            application_start=datetime(session.start_year, 1, 1),
                            application_end=datetime(session.start_year, 6, 30),
                            is_open=(session.start_year == 2024)
                        )
                        cycle.save()
                        admission_cycles.append(cycle)
                        cycle_count += 1
                        print(f"{cycle_count} admission cycle created: {program.name} in {session.name}")
                        logger.debug(f"Admission cycle {cycle_count}: {program.name} in {session.name}")
                    except IntegrityError:
                        print(f"Skipping AdmissionCycle for {program.name} in {session.name}")
                        logger.warning(f"Skipping AdmissionCycle for {program.name} in {session.name}")
                        continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return admission_cycles

def create_applicants_students(sessions, programs, users, start_index):
    """Create Applicant and Student records, skipping existing ones."""
    applicants = []
    students = []
    applicant_count = 0
    student_count = 0
    user_index = start_index
    existing_roll_nos = set(Student.objects.values_list('university_roll_no', flat=True))
    output = StringIO()
    now = timezone.now()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for program in applicable_programs:
                    for shift in ['morning', 'evening']:
                        for _ in range(STUDENTS_PER_SESSION // 2):
                            if user_index >= len(users):
                                print("Not enough users for applicants/students")
                                logger.warning("Not enough users for applicants/students")
                                break
                            user = users[user_index]
                            user_index += 1
                            # Check if applicant exists
                            if Applicant.objects.filter(user=user, session=session, program=program).exists():
                                print(f"Skipping existing Applicant for '{user.email}'")
                                logger.debug(f"Skipping existing Applicant for '{user.email}'")
                                applicants.append(Applicant.objects.get(user=user, session=session, program=program))
                                applicant_count += 1
                                # Check if student exists
                                if Student.objects.filter(user=user, program=program).exists():
                                    print(f"Skipping existing Student for '{user.email}'")
                                    logger.debug(f"Skipping existing Student for '{user.email}'")
                                    students.append(Student.objects.get(user=user, program=program))
                                    student_count += 1
                                continue
                            try:
                                first_name, last_name = generate_muslim_name()
                                applicant = Applicant(
                                    user=user,
                                    session=session,
                                    faculty=program.department.faculty,
                                    department=program.department,
                                    program=program,
                                    status='accepted',
                                    applied_at=now,
                                    applicant_photo=create_fake_image(),
                                    full_name=f"{first_name} {last_name}",
                                    religion='Islam',
                                    caste=fake.word().capitalize(),
                                    cnic=fake.numerify(text="#####-#######-#"),
                                    dob=fake.date_of_birth(minimum_age=18, maximum_age=30),
                                    contact_no=fake.phone_number()[:15],
                                    identification_mark=fake.sentence(),
                                    father_name=fake.name(),
                                    father_occupation=fake.job(),
                                    father_cnic=fake.numerify(text="#####-#######-#"),
                                    monthly_income=random.randint(50000, 200000),
                                    relationship=random.choice(['father', 'guardian']),
                                    permanent_address=fake.address(),
                                    shift=shift,
                                    declaration=True,
                                    created_at=now
                                )
                                applicant.save()
                                applicants.append(applicant)
                                applicant_count += 1
                                print(f"{applicant_count} applicant created: {user.email}")
                                logger.debug(f"Applicant {applicant_count}: {user.email}")
                                roll_no = fake.random_number(digits=8)
                                attempts = 0
                                while roll_no in existing_roll_nos:
                                    roll_no = fake.random_number(digits=8)
                                    attempts += 1
                                    if attempts > 100:
                                        print(f"Skipping Student due to roll number generation failure")
                                        logger.warning(f"Skipping Student due to roll number generation failure")
                                        break
                                if attempts <= 100:
                                    existing_roll_nos.add(roll_no)
                                    student = Student(
                                        applicant=applicant,
                                        user=user,
                                        university_roll_no=roll_no,
                                        college_roll_no=fake.random_number(digits=8),
                                        enrollment_date=datetime(session.start_year, 1, 1),
                                        program=program,
                                        current_status='active',
                                        emergency_contact=fake.name(),
                                        emergency_phone=fake.phone_number()[:15],
                                        role=random.choice(['CR', 'GR', None])
                                    )
                                    student.save()
                                    students.append(student)
                                    student_count += 1
                                    print(f"{student_count} student created: {user.email}")
                                    logger.debug(f"Student {student_count}: {user.email}")
                            except IntegrityError:
                                print(f"Skipping Applicant/Student for '{user.email}' due to conflict")
                                logger.warning(f"Skipping Applicant/Student for '{user.email}' due to conflict")
                                user_index -= 1
                                continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return applicants, students, user_index

def create_academic_qualifications(applicants):
    """Create AcademicQualification records, skipping existing ones."""
    qualifications = []
    qualification_objects = []
    qualification_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for applicant in applicants:
                for _ in range(random.randint(1, 3)):
                    exam_passed = random.choice(['Matriculation', 'FSc', "Bachelor's"])
                    passing_year = random.randint(2015, 2023)
                    # Check if qualification exists
                    if AcademicQualification.objects.filter(applicant=applicant, exam_passed=exam_passed, passing_year=passing_year).exists():
                        print(f"Skipping existing AcademicQualification for {applicant.full_name}")
                        logger.debug(f"Skipping existing AcademicQualification for {applicant.full_name}")
                        qualifications.append(AcademicQualification.objects.filter(applicant=applicant, exam_passed=exam_passed, passing_year=passing_year).first())
                        qualification_count += 1
                        continue
                    qualification = AcademicQualification(
                        applicant=applicant,
                        exam_passed=exam_passed,
                        passing_year=passing_year,
                        marks_obtained=random.randint(400, 900),
                        total_marks=1000,
                        division=random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                        subjects=', '.join(fake.words(nb=3)),
                        board=fake.company() + " Board",
                        certificate_file=create_fake_file()
                    )
                    qualification_objects.append(qualification)
                    qualification_count += 1
                    print(f"{qualification_count} academic qualification created: {applicant.full_name}")
                    logger.debug(f"Academic qualification {qualification_count}: {applicant.full_name}")
                if qualification_count % 100 == 0:
                    AcademicQualification.objects.bulk_create(qualification_objects, ignore_conflicts=True)
                    qualifications.extend(list(AcademicQualification.objects.filter(applicant__in=applicants)))
                    qualification_objects = []
                    print(output.getvalue(), end='', flush=True)
                    output.truncate(0)
                    output.seek(0)
            if qualification_objects:
                AcademicQualification.objects.bulk_create(qualification_objects, ignore_conflicts=True)
                qualifications.extend(list(AcademicQualification.objects.filter(applicant__in=applicants)))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return qualifications

def create_extracurricular_activities(applicants):
    """Create ExtraCurricularActivity records, skipping existing ones."""
    activities = []
    activity_objects = []
    activity_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for applicant in applicants:
                for _ in range(random.randint(0, 2)):
                    activity_name = fake.catch_phrase()
                    activity_year = random.randint(2015, 2023)
                    # Check if activity exists
                    if ExtraCurricularActivity.objects.filter(applicant=applicant, activity=activity_name, activity_year=activity_year).exists():
                        print(f"Skipping existing ExtraCurricularActivity for {applicant.full_name}")
                        logger.debug(f"Skipping existing ExtraCurricularActivity for {applicant.full_name}")
                        activities.append(ExtraCurricularActivity.objects.filter(applicant=applicant, activity=activity_name, activity_year=activity_year).first())
                        activity_count += 1
                        continue
                    activity = ExtraCurricularActivity(
                        applicant=applicant,
                        activity=activity_name,
                        position=random.choice(['Captain', 'Secretary', 'Member']),
                        achievement=fake.sentence(),
                        activity_year=activity_year,
                        certificate_file=create_fake_file()
                    )
                    activity_objects.append(activity)
                    activity_count += 1
                    print(f"{activity_count} extracurricular activity created: {applicant.full_name}")
                    logger.debug(f"Extracurricular activity {activity_count}: {applicant.full_name}")
                if activity_count % 100 == 0:
                    ExtraCurricularActivity.objects.bulk_create(activity_objects, ignore_conflicts=True)
                    activities.extend(list(ExtraCurricularActivity.objects.filter(applicant__in=applicants)))
                    activity_objects = []
                    print(output.getvalue(), end='', flush=True)
                    output.truncate(0)
                    output.seek(0)
            if activity_objects:
                ExtraCurricularActivity.objects.bulk_create(activity_objects, ignore_conflicts=True)
                activities.extend(list(ExtraCurricularActivity.objects.filter(applicant__in=applicants)))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return activities

def create_semester_enrollments(students, semesters):
    """Create StudentSemesterEnrollment records, skipping existing ones."""
    semester_enrollments = []
    enrollment_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for student in students:
                applicable_semesters = [s for s in semesters if s.program == student.program and s.session == student.applicant.session]
                for semester in applicable_semesters:
                    # Check if enrollment exists
                    if StudentSemesterEnrollment.objects.filter(student=student, semester=semester).exists():
                        print(f"Skipping existing SemesterEnrollment for {student.user.email} in {semester.name}")
                        logger.debug(f"Skipping existing SemesterEnrollment for {student.user.email} in {semester.name}")
                        semester_enrollments.append(StudentSemesterEnrollment.objects.get(student=student, semester=semester))
                        enrollment_count += 1
                        continue
                    try:
                        enrollment = StudentSemesterEnrollment(
                            student=student,
                            semester=semester,
                            enrollment_date=semester.start_time,
                            status='enrolled'
                        )
                        enrollment.save()
                        semester_enrollments.append(enrollment)
                        enrollment_count += 1
                        print(f"{enrollment_count} semester enrollment created: {student.user.email} in {semester.name}")
                        logger.debug(f"Semester enrollment {enrollment_count}: {student.user.email} in {semester.name}")
                    except IntegrityError:
                        print(f"Skipping SemesterEnrollment for {student.user.email} in {semester.name}")
                        logger.warning(f"Skipping SemesterEnrollment for {student.user.email} in {semester.name}")
                        continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return semester_enrollments

def create_course_enrollments(semester_enrollments, course_offerings):
    """Create CourseEnrollment records, skipping existing ones."""
    course_enrollments = []
    enrollment_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for enrollment in semester_enrollments:
                applicable_offerings = [co for co in course_offerings if co.semester == enrollment.semester]
                for offering in applicable_offerings:
                    # Check if course enrollment exists
                    if CourseEnrollment.objects.filter(student_semester_enrollment=enrollment, course_offering=offering).exists():
                        print(f"Skipping existing CourseEnrollment for {enrollment.student.user.email} in {offering.course.code}")
                        logger.debug(f"Skipping existing CourseEnrollment for {enrollment.student.user.email} in {offering.course.code}")
                        course_enrollments.append(CourseEnrollment.objects.get(student_semester_enrollment=enrollment, course_offering=offering))
                        enrollment_count += 1
                        continue
                    try:
                        course_enrollment = CourseEnrollment(
                            student_semester_enrollment=enrollment,
                            course_offering=offering,
                            enrollment_date=enrollment.enrollment_date,
                            status='enrolled'
                        )
                        course_enrollment.save()
                        course_enrollments.append(course_enrollment)
                        enrollment_count += 1
                        print(f"{enrollment_count} course enrollment created: {enrollment.student.user.email} in {offering.course.code}")
                        logger.debug(f"Course enrollment {enrollment_count}: {enrollment.student.user.email} in {offering.course.code}")
                    except IntegrityError:
                        print(f"Skipping CourseEnrollment for {enrollment.student.user.email} in {offering.course.code}")
                        logger.warning(f"Skipping CourseEnrollment for {enrollment.student.user.email} in {offering.course.code}")
                        continue
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return course_enrollments

def create_academic_records(semester_enrollments, course_offerings, teachers):
    """Create Attendance, Assignment, Quiz, and ExamResult records, skipping existing ones."""
    attendances = []
    assignments = []
    assignment_submissions = []
    quizzes = []
    questions = []
    options = []
    quiz_submissions = []
    exam_results = []
    attendance_objects = []
    assignment_objects = []
    submission_objects = []
    quiz_objects = []
    question_objects = []
    option_objects = []
    quiz_submission_objects = []
    exam_result_objects = []
    attendance_count = 0
    assignment_count = 0
    submission_count = 0
    quiz_count = 0
    question_count = 0
    option_count = 0
    quiz_submission_count = 0
    exam_result_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for enrollment in semester_enrollments:
                applicable_offerings = [co for co in course_offerings if co.semester == enrollment.semester]
                for offering in applicable_offerings:
                    student = enrollment.student
                    semester = enrollment.semester
                    # Attendance
                    for _ in range(ATTENDANCE_PER_STUDENT_PER_SEMESTER):
                        date = fake.date_between(start_date=semester.start_time, end_date=semester.end_time)
                        shift = offering.shift if offering.shift != 'both' else student.applicant.shift
                        # Check if attendance exists
                        if Attendance.objects.filter(student=student, course_offering=offering, date=date).exists():
                            print(f"Skipping existing Attendance for {student.user.email} in {offering.course.code}")
                            logger.debug(f"Skipping existing Attendance for {student.user.email} in {offering.course.code}")
                            attendances.append(Attendance.objects.filter(student=student, course_offering=offering, date=date).first())
                            attendance_count += 1
                            continue
                        attendance = Attendance(
                            student=student,
                            course_offering=offering,
                            date=date,
                            status=random.choice([choice[0] for choice in Attendance.STATUS_CHOICES]),
                            shift=shift,
                            recorded_by=offering.teacher,
                            recorded_at=now
                        )
                        attendance_objects.append(attendance)
                        attendance_count += 1
                        print(f"{attendance_count} attendance created: {student.user.email} in {offering.course.code}")
                        logger.debug(f"Attendance {attendance_count}: {student.user.email} in {offering.course.code}")
                        if attendance_count % 1000 == 0:
                            Attendance.objects.bulk_create(attendance_objects, ignore_conflicts=True)
                            attendances.extend(list(Attendance.objects.filter(student__in=[s.id for s in semester_enrollments])))
                            attendance_objects = []
                            print(output.getvalue(), end='', flush=True)
                            output.truncate(0)
                            output.seek(0)
                    # Assignments
                    for _ in range(ASSIGNMENTS_PER_STUDENT_PER_SEMESTER):
                        title = fake.catch_phrase()
                        due_date = fake.date_between(start_date=semester.start_time, end_date=semester.end_time)
                        # Check if assignment exists
                        if Assignment.objects.filter(course_offering=offering, title=title).exists():
                            print(f"Skipping existing Assignment '{title}' in {offering.course.code}")
                            logger.debug(f"Skipping existing Assignment '{title}' in {offering.course.code}")
                            assignments.append(Assignment.objects.filter(course_offering=offering, title=title).first())
                            assignment_count += 1
                            continue
                        assignment = Assignment(
                            course_offering=offering,
                            teacher=offering.teacher,
                            title=title,
                            description=fake.text(max_nb_chars=500),
                            due_date=due_date,
                            max_points=100,
                            resource_file=create_fake_file(),
                            created_at=now,
                            updated_at=now
                        )
                        assignment_objects.append(assignment)
                        assignment_count += 1
                        print(f"{assignment_count} assignment created: {offering.course.code}")
                        logger.debug(f"Assignment {assignment_count}: {offering.course.code}")
                    
                    # Save assignments before checking submissions
                    if assignment_objects:
                        Assignment.objects.bulk_create(assignment_objects, ignore_conflicts=True)
                        assignments.extend(list(Assignment.objects.filter(course_offering=offering, title__in=[a.title for a in assignment_objects])))
                        assignment_objects = []
                    
                    # Assignment Submissions
                    for assignment in assignments:
                        if assignment.course_offering != offering:
                            continue
                        # Check if assignment submission exists
                        if AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
                            print(f"Skipping existing AssignmentSubmission for {student.user.email} in {offering.course.code}")
                            logger.debug(f"Skipping existing AssignmentSubmission for {student.user.email} in {offering.course.code}")
                            assignment_submissions.append(AssignmentSubmission.objects.filter(assignment=assignment, student=student).first())
                            submission_count += 1
                            continue
                        submission = AssignmentSubmission(
                            assignment=assignment,
                            student=student,
                            content=fake.text(max_nb_chars=500),
                            file=create_fake_file(),
                            submitted_at=assignment.due_date,
                            marks_obtained=random.randint(0, 100),
                            feedback=fake.text(max_nb_chars=200),
                            graded_by=offering.teacher,
                            graded_at=now
                        )
                        submission_objects.append(submission)
                        submission_count += 1
                        print(f"{submission_count} assignment submission created: {student.user.email} in {offering.course.code}")
                        logger.debug(f"Assignment submission {submission_count}: {student.user.email} in {offering.course.code}")
                        if submission_count % 1000 == 0:
                            AssignmentSubmission.objects.bulk_create(submission_objects, ignore_conflicts=True)
                            assignment_submissions.extend(list(AssignmentSubmission.objects.filter(student__in=[s.id for s in semester_enrollments])))
                            submission_objects = []
                            print(output.getvalue(), end='', flush=True)
                            output.truncate(0)
                            output.seek(0)
                    # Quizzes
                    for _ in range(QUIZZES_PER_STUDENT_PER_SEMESTER):
                        title = fake.catch_phrase()
                        # Check if quiz exists
                        if Quiz.objects.filter(course_offering=offering, title=title).exists():
                            print(f"Skipping existing Quiz '{title}' in {offering.course.code}")
                            logger.debug(f"Skipping existing Quiz '{title}' in {offering.course.code}")
                            quizzes.append(Quiz.objects.filter(course_offering=offering, title=title).first())
                            quiz_count += 1
                            continue
                        quiz = Quiz(
                            course_offering=offering,
                            title=title,
                            publish_flag=True,
                            timer_seconds=random.choice([15, 30, 45, 60]),
                            created_at=now,
                            updated_at=now
                        )
                        quiz_objects.append(quiz)
                        quiz_count += 1
                        print(f"{quiz_count} quiz created: {title} in {offering.course.code}")
                        logger.debug(f"Quiz {quiz_count}: {title} in {offering.course.code}")
                    # Save quizzes to assign IDs
                    if quiz_objects:
                        Quiz.objects.bulk_create(quiz_objects, ignore_conflicts=True)
                        quizzes.extend(list(Quiz.objects.filter(course_offering__in=[o.id for o in course_offerings])))
                        quiz_objects = []
                    # Questions
                    for quiz in quizzes:
                        if quiz.course_offering != offering:
                            continue
                        for _ in range(random.randint(3, 5)):
                            text = fake.sentence()
                            # Check if question exists
                            if Question.objects.filter(quiz=quiz, text=text).exists():
                                print(f"Skipping existing Question '{text}' in {quiz.title}")
                                logger.debug(f"Skipping existing Question '{text}' in {quiz.title}")
                                questions.append(Question.objects.filter(quiz=quiz, text=text).first())
                                question_count += 1
                                continue
                            question = Question(
                                quiz=quiz,
                                text=text,
                                marks=random.randint(1, 5),
                                created_at=now
                            )
                            question_objects.append(question)
                            question_count += 1
                            print(f"{question_count} question created: {text} in {quiz.title}")
                            logger.debug(f"Question {question_count}: {text} in {quiz.title}")
                        if question_count % 1000 == 0:
                            Question.objects.bulk_create(question_objects, ignore_conflicts=True)
                            questions.extend(list(Question.objects.filter(quiz__in=quizzes)))
                            question_objects = []
                            print(output.getvalue(), end='', flush=True)
                            output.truncate(0)
                            output.seek(0)
                    # Save questions
                    if question_objects:
                        Question.objects.bulk_create(question_objects, ignore_conflicts=True)
                        questions.extend(list(Question.objects.filter(quiz__in=quizzes)))
                        question_objects = []
                    # Options
                    for question in questions:
                        if question.quiz.course_offering != offering:
                            continue
                        correct_option = random.randint(1, 4)
                        for i in range(1, 5):
                            text = fake.word().capitalize()
                            # Check if option exists
                            if Option.objects.filter(question=question, text=text).exists():
                                print(f"Skipping existing Option '{text}' for {question.text}")
                                logger.debug(f"Skipping existing Option '{text}' for {question.text}")
                                # Use first matching option to avoid MultipleObjectsReturned
                                existing_option = Option.objects.filter(question=question, text=text).first()
                                if existing_option:
                                    options.append(existing_option)
                                    option_count += 1
                                continue
                            option = Option(
                                question=question,
                                text=text,
                                is_correct=(i == correct_option)
                            )
                            option_objects.append(option)
                            option_count += 1
                            print(f"{option_count} option created: {text} for {question.text}")
                            logger.debug(f"Option {option_count}: {text} for {question.text}")
                        if option_count % 10000 == 0:
                            Option.objects.bulk_create(option_objects, ignore_conflicts=True)
                            options.extend(list(Option.objects.filter(question__in=questions)))
                            option_objects = []
                            print(output.getvalue(), end='', flush=True)
                            output.truncate(0)
                            output.seek(0)
                    # Save options
                    if option_objects:
                        Option.objects.bulk_create(option_objects, ignore_conflicts=True)
                        options.extend(list(Option.objects.filter(question__in=questions)))
                        option_objects = []
                    # Quiz Submissions
                    for quiz in quizzes:
                        if quiz.course_offering != offering:
                            continue
                        # Check if quiz submission exists
                        if QuizSubmission.objects.filter(student=student, quiz=quiz).exists():
                            print(f"Skipping existing QuizSubmission for {student.user.email} in {quiz.title}")
                            logger.debug(f"Skipping existing QuizSubmission for {student.user.email} in {quiz.title}")
                            quiz_submissions.append(QuizSubmission.objects.filter(student=student, quiz=quiz).first())
                            quiz_submission_count += 1
                            continue
                        question_ids = list(quiz.questions.values_list('id', flat=True))
                        answers = {str(qid): str(random.choice(Option.objects.filter(question_id=qid).values_list('id', flat=True))) for qid in question_ids}
                        score = sum(1 for qid, oid in answers.items() if Option.objects.get(id=oid).is_correct)
                        submission = QuizSubmission(
                            student=student,
                            quiz=quiz,
                            submitted_at=now,
                            score=score,
                            answers=answers
                        )
                        quiz_submission_objects.append(submission)
                        quiz_submission_count += 1
                        print(f"{quiz_submission_count} quiz submission created: {student.user.email} in {quiz.title}")
                        logger.debug(f"Quiz submission {quiz_submission_count}: {student.user.email} in {quiz.title}")
                        if quiz_submission_count % 1000 == 0:
                            QuizSubmission.objects.bulk_create(quiz_submission_objects, ignore_conflicts=True)
                            quiz_submissions.extend(list(QuizSubmission.objects.filter(student__in=[s.id for s in semester_enrollments])))
                            quiz_submission_objects = []
                            print(output.getvalue(), end='', flush=True)
                            output.truncate(0)
                            output.seek(0)
                    # Exam Result
                    if ExamResult.objects.filter(course_offering=offering, student=student).exists():
                        print(f"Skipping existing ExamResult for {student.user.email} in {offering.course.code}")
                        logger.debug(f"Skipping existing ExamResult for {student.user.email} in {offering.course.code}")
                        exam_results.append(ExamResult.objects.get(course_offering=offering, student=student))
                        exam_result_count += 1
                        continue
                    exam_result = ExamResult(
                        course_offering=offering,
                        student=student,
                        midterm_obtained=random.randint(0, 100),
                        midterm_total=100,
                        final_obtained=random.randint(0, 100),
                        final_total=100,
                        sessional_obtained=random.randint(0, 50),
                        sessional_total=50,
                        project_obtained=random.randint(0, 100),
                        project_total=100,
                        practical_obtained=random.randint(0, 50),
                        practical_total=50,
                        graded_by=offering.teacher,
                        remarks=fake.text(max_nb_chars=200)
                    )
                    exam_result_objects.append(exam_result)
                    exam_result_count += 1
                    print(f"{exam_result_count} exam result created: {student.user.email} in {offering.course.code}")
                    logger.debug(f"Exam result {exam_result_count}: {student.user.email} in {offering.course.code}")
            # Bulk create remaining objects
            if attendance_objects:
                Attendance.objects.bulk_create(attendance_objects, ignore_conflicts=True)
                attendances.extend(list(Attendance.objects.filter(student__in=[s.id for s in semester_enrollments])))
            if assignment_objects:
                Assignment.objects.bulk_create(assignment_objects, ignore_conflicts=True)
                assignments.extend(list(Assignment.objects.filter(course_offering__in=[o.id for o in course_offerings])))
            if submission_objects:
                AssignmentSubmission.objects.bulk_create(submission_objects, ignore_conflicts=True)
                assignment_submissions.extend(list(AssignmentSubmission.objects.filter(student__in=[s.id for s in semester_enrollments])))
            if quiz_submission_objects:
                QuizSubmission.objects.bulk_create(quiz_submission_objects, ignore_conflicts=True)
                quiz_submissions.extend(list(QuizSubmission.objects.filter(student__in=[s.id for s in semester_enrollments])))
            if exam_result_objects:
                ExamResult.objects.bulk_create(exam_result_objects, ignore_conflicts=True)
                exam_results.extend(list(ExamResult.objects.filter(student__in=[s.id for s in semester_enrollments])))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return attendances, assignments, assignment_submissions, quizzes, questions, options, quiz_submissions, exam_results

def create_notices(sessions, programs, teachers):
    """Create Notice records, skipping existing ones."""
    notices = []
    notice_objects = []
    notice_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for _ in range(NOTICES_PER_SESSION):
                    title = fake.catch_phrase()
                    # Check if notice exists
                    if Notice.objects.filter(title=title, created_by__in=teachers).exists():
                        print(f"Skipping existing Notice '{title}'")
                        logger.debug(f"Skipping existing Notice '{title}'")
                        notices.append(Notice.objects.filter(title=title, created_by__in=teachers).first())
                        notice_count += 1
                        continue
                    notice = Notice(
                        title=title,
                        content=fake.text(max_nb_chars=1000),
                        notice_type=random.choice([choice[0] for choice in Notice.NOTICE_TYPES]),
                        priority=random.choice([choice[0] for choice in Notice.PRIORITY_LEVELS]),
                        is_pinned=random.choice([True, False]),
                        is_active=True,
                        valid_from=now,
                        valid_until=fake.date_time_this_year(),
                        attachment=create_fake_file(),
                        created_by=random.choice(teachers),
                        created_at=now,
                        updated_at=now
                    )
                    notice_objects.append(notice)
                    notice_count += 1
                    print(f"{notice_count} notice created: {title}")
                    logger.debug(f"Notice {notice_count}: {title}")
                if notice_count % 100 == 0:
                    Notice.objects.bulk_create(notice_objects, ignore_conflicts=True)
                    notices.extend(list(Notice.objects.filter(created_by__in=[t.id for t in teachers])))
                    for notice in notices[-len(notice_objects):]:
                        notice.programs.set(applicable_programs)
                        notice.sessions.set([session])
                    notice_objects = []
                    print(output.getvalue(), end='', flush=True)
                    output.truncate(0)
                    output.seek(0)
            if notice_objects:
                Notice.objects.bulk_create(notice_objects, ignore_conflicts=True)
                notices.extend(list(Notice.objects.filter(created_by__in=[t.id for t in teachers])))
                for notice in notices[-len(notice_objects):]:
                    notice.programs.set(applicable_programs)
                    notice.sessions.set([session])
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return notices

def create_offices_staff(users, start_index):
    """Create Office and OfficeStaff records, skipping existing ones."""
    offices = []
    office_staffs = []
    office_objects = []
    staff_objects = []
    office_count = 0
    staff_count = 0
    OFFICE_NAMES = ['Registrar Office', 'Admissions Office', 'Finance Office']
    user_index = start_index
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for name in OFFICE_NAMES:
                slug = fake.slug(name)
                # Check if office exists
                if Office.objects.filter(slug=slug).exists():
                    print(f"Skipping existing Office '{name}'")
                    logger.debug(f"Skipping existing Office '{name}'")
                    offices.append(Office.objects.get(slug=slug))
                    office_count += 1
                    continue
                office = Office(
                    name=name,
                    description=fake.text(max_nb_chars=500),
                    image=create_fake_image(),
                    location=fake.address(),
                    contact_email=fake.email(),
                    contact_phone=fake.phone_number()[:20],
                    slug=slug
                )
                office_objects.append(office)
                office_count += 1
                print(f"{office_count} office created: {name}")
                logger.debug(f"Office {office_count}: {name}")
            Office.objects.bulk_create(office_objects, ignore_conflicts=True)
            offices.extend(list(Office.objects.filter(name__in=OFFICE_NAMES)))
            for office in offices:
                for _ in range(NUM_OFFICE_STAFF_PER_OFFICE):
                    if user_index >= len(users):
                        print("Not enough users for office staff")
                        logger.warning("Not enough users for office staff")
                        break
                    user = users[user_index]
                    user_index += 1
                    # Check if office staff exists
                    if OfficeStaff.objects.filter(user=user, office=office).exists():
                        print(f"Skipping existing OfficeStaff for '{user.email}'")
                        logger.debug(f"Skipping existing OfficeStaff for '{user.email}'")
                        office_staffs.append(OfficeStaff.objects.get(user=user, office=office))
                        staff_count += 1
                        continue
                    staff = OfficeStaff(
                        user=user,
                        office=office,
                        position=fake.job(),
                        contact_no=fake.phone_number()[:15]
                    )
                    staff_objects.append(staff)
                    staff_count += 1
                    print(f"{staff_count} office staff created: {user.email}")
                    logger.debug(f"Office staff {staff_count}: {user.email}")
            OfficeStaff.objects.bulk_create(staff_objects, ignore_conflicts=True)
            office_staffs.extend(list(OfficeStaff.objects.filter(user__in=[u.id for u in users[start_index:user_index]])))
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return offices, office_staffs

def generate_fake_data():
    """Generate fake data sequentially in a single transaction, skipping existing records."""
    start_time = time.time()
    output = StringIO()
    
    with redirect_stdout(output):
        # Get existing course codes and emails
        existing_course_codes = set(Course.objects.values_list('code', flat=True))
        existing_emails = set(CustomUser.objects.values_list('email', flat=True))
        logger.debug(f"Found {len(existing_emails)} existing emails, {len(existing_course_codes)} existing course codes")

        # Calculate total users needed
        total_users_needed = (STUDENTS_PER_SESSION * (len(BS_SESSIONS) + len(MS_SESSIONS)) * len(FACULTIES) * 2 * 2) + \
                             (TEACHERS_PER_DEPARTMENT * len(FACULTIES) * 2) + \
                             (NUM_OFFICES * NUM_OFFICE_STAFF_PER_OFFICE)
        logger.debug(f"Total users needed: {total_users_needed}")

        with transaction.atomic():
            # Create users
            users = create_users(total_users_needed, existing_emails)

            # Create faculties, departments, programs
            faculties, departments, programs = create_faculties_departments_programs()

            # Create sessions and semesters
            sessions, semesters = create_sessions_semesters(programs)

            # Create teachers
            teachers, user_index = create_teachers(departments, users, 0)

            # Create courses
            courses = create_courses(departments, existing_course_codes)

            # Create course offerings
            course_offerings = create_course_offerings(semesters, courses, teachers)

            # Create venues
            venues = create_venues(departments)

            # Create timetable slots
            timetable_slots = create_timetable_slots(course_offerings, venues)

            # Create admission cycles
            admission_cycles = create_admission_cycles(sessions, programs)

            # Create applicants and students
            applicants, students, user_index = create_applicants_students(sessions, programs, users, user_index)

            # Create academic qualifications
            qualifications = create_academic_qualifications(applicants)

            # Create extracurricular activities
            activities = create_extracurricular_activities(applicants)

            # Create semester enrollments
            semester_enrollments = create_semester_enrollments(students, semesters)

            # Create course enrollments
            course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)

            # Create academic records
            attendances, assignments, assignment_submissions, quizzes, questions, options, quiz_submissions, exam_results = \
                create_academic_records(semester_enrollments, course_offerings, teachers)

            # Create notices
            notices = create_notices(sessions, programs, teachers)

            # Create offices and staff
            offices, office_staffs = create_offices_staff(users, user_index)

        print(f"Total execution time: {time.time() - start_time:.2f} seconds")
        logger.debug(f"Total execution time: {time.time() - start_time:.2f} seconds")
    
    print(output.getvalue(), end='', flush=True)
    output.close()

if __name__ == '__main__':
    try:
        generate_fake_data()
        print("Fake data generation completed!")
        logger.info("Fake data generation completed")
    except Exception as e:
        print(f"Error during data generation: {str(e)}")
        logger.error(f"Error during data generation: {str(e)}")
        sys.exit(1)