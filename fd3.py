import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.db import transaction, IntegrityError, DatabaseError
import sys
import time
import logging
from io import StringIO
from contextlib import redirect_stdout

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import models
from users.models import CustomUser
from academics.models import Faculty, Department, Program, Semester
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from faculty_staff.models import Teacher, TeacherDetails, Office, OfficeStaff
from courses.models import Course, CourseOffering, Venue, TimetableSlot, StudyMaterial, Assignment, AssignmentSubmission, Notice, ExamResult, Attendance
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment

# Predefined data lists and dictionaries
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
DOMAINS = ['warren-fuller.com', 'techlearn.org', 'edusys.net', 'campus360.com', 'studyhub.org']
COURSE_NAMES = {
    'CS': ['Introduction to Programming', 'Data Structures', 'Algorithms', 'Database Systems', 'Operating Systems'],
    'EE': ['Circuit Analysis', 'Electronics', 'Digital Systems', 'Power Systems', 'Control Systems']
}
DESCRIPTIONS = [
    'This is a foundational course covering key concepts.',
    'Advanced topics in system design and analysis.',
    'Practical applications and hands-on projects.',
    'Theoretical foundations and case studies.',
    'Exploration of modern techniques and tools.'
]
NOTICE_TITLES = ['Course Update', 'Exam Schedule', 'Seminar Announcement', 'Holiday Notice', 'Registration Deadline']
QUALIFICATIONS = ['Matriculation', 'FSc', 'Bachelor’s']
ACTIVITIES = ['Debate Club', 'Coding Competition', 'Sports Tournament', 'Science Fair', 'Community Service']
JOBS = ['Registrar', 'Accountant', 'Admissions Officer', 'IT Support', 'HR Manager']
ADDRESSES = ['123 Main St, Karachi', '456 Gulshan, Lahore', '789 Clifton, Islamabad', '101 Bahria, Rawalpindi']
PHONE_NUMBERS = ['03001234567', '03111234567', '03211234567', '03311234567', '03411234567']
CNICS = ['12345-6789012-3', '54321-1234567-8', '98765-4321098-7', '45678-9012345-6']
SENTENCES = [
    'This is a sample description.', 'Learn advanced techniques in this field.', 
    'Hands-on experience with modern tools.', 'Explore real-world applications.'
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
NOTICES_PER_SESSION = 5
NUM_OFFICES = 3
NUM_OFFICE_STAFF_PER_OFFICE = 3
NUM_VENUES_PER_DEPARTMENT = 3
NUM_COURSES_PER_DEPARTMENT = 5

def create_fake_image():
    """Return None to disable image generation for performance."""
    logger.debug("Skipping fake image generation")
    return None

def create_fake_file(extension='pdf'):
    """Return None to disable file generation for performance."""
    logger.debug(f"Skipping fake file generation with extension {extension}")
    return None

def generate_muslim_name():
    """Generate a Muslim full name."""
    logger.debug("Generating Muslim name")
    gender = random.choice(['male', 'female'])
    first_name = random.choice(MUSLIM_MALE_NAMES if gender == 'male' else MUSLIM_FEMALE_NAMES)
    last_name = random.choice(MUSLIM_LAST_NAMES)
    return first_name, last_name

def create_users(num_users, existing_emails):
    """Create CustomUser records, saving each individually, skipping existing emails."""
    users = []
    user_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    emails = set()
    
    with redirect_stdout(output):
        for i in range(num_users):
            first_name, last_name = generate_muslim_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(DOMAINS)}"
            attempts = 0
            while (email in existing_emails or email in emails) and attempts < 100:
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 1000)}@{random.choice(DOMAINS)}"
                attempts += 1
            if attempts >= 100:
                skip_count += 1
                print(f"Skipping User due to email generation failure (Skip #{skip_count})")
                logger.warning(f"Skipping User due to email generation failure")
                continue
            if CustomUser.objects.filter(email=email).exists():
                skip_count += 1
                print(f"Skipping existing user: {email} (Skip #{skip_count})")
                logger.debug(f"Skipping existing user: {email} (Skip #{skip_count})")
                users.append(CustomUser.objects.get(email=email))
                user_count += 1
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
                info=random.choice(SENTENCES),
                profile_picture=create_fake_image()
            )
            user.set_password('password123')
            try:
                user.save()
                users.append(user)
                user_count += 1
                print(f"{user_count} user created: {email}")
                logger.debug(f"User {user_count}: {email}")
            except IntegrityError as e:
                skip_count += 1
                print(f"Skipping User '{email}' due to conflict: {str(e)} (Skip #{skip_count})")
                logger.warning(f"Skipping User '{email}' due to conflict: {str(e)}")
                continue
            if user_count % 100 == 0:
                print(output.getvalue(), end='', flush=True)
                output.truncate(0)
                output.seek(0)
        print(f"Total users skipped: {skip_count}")
        logger.debug(f"Total users skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return users

def create_faculties_departments_programs():
    """Create Faculty, Department, and Program records, saving each individually."""
    faculties = []
    departments = []
    programs = []
    faculty_count = 0
    department_count = 0
    program_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for faculty_data in FACULTIES:
                slug = f"faculty-{faculty_data['name'].lower().replace(' ', '-')}"
                if Faculty.objects.filter(slug=slug).exists():
                    skip_count += 1
                    print(f"Skipping existing Faculty '{faculty_data['name']}' (Skip #{skip_count})")
                    logger.debug(f"Skipping existing Faculty '{faculty_data['name']}'")
                    faculties.append(Faculty.objects.get(slug=slug))
                    faculty_count += 1
                    continue
                try:
                    faculty = Faculty(
                        name=faculty_data['name'],
                        slug=slug,
                        description=random.choice(DESCRIPTIONS)
                    )
                    faculty.save()
                    faculties.append(faculty)
                    faculty_count += 1
                    print(f"{faculty_count} faculty created: {faculty_data['name']}")
                    logger.debug(f"Faculty {faculty_count}: {faculty_data['name']}")
                except IntegrityError as e:
                    skip_count += 1
                    print(f"Skipping Faculty '{faculty_data['name']}' due to conflict: {str(e)} (Skip #{skip_count})")
                    logger.warning(f"Skipping Faculty '{faculty_data['name']}' due to conflict: {str(e)}")
                    continue
                for dept_data in faculty_data['departments']:
                    dept_slug = f"dept-{dept_data['name'].lower().replace(' ', '-')}"
                    if Department.objects.filter(slug=dept_slug, code=dept_data['code']).exists():
                        skip_count += 1
                        print(f"Skipping existing Department '{dept_data['name']}' (Skip #{skip_count})")
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
                            introduction=random.choice(SENTENCES),
                            details=random.choice(DESCRIPTIONS)
                        )
                        department.save()
                        departments.append(department)
                        department_count += 1
                        print(f"{department_count} department created: {dept_data['name']}")
                        logger.debug(f"Department {department_count}: {dept_data['name']}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Department '{dept_data['name']}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping Department '{dept_data['name']}' due to conflict: {str(e)}")
                        continue
                    for program_name, degree_type in dept_data['programs']:
                        if Program.objects.filter(name=program_name, department=department).exists():
                            skip_count += 1
                            print(f"Skipping existing Program '{program_name}' (Skip #{skip_count})")
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
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping Program '{program_name}' due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping Program '{program_name}' due to conflict: {str(e)}")
                            continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return faculties, departments, programs

def create_sessions_semesters(programs):
    """Create AcademicSession and Semester records, saving each individually."""
    sessions = []
    semesters = []
    session_count = 0
    semester_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session_data in BS_SESSIONS + MS_SESSIONS:
                if AcademicSession.objects.filter(name=session_data['name']).exists():
                    skip_count += 1
                    print(f"Skipping existing Session '{session_data['name']}' (Skip #{skip_count})")
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
                        description=random.choice(DESCRIPTIONS),
                        created_at=now,
                        updated_at=now
                    )
                    session.save()
                    sessions.append(session)
                    session_count += 1
                    print(f"{session_count} session created: {session_data['name']}")
                    logger.debug(f"Session {session_count}: {session_data['name']}")
                except IntegrityError as e:
                    skip_count += 1
                    print(f"Skipping Session '{session_data['name']}' due to conflict: {str(e)} (Skip #{skip_count})")
                    logger.warning(f"Skipping Session '{session_data['name']}' due to conflict: {str(e)}")
                    continue
            for session in sessions:
                session_info = next(s for s in (BS_SESSIONS + MS_SESSIONS) if s['name'] == session.name)
                num_semesters = session_info['semesters']
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for program in applicable_programs:
                    for number in range(1, num_semesters + 1):
                        if Semester.objects.filter(program=program, session=session, number=number).exists():
                            skip_count += 1
                            print(f"Skipping existing Semester {number} for {program.name} in {session.name} (Skip #{skip_count})")
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
                                description=random.choice(DESCRIPTIONS),
                                start_time=start_date,
                                end_time=end_date,
                                is_active=(number == session_info['semesters'] and session.start_year == 2024)
                            )
                            semester.save()
                            semesters.append(semester)
                            semester_count += 1
                            print(f"{semester_count} semester created: Semester {number} for {program.name}")
                            logger.debug(f"Semester {semester_count}: Semester {number} for {program.name}")
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping Semester {number} for {program.name} in {session.name} due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping Semester {number} for {program.name} in {session.name}: {str(e)}")
                            continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return sessions, semesters

def create_teachers(departments, users, start_index):
    """Create Teacher and TeacherDetails records, saving each individually."""
    teachers = []
    teacher_details = []
    user_index = start_index
    teacher_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
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
                    if Teacher.objects.filter(user=user, department=department).exists():
                        skip_count += 1
                        print(f"Skipping existing Teacher for user '{user.email}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing Teacher for user '{user.email}'")
                        teachers.append(Teacher.objects.get(user=user, department=department))
                        teacher_count += 1
                        continue
                    try:
                        teacher = Teacher(
                            user=user,
                            department=department,
                            designation=designation,
                            contact_no=random.choice(PHONE_NUMBERS),
                            qualification=random.choice(SENTENCES),
                            hire_date=datetime(2020, random.randint(1, 12), 1),
                            is_active=True,
                            linkedin_url=f"https://linkedin.com/in/{user.first_name.lower()}{user.last_name.lower()}",
                            twitter_url=f"https://twitter.com/{user.first_name.lower()}{user.last_name.lower()}",
                            personal_website=f"https://www.{user.first_name.lower()}.com",
                            experience=random.choice(DESCRIPTIONS)
                        )
                        teacher.save()
                        teachers.append(teacher)
                        teacher_count += 1
                        print(f"{teacher_count} teacher created: {user.email}")
                        logger.debug(f"Teacher {teacher_count}: {user.email}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Teacher for user '{user.email}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping Teacher for user '{user.email}' due to conflict: {str(e)}")
                        user_index -= 1
                        continue
                    if TeacherDetails.objects.filter(teacher=teacher).exists():
                        skip_count += 1
                        print(f"Skipping existing TeacherDetails for teacher '{teacher.user.email}' (Skip #{skip_count})")
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
                        teacher_detail.save()
                        teacher_details.append(teacher_detail)
                        print(f"TeacherDetails created for teacher '{teacher.user.email}'")
                        logger.debug(f"TeacherDetails created for teacher '{teacher.user.email}'")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping TeacherDetails for teacher '{teacher.user.email}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping TeacherDetails for teacher '{teacher.user.email}' due to conflict: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return teachers, user_index

def create_courses(departments, existing_course_codes):
    """Create Course records with predefined names, saving each individually."""
    courses = []
    course_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for department in departments:
                course_names = COURSE_NAMES[department.code]
                for i, name in enumerate(course_names, 1):
                    code = f"{department.code}{100 + i}"
                    attempts = 0
                    while code in existing_course_codes and attempts < 100:
                        code = f"{department.code}{100 + i + random.randint(1, 1000)}"
                        attempts += 1
                    if attempts >= 100:
                        skip_count += 1
                        print(f"Skipping Course due to code generation failure (Skip #{skip_count})")
                        logger.warning(f"Skipping Course due to code generation failure")
                        continue
                    if Course.objects.filter(code=code).exists():
                        skip_count += 1
                        print(f"Skipping existing Course '{code}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing Course '{code}'")
                        courses.append(Course.objects.get(code=code))
                        course_count += 1
                        continue
                    existing_course_codes.add(code)
                    try:
                        course = Course(
                            opt=random.choice([True, False]),
                            code=code,
                            name=name,
                            credits=random.randint(1, 4),
                            lab_work=random.randint(0, 2),
                            is_active=True,
                            description=random.choice(DESCRIPTIONS)
                        )
                        course.save()
                        courses.append(course)
                        course_count += 1
                        print(f"{course_count} course created: {code} - {name}")
                        logger.debug(f"Course {course_count}: {code} - {name}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Course '{code}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping Course '{code}' due to conflict: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return courses

def create_course_offerings(semesters, courses, teachers):
    """Create exactly 3 CourseOffering records per semester, saving each individually."""
    course_offerings = []
    offering_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for semester in semesters:
                if len(courses) < 3:
                    print(f"Warning: Not enough courses ({len(courses)}) to assign 3 offerings for {semester.program.department.name}")
                    logger.warning(f"Not enough courses ({len(courses)}) for {semester.program.department.name}")
                    continue
                selected_courses = random.sample(courses, min(3, len(courses)))
                department_teachers = [t for t in teachers if t.department == semester.program.department]
                if not department_teachers:
                    print(f"No teachers available for {semester.program.department.name}")
                    logger.warning(f"No teachers available for {semester.program.department.name}")
                    continue
                for course in selected_courses:
                    if CourseOffering.objects.filter(course=course, semester=semester).exists():
                        skip_count += 1
                        print(f"Skipping existing CourseOffering for {course.code} in {semester.name} (Skip #{skip_count})")
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
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping CourseOffering for {course.code} in {semester.name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping CourseOffering for {course.code} in {semester.name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return course_offerings

def create_venues(departments):
    """Create Venue records, saving each individually."""
    venues = []
    venue_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for department in departments:
                for i in range(NUM_VENUES_PER_DEPARTMENT):
                    name = f"Room {department.code}-{i + 1}"
                    if Venue.objects.filter(name=name, department=department).exists():
                        skip_count += 1
                        print(f"Skipping existing Venue '{name}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing Venue '{name}'")
                        venues.append(Venue.objects.get(name=name, department=department))
                        venue_count += 1
                        continue
                    try:
                        venue = Venue(
                            name=name,
                            department=department,
                            capacity=random.randint(20, 100),
                            is_active=True
                        )
                        venue.save()
                        venues.append(venue)
                        venue_count += 1
                        print(f"{venue_count} venue created: {name}")
                        logger.debug(f"Venue {venue_count}: {name}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Venue '{name}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping Venue '{name}' due to conflict: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return venues

def create_timetable_slots(course_offerings, venues):
    """Create TimetableSlot records, saving each individually."""
    timetable_slots = []
    slot_count = 0
    skip_count = 0
    output = StringIO()
    days = [choice[0] for choice in TimetableSlot.DAYS_OF_WEEK]
    
    with redirect_stdout(output):
        with transaction.atomic():
            for offering in course_offerings:
                for _ in range(random.randint(1, 3)):
                    start_time = datetime.strptime(f"{random.randint(8, 16)}:00", "%H:%M").time()
                    start_datetime = datetime.combine(datetime.today(), start_time)
                    end_time = (start_datetime + timedelta(hours=1)).time()
                    day = random.choice(days)
                    venue = random.choice([v for v in venues if v.department == offering.department])
                    if TimetableSlot.objects.filter(course_offering=offering, day=day, start_time=start_time, venue=venue).exists():
                        skip_count += 1
                        print(f"Skipping existing TimetableSlot for {offering.course.code} on {day} (Skip #{skip_count})")
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
                        skip_count += 1
                        print(f"Skipping TimetableSlot for {offering.course.code} due to {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping TimetableSlot for {offering.course.code} due to {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return timetable_slots

def create_admission_cycles(sessions, programs):
    """Create AdmissionCycle records, saving each individually."""
    admission_cycles = []
    cycle_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for program in applicable_programs:
                    if AdmissionCycle.objects.filter(program=program, session=session).exists():
                        skip_count += 1
                        print(f"Skipping existing AdmissionCycle for {program.name} in {session.name} (Skip #{skip_count})")
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
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping AdmissionCycle for {program.name} in {session.name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping AdmissionCycle for {program.name} in {session.name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return admission_cycles

def create_applicants_students(sessions, programs, users, start_index):
    """Create Applicant and Student records, saving each individually."""
    applicants = []
    students = []
    applicant_count = 0
    student_count = 0
    skip_count = 0
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
                            if Applicant.objects.filter(user=user, session=session, program=program).exists():
                                skip_count += 1
                                print(f"Skipping existing Applicant for '{user.email}' (Skip #{skip_count})")
                                logger.debug(f"Skipping existing Applicant for '{user.email}'")
                                applicants.append(Applicant.objects.get(user=user, session=session, program=program))
                                applicant_count += 1
                                if Student.objects.filter(user=user, program=program).exists():
                                    skip_count += 1
                                    print(f"Skipping existing Student for '{user.email}' (Skip #{skip_count})")
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
                                    caste=random.choice(['Qureshi', 'Jutt', 'Rajput']),
                                    cnic=random.choice(CNICS),
                                    dob=datetime(2000, random.randint(1, 12), random.randint(1, 28)),
                                    contact_no=random.choice(PHONE_NUMBERS),
                                    identification_mark=random.choice(SENTENCES),
                                    father_name=f"{random.choice(MUSLIM_MALE_NAMES)} {random.choice(MUSLIM_LAST_NAMES)}",
                                    father_occupation=random.choice(JOBS),
                                    father_cnic=random.choice(CNICS),
                                    monthly_income=random.randint(50000, 200000),
                                    relationship='father',
                                    permanent_address=random.choice(ADDRESSES),
                                    shift=shift,
                                    declaration=True,
                                    created_at=now
                                )
                                applicant.save()
                                applicants.append(applicant)
                                applicant_count += 1
                                print(f"{applicant_count} applicant created: {user.email}")
                                logger.debug(f"Applicant {applicant_count}: {user.email}")
                                roll_no = random.randint(10000000, 99999999)
                                attempts = 0
                                while roll_no in existing_roll_nos and attempts < 100:
                                    roll_no = random.randint(10000000, 99999999)
                                    attempts += 1
                                if attempts >= 100:
                                    skip_count += 1
                                    print(f"Skipping Student due to roll number generation failure (Skip #{skip_count})")
                                    logger.warning(f"Skipping Student due to roll number generation failure")
                                    continue
                                existing_roll_nos.add(roll_no)
                                student = Student(
                                    applicant=applicant,
                                    user=user,
                                    university_roll_no=roll_no,
                                    college_roll_no=random.randint(10000000, 99999999),
                                    enrollment_date=datetime(session.start_year, 1, 1),
                                    program=program,
                                    current_status='active',
                                    emergency_contact=f"{random.choice(MUSLIM_MALE_NAMES)} {random.choice(MUSLIM_LAST_NAMES)}",
                                    emergency_phone=random.choice(PHONE_NUMBERS),
                                    role=random.choice(['CR', 'GR', None])
                                )
                                student.save()
                                students.append(student)
                                student_count += 1
                                print(f"{student_count} student created: {user.email}")
                                logger.debug(f"Student {student_count}: {user.email}")
                            except IntegrityError as e:
                                skip_count += 1
                                print(f"Skipping Applicant/Student for '{user.email}' due to conflict: {str(e)} (Skip #{skip_count})")
                                logger.warning(f"Skipping Applicant/Student for '{user.email}' due to conflict: {str(e)}")
                                user_index -= 1
                                continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return applicants, students, user_index

def create_academic_qualifications(applicants):
    """Create AcademicQualification records, saving each individually."""
    qualifications = []
    qualification_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for applicant in applicants:
                for _ in range(random.randint(1, 3)):
                    exam_passed = random.choice(QUALIFICATIONS)
                    passing_year = random.randint(2015, 2023)
                    if AcademicQualification.objects.filter(applicant=applicant, exam_passed=exam_passed, passing_year=passing_year).exists():
                        skip_count += 1
                        print(f"Skipping existing AcademicQualification for {applicant.full_name} (Skip #{skip_count})")
                        logger.debug(f"Skipping existing AcademicQualification for {applicant.full_name}")
                        qualifications.append(AcademicQualification.objects.filter(applicant=applicant, exam_passed=exam_passed, passing_year=passing_year).first())
                        qualification_count += 1
                        continue
                    try:
                        qualification = AcademicQualification(
                            applicant=applicant,
                            exam_passed=exam_passed,
                            passing_year=passing_year,
                            marks_obtained=random.randint(400, 900),
                            total_marks=1000,
                            division=random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                            subjects=', '.join(random.sample(['Math', 'Physics', 'Chemistry', 'Biology', 'CS'], 3)),
                            board=f"{random.choice(['Karachi', 'Lahore', 'Islamabad'])} Board",
                            certificate_file=create_fake_file()
                        )
                        qualification.save()
                        qualifications.append(qualification)
                        qualification_count += 1
                        print(f"{qualification_count} academic qualification created: {applicant.full_name}")
                        logger.debug(f"Academic qualification {qualification_count}: {applicant.full_name}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping AcademicQualification for {applicant.full_name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping AcademicQualification for {applicant.full_name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return qualifications

def create_extracurricular_activities(applicants):
    """Create ExtraCurricularActivity records, saving each individually."""
    activities = []
    activity_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for applicant in applicants:
                for _ in range(random.randint(0, 2)):
                    activity_name = random.choice(ACTIVITIES)
                    activity_year = random.randint(2015, 2023)
                    if ExtraCurricularActivity.objects.filter(applicant=applicant, activity=activity_name, activity_year=activity_year).exists():
                        skip_count += 1
                        print(f"Skipping existing ExtraCurricularActivity for {applicant.full_name} (Skip #{skip_count})")
                        logger.debug(f"Skipping existing ExtraCurricularActivity for {applicant.full_name}")
                        activities.append(ExtraCurricularActivity.objects.filter(applicant=applicant, activity=activity_name, activity_year=activity_year).first())
                        activity_count += 1
                        continue
                    try:
                        activity = ExtraCurricularActivity(
                            applicant=applicant,
                            activity=activity_name,
                            position=random.choice(['Captain', 'Secretary', 'Member']),
                            achievement=random.choice(SENTENCES),
                            activity_year=activity_year,
                            certificate_file=create_fake_file()
                        )
                        activity.save()
                        activities.append(activity)
                        activity_count += 1
                        print(f"{activity_count} extracurricular activity created: {applicant.full_name}")
                        logger.debug(f"Extracurricular activity {activity_count}: {applicant.full_name}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping ExtraCurricularActivity for {applicant.full_name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping ExtraCurricularActivity for {applicant.full_name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return activities

def create_semester_enrollments(students, semesters):
    """Create StudentSemesterEnrollment records, saving each individually."""
    semester_enrollments = []
    enrollment_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for student in students:
                applicable_semesters = [s for s in semesters if s.program == student.program and s.session == student.applicant.session]
                if not applicable_semesters:
                    print(f"No applicable semesters for {student.user.email}")
                    logger.warning(f"No applicable semesters for {student.user.email}")
                    continue
                for semester in applicable_semesters:
                    if StudentSemesterEnrollment.objects.filter(student=student, semester=semester).exists():
                        skip_count += 1
                        print(f"Skipping existing SemesterEnrollment for {student.user.email} in {semester.name} (Skip #{skip_count})")
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
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping SemesterEnrollment for {student.user.email} in {semester.name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping SemesterEnrollment for {student.user.email} in {semester.name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return semester_enrollments

def create_course_enrollments(semester_enrollments, course_offerings):
    """Create CourseEnrollment records, saving each individually."""
    course_enrollments = []
    enrollment_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for enrollment in semester_enrollments:
                applicable_offerings = [co for co in course_offerings if co.semester == enrollment.semester]
                if not applicable_offerings:
                    print(f"No applicable offerings for {enrollment.student.user.email} in {enrollment.semester.name}")
                    logger.warning(f"No applicable offerings for {enrollment.student.user.email}")
                    continue
                for offering in applicable_offerings:
                    if CourseEnrollment.objects.filter(student_semester_enrollment=enrollment, course_offering=offering).exists():
                        skip_count += 1
                        print(f"Skipping existing CourseEnrollment for {enrollment.student.user.email} in {offering.course.code} (Skip #{skip_count})")
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
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping CourseEnrollment for {enrollment.student.user.email} in {offering.course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping CourseEnrollment for {enrollment.student.user.email} in {offering.course.code}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()   
    return course_enrollments

def create_academic_records(semester_enrollments, course_offerings, teachers):
    """Create Attendance, Assignment, AssignmentSubmission, and ExamResult records, saving each individually."""
    attendances = []
    assignments = []
    assignment_submissions = []
    exam_results = []
    attendance_count = 0
    assignment_count = 0
    submission_count = 0
    exam_result_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for enrollment in semester_enrollments:
                applicable_offerings = [co for co in course_offerings if co.semester == enrollment.semester]
                if not applicable_offerings:
                    print(f"No applicable offerings for {enrollment.student.user.email} in {enrollment.semester.name}")
                    logger.warning(f"No applicable offerings for {enrollment.student.user.email}")
                    continue
                student = enrollment.student
                semester = enrollment.semester
                for offering in applicable_offerings:
                    # Attendance
                    for _ in range(ATTENDANCE_PER_STUDENT_PER_SEMESTER):
                        date = semester.start_time + timedelta(days=random.randint(0, 180))
                        shift = offering.shift if offering.shift != 'both' else student.applicant.shift
                        if Attendance.objects.filter(student=student, course_offering=offering, date=date).exists():
                            skip_count += 1
                            print(f"Skipping existing Attendance for {student.user.email} in {offering.course.code} (Skip #{skip_count})")
                            logger.debug(f"Skipping existing Attendance for {student.user.email} in {offering.course.code}")
                            attendances.append(Attendance.objects.filter(student=student, course_offering=offering, date=date).first())
                            attendance_count += 1
                            continue
                        try:
                            attendance = Attendance(
                                student=student,
                                course_offering=offering,
                                date=date,
                                status=random.choice([choice[0] for choice in Attendance.STATUS_CHOICES]),
                                shift=shift,
                                recorded_by=offering.teacher,
                                recorded_at=now
                            )
                            attendance.save()
                            attendances.append(attendance)
                            attendance_count += 1
                            print(f"{attendance_count} attendance created: {student.user.email} in {offering.course.code}")
                            logger.debug(f"Attendance {attendance_count}: {student.user.email} in {offering.course.code}")
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping Attendance for {student.user.email} in {offering.course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping Attendance for {student.user.email} in {offering.course.code}: {str(e)}")
                            continue
                    # Assignments
                    for i in range(ASSIGNMENTS_PER_STUDENT_PER_SEMESTER):
                        title = f"Assignment {offering.course.code}-{i+1}"
                        due_date = semester.start_time + timedelta(days=random.randint(30, 180))
                        if Assignment.objects.filter(course_offering=offering, title=title).exists():
                            skip_count += 1
                            print(f"Skipping existing Assignment '{title}' in {offering.course.code} (Skip #{skip_count})")
                            logger.debug(f"Skipping existing Assignment '{title}' in {offering.course.code}")
                            assignments.append(Assignment.objects.filter(course_offering=offering, title=title).first())
                            assignment_count += 1
                            continue
                        try:
                            assignment = Assignment(
                                course_offering=offering,
                                teacher=offering.teacher,
                                title=title,
                                description=random.choice(DESCRIPTIONS),
                                due_date=due_date,
                                max_points=100,
                                resource_file=create_fake_file(),
                                created_at=now,
                                updated_at=now
                            )
                            assignment.save()
                            assignments.append(assignment)
                            assignment_count += 1
                            print(f"{assignment_count} assignment created: {title} in {offering.course.code}")
                            logger.debug(f"Assignment {assignment_count}: {title} in {offering.course.code}")
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping Assignment '{title}' in {offering.course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping Assignment '{title}' in {offering.course.code}: {str(e)}")
                            continue
                        # Assignment Submissions
                        if AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
                            skip_count += 1
                            print(f"Skipping existing AssignmentSubmission for {student.user.email} in {offering.course.code} (Skip #{skip_count})")
                            logger.debug(f"Skipping existing AssignmentSubmission for {student.user.email} in {offering.course.code}")
                            assignment_submissions.append(AssignmentSubmission.objects.filter(assignment=assignment, student=student).first())
                            submission_count += 1
                            continue
                        try:
                            submission = AssignmentSubmission(
                                assignment=assignment,
                                student=student,
                                content=random.choice(SENTENCES),
                                file=create_fake_file(),
                                submitted_at=assignment.due_date,
                                marks_obtained=random.randint(0, 100),
                                feedback=random.choice(SENTENCES),
                                graded_by=offering.teacher,
                                graded_at=now
                            )
                            submission.save()
                            assignment_submissions.append(submission)
                            submission_count += 1
                            print(f"{submission_count} assignment submission created: {student.user.email} in {offering.course.code}")
                            logger.debug(f"Assignment submission {submission_count}: {student.user.email} in {offering.course.code}")
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping AssignmentSubmission for {student.user.email} in {offering.course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping AssignmentSubmission for {student.user.email} in {offering.course.code}: {str(e)}")
                            continue
                    # Exam Result
                    if ExamResult.objects.filter(course_offering=offering, student=student).exists():
                        skip_count += 1
                        print(f"Skipping existing ExamResult for {student.user.email} in {offering.course.code} (Skip #{skip_count})")
                        logger.debug(f"Skipping existing ExamResult for {student.user.email} in {offering.course.code}")
                        exam_results.append(ExamResult.objects.get(course_offering=offering, student=student))
                        exam_result_count += 1
                        continue
                    try:
                        exam_result = ExamResult(
                            course_offering=offering,
                            student=student,
                            midterm_obtained=random.randint(0, 100),
                            midterm_total=100,
                            final_obtained=random.randint(0, 100),
                            final_total=100,
                            sessional_obtained=random.randint(0, 50),
                            sessional_total=50,
                            project_obtained=random.randint(0, 50),
                            project_total=50,
                            practical_obtained=random.randint(0, 50),
                            practical_total=50,
                            graded_by=offering.teacher,
                            remarks=random.choice(SENTENCES)
                        )
                        exam_result.save()
                        exam_results.append(exam_result)
                        exam_result_count += 1
                        print(f"{exam_result_count} exam result created: {student.user.email} in {offering.course.code}")
                        logger.debug(f"Exam result {exam_result_count}: {student.user.email} in {offering.course.code}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping ExamResult for {student.user.email} in {offering.course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping ExamResult for {student.user.email} in {offering.course.code}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return attendances, assignments, assignment_submissions, exam_results

def create_notices(sessions, programs, teachers):
    """Create Notice records, saving each individually."""
    notices = []
    notice_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS' and session.start_year <= 2024) or 
                                      (p.degree_type == 'MS' and session.start_year >= 2023)]
                for _ in range(NOTICES_PER_SESSION):
                    title = random.choice(NOTICE_TITLES)
                    if Notice.objects.filter(title=title, created_by__in=teachers).exists():
                        skip_count += 1
                        print(f"Skipping existing Notice '{title}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing Notice '{title}'")
                        notices.append(Notice.objects.filter(title=title, created_by__in=teachers).first())
                        notice_count += 1
                        continue
                    try:
                        notice = Notice(
                            title=title,
                            content=random.choice(DESCRIPTIONS),
                            notice_type=random.choice([choice[0] for choice in Notice.NOTICE_TYPES]),
                            priority=random.choice([choice[0] for choice in Notice.PRIORITY_LEVELS]),
                            is_pinned=random.choice([True, False]),
                            is_active=True,
                            valid_from=now,
                            valid_until=now + timedelta(days=30),
                            attachment=create_fake_file(),
                            created_by=random.choice(teachers),
                            created_at=now,
                            updated_at=now
                        )
                        notice.save()
                        notice.programs.set(applicable_programs)
                        notice.sessions.set([session])
                        notices.append(notice)
                        notice_count += 1
                        print(f"{notice_count} notice created: {title}")
                        logger.debug(f"Notice {notice_count}: {title}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Notice '{title}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping Notice '{title}': {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return notices

def create_offices_staff(users, start_index):
    """Create Office and OfficeStaff records, saving each individually."""
    offices = []
    office_staffs = []
    office_count = 0
    staff_count = 0
    skip_count = 0
    OFFICE_NAMES = ['Registrar Office', 'Admissions Office', 'Finance Office']
    user_index = start_index
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for name in OFFICE_NAMES:
                slug = f"office-{name.lower().replace(' ', '-')}"
                if Office.objects.filter(slug=slug).exists():
                    skip_count += 1
                    print(f"Skipping existing Office '{name}' (Skip #{skip_count})")
                    logger.debug(f"Skipping existing Office '{name}'")
                    offices.append(Office.objects.get(slug=slug))
                    office_count += 1
                    continue
                try:
                    office = Office(
                        name=name,
                        description=random.choice(DESCRIPTIONS),
                        image=create_fake_image(),
                        location=random.choice(ADDRESSES),
                        contact_email=f"contact@{name.lower().replace(' ', '')}.com",
                        contact_phone=random.choice(PHONE_NUMBERS),
                        slug=slug
                    )
                    office.save()
                    offices.append(office)
                    office_count += 1
                    print(f"{office_count} office created: {name}")
                    logger.debug(f"Office {office_count}: {name}")
                except IntegrityError as e:
                    skip_count += 1
                    print(f"Skipping Office '{name}' due to conflict: {str(e)} (Skip #{skip_count})")
                    logger.warning(f"Skipping Office '{name}': {str(e)}")
                    continue
            for office in offices:
                for _ in range(NUM_OFFICE_STAFF_PER_OFFICE):
                    if user_index >= len(users):
                        print("Not enough users for office staff")
                        logger.warning("Not enough users for office staff")
                        break
                    user = users[user_index]
                    user_index += 1
                    if OfficeStaff.objects.filter(user=user, office=office).exists():
                        skip_count += 1
                        print(f"Skipping existing OfficeStaff for '{user.email}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing OfficeStaff for '{user.email}'")
                        office_staffs.append(OfficeStaff.objects.get(user=user, office=office))
                        staff_count += 1
                        continue
                    try:
                        staff = OfficeStaff(
                            user=user,
                            office=office,
                            position=random.choice(JOBS),
                            contact_no=random.choice(PHONE_NUMBERS)
                        )
                        staff.save()
                        office_staffs.append(staff)
                        staff_count += 1
                        print(f"{staff_count} office staff created: {user.email}")
                        logger.debug(f"Office staff {staff_count}: {user.email}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping OfficeStaff for '{user.email}' due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping OfficeStaff for '{user.email}': {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return offices, office_staffs

def generate_fake_data():
    """Generate fake data, saving each record individually."""
    start_time = time.time()
    output = StringIO()
    
    try:
        with redirect_stdout(output):
            existing_course_codes = set(Course.objects.values_list('code', flat=True))
            existing_emails = set(CustomUser.objects.values_list('email', flat=True))
            logger.debug(f"Found {len(existing_emails)} existing emails, {len(existing_course_codes)} existing course codes")

            total_users_needed = (STUDENTS_PER_SESSION * (len(BS_SESSIONS) + len(MS_SESSIONS)) * len(FACULTIES) * 2 * 2) + \
                                 (TEACHERS_PER_DEPARTMENT * len(FACULTIES) * 2) + \
                                 (NUM_OFFICES * NUM_OFFICE_STAFF_PER_OFFICE)
            logger.debug(f"Total users needed: {total_users_needed}")

            with transaction.atomic():
                users = create_users(total_users_needed, existing_emails)
                faculties, departments, programs = create_faculties_departments_programs()
                sessions, semesters = create_sessions_semesters(programs)
                teachers, user_index = create_teachers(departments, users, 0)
                courses = create_courses(departments, existing_course_codes)
                course_offerings = create_course_offerings(semesters, courses, teachers)
                venues = create_venues(departments)
                timetable_slots = create_timetable_slots(course_offerings, venues)
                admission_cycles = create_admission_cycles(sessions, programs)
                applicants, students, user_index = create_applicants_students(sessions, programs, users, user_index)
                qualifications = create_academic_qualifications(applicants)
                activities = create_extracurricular_activities(applicants)
                semester_enrollments = create_semester_enrollments(students, semesters)
                course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)
                attendances, assignments, assignment_submissions, exam_results = \
                    create_academic_records(semester_enrollments, course_offerings, teachers)
                notices = create_notices(sessions, programs, teachers)
                offices, office_staffs = create_offices_staff(users, user_index)

            print(f"Total execution time: {time.time() - start_time:.2f} seconds")
            logger.debug(f"Total execution time: {time.time() - start_time:.2f} seconds")
    except (IntegrityError, DatabaseError) as e:
        print(f"Transaction failed: {str(e)}")
        logger.error(f"Transaction failed: {str(e)}", exc_info=True)
        raise
    finally:
        print(output.getvalue(), end='', flush=True)
        output.close()

if __name__ == '__main__':
    try:
        generate_fake_data()
        print("Fake data generation completed!")
        logger.info("Fake data generation completed")
    except Exception as e:
        print(f"Error during data generation: {str(e)}")
        logger.error(f"Error during data generation: {str(e)}", exc_info=True)
        sys.exit(1)