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
from fee_management.models import FeeType, SemesterFee, FeeVoucher, StudentFeePayment, MeritList, MeritListEntry
from django.contrib.postgres.fields import JSONField

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
    'CS': ['Introduction to Programming', 'Data Structures', 'Algorithms', 'Database Systems', 'Operating Systems', 'Web Development', 'Software Engineering', 'AI Fundamentals'],
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
FEE_TYPES = ['Tuition Fee', 'Library Fee', 'Lab Fee', 'Examination Fee', 'Registration Fee']
DYNAMIC_FEE_HEADS = {
    'Tuition Fee': {'base_fee': 50000, 'misc': 5000},
    'Library Fee': {'resource_access': 2000, 'late_fine': 500},
    'Lab Fee': {'equipment': 3000, 'maintenance': 1000},
    'Examination Fee': {'midterm': 1500, 'final': 2000},
    'Registration Fee': {'admin': 1000, 'processing': 500}
}
STUDY_MATERIAL_TOPICS = ['Introduction', 'Core Concepts', 'Advanced Topics', 'Practical Applications', 'Case Studies']
STUDY_MATERIAL_TITLES = ['Lecture Notes', 'Tutorial Guide', 'Reference Material', 'Practice Problems', 'Supplementary Reading']
STUDY_MATERIAL_LINKS = [
    'https://example.com/resource1',
    'https://example.com/resource2',
    'https://example.com/video'
]

# Configuration
FACULTIES = [
    {'name': 'Faculty of Engineering and Technology', 'departments': [
        {'name': 'Department of Computer Science', 'code': 'CS', 'programs': [
            ('BS Computer Science', 'BS'), ('MS Computer Science', 'MS'), ('BSIT', 'BS')
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
    {'name': '2025-2029', 'start_year': 2025, 'end_year': 2029, 'semesters': 1},
]
STUDENTS_PER_SESSION = 10
TEACHERS_PER_DEPARTMENT = 7
ATTENDANCE_PER_STUDENT_PER_SEMESTER = 5
ASSIGNMENTS_PER_STUDENT_PER_SEMESTER = 3
NOTICES_PER_SESSION = 5
NUM_OFFICES = 3
NUM_OFFICE_STAFF_PER_OFFICE = 1
NUM_VENUES_PER_DEPARTMENT = 5
NUM_COURSES_PER_DEPARTMENT = 20
NUM_STUDY_MATERIALS_PER_COURSE = 3
NUM_FEE_VOUCHERS_PER_STUDENT = 1
NUM_MERIT_LISTS_PER_PROGRAM = 2

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
    """Create AcademicSession and Semester records, saving each individually, all sessions active."""
    sessions = []
    semesters = []
    session_count = 0
    semester_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session_data in BS_SESSIONS:
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
                        is_active=True,  # All sessions active
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
                session_info = next(s for s in BS_SESSIONS if s['name'] == session.name)
                num_semesters = session_info['semesters']
                applicable_programs = [p for p in programs if (p.degree_type == 'BS')]
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
                                is_active=(number == session_info['semesters'])
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
    
    output_str = output.getvalue()
    output.close()
    if output_str.strip():
        print(output_str, end='', flush=True)
    return teachers, user_index

def create_courses(departments, existing_course_codes):
    """
    Create Course records with predefined names, ensuring data integrity.
    
    Args:
        departments: List of Department objects
        existing_course_codes: Set of existing course codes to avoid duplicates
        
    Returns:
        List of created Course objects
    """
    courses = []
    course_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for department in departments:
                # Get course names for this department's code
                dept_code = department.code.upper()
                course_names = COURSE_NAMES.get(dept_code, [])
                
                if not course_names:
                    print(f"No course names defined for department code: {dept_code}")
                    logger.warning(f"No course names defined for department code: {dept_code}")
                    continue
                    
                for i, name in enumerate(course_names, 1):
                    # Generate course code (e.g., CS101, CS102, etc.)
                    code = f"{dept_code}{100 + i}"
                    
                    # Ensure code is unique
                    attempts = 0
                    while code in existing_course_codes and attempts < 100:
                        code = f"{dept_code}{100 + i + random.randint(1, 1000)}"
                        attempts += 1
                        
                    if attempts >= 100:
                        skip_count += 1
                        print(f"Skipping Course due to code generation failure (Skip #{skip_count})")
                        logger.warning("Skipping Course due to code generation failure")
                        continue
                        
                    # Check if course already exists
                    try:
                        course = Course.objects.get(code=code)
                        skip_count += 1
                        print(f"Skipping existing Course '{code}' (Skip #{skip_count})")
                        logger.debug(f"Skipping existing Course '{code}'")
                        courses.append(course)
                        course_count += 1
                        continue
                    except Course.DoesNotExist:
                        pass  # Course doesn't exist, we'll create it
                        
                    existing_course_codes.add(code)
                    
                    try:
                        # Create course with valid data
                        course = Course(
                            opt=random.choice([True, False]),  # Randomly make some courses optional
                            code=code,
                            name=name,
                            department=department,  # Link to department
                            credits=random.randint(1, 6),  # 1-6 credits as per model validation
                            lab_work=random.randint(0, 4),  # 0-4 lab hours as per model validation
                            is_active=random.choice([True, False]),  # Some courses might be inactive
                            description=random.choice(DESCRIPTIONS)[:1000]  # Ensure within max length
                        )
                        
                        # Save the course
                        course.full_clean()  # Explicitly validate before save
                        course.save()
                        
                        # Add to our list of created courses
                        courses.append(course)
                        course_count += 1
                        
                        print(f"{course_count}. Created course: {code} - {name}")
                        logger.info(f"Created course: {code} - {name}")
                        
                    except ValidationError as ve:
                        skip_count += 1
                        print(f"Skipping Course '{code}' due to validation error: {ve} (Skip #{skip_count})")
                        logger.warning(f"Validation error for course {code}: {ve}")
                        continue
                        
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping Course '{code}' due to database error: {e} (Skip #{skip_count})")
                        logger.error(f"Database error creating course {code}: {e}")
                        continue
                        
                    except Exception as e:
                        skip_count += 1
                        print(f"Skipping Course '{code}' due to unexpected error: {e} (Skip #{skip_count})")
                        logger.error(f"Unexpected error creating course {code}: {e}", exc_info=True)
                        continue
            
            # Print summary
            print(f"\n=== Course Creation Summary ===")
            print(f"Total courses created: {course_count}")
            print(f"Total courses skipped: {skip_count}")
            logger.info(f"Created {course_count} courses, skipped {skip_count}")
    
    # Ensure output is flushed
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
    """Create AdmissionCycle records, saving each individually, 2025-2029 open."""
    admission_cycles = []
    cycle_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if (p.degree_type == 'BS')]
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
                            is_open=(session.start_year == 2025)  # Open for 2025-2029
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
                applicable_programs = [p for p in programs if (p.degree_type == 'BS')]
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
                                    Registration_number=f"{session.name.split('-')[0]}-GGCJ-{random.randint(10000, 99999)}",
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
                        credits = offering.course.credits
                        lab_work = offering.course.lab_work
                        midterm_obtained = random.randint(0, credits * 4)
                        midterm_total = credits * 4
                        final_obtained = random.randint(0, credits * 14)
                        final_total = credits * 14
                        sessional_obtained = random.randint(0, credits * 2)
                        sessional_total = credits * 2
                        practical_obtained = random.randint(0, lab_work * 20) if lab_work > 0 else 0
                        practical_total = lab_work * 20 if lab_work > 0 else 0
                        total_marks = midterm_obtained + final_obtained + sessional_obtained + practical_obtained
                        max_marks = midterm_total + final_total + sessional_total + practical_total
                        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
                        exam_result = ExamResult(
                            course_offering=offering,
                            student=student,
                            midterm_obtained=midterm_obtained,
                            midterm_total=midterm_total,
                            final_obtained=final_obtained,
                            final_total=final_total,
                            sessional_obtained=sessional_obtained,
                            sessional_total=sessional_total,
                            practical_obtained=practical_obtained,
                            practical_total=practical_total,
                            total_marks=total_marks,
                            percentage=percentage,
                            is_fail=False,
                            is_published=random.choice([True, False]),
                            published_at=timezone.now() if random.choice([True, False]) else None,
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
                applicable_programs = [p for p in programs if (p.degree_type == 'BS')]
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

def create_fee_types():
    """Create FeeType records, saving each individually."""
    fee_types = []
    fee_type_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for name in FEE_TYPES:
                if FeeType.objects.filter(name=name).exists():
                    skip_count += 1
                    print(f"Skipping existing FeeType '{name}' (Skip #{skip_count})")
                    logger.debug(f"Skipping existing FeeType '{name}'")
                    fee_types.append(FeeType.objects.get(name=name))
                    fee_type_count += 1
                    continue
                try:
                    fee_type = FeeType(
                        name=name,
                        description=random.choice(DESCRIPTIONS),
                        is_active=True
                    )
                    fee_type.save()
                    fee_types.append(fee_type)
                    fee_type_count += 1
                    print(f"{fee_type_count} fee type created: {name}")
                    logger.debug(f"FeeType {fee_type_count}: {name}")
                except IntegrityError as e:
                    skip_count += 1
                    print(f"Skipping FeeType '{name}' due to conflict: {str(e)} (Skip #{skip_count})")
                    logger.warning(f"Skipping FeeType '{name}': {str(e)}")
                    continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return fee_types

def create_semester_fees(fee_types):
    """Create SemesterFee records, saving each individually."""
    semester_fees = []
    semester_fee_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for fee_type in fee_types:
                for shift in ['morning', 'evening']:
                    if SemesterFee.objects.filter(fee_type=fee_type, shift=shift).exists():
                        skip_count += 1
                        print(f"Skipping existing SemesterFee for {fee_type.name} ({shift}) (Skip #{skip_count})")
                        logger.debug(f"Skipping existing SemesterFee for {fee_type.name} ({shift})")
                        semester_fees.append(SemesterFee.objects.get(fee_type=fee_type, shift=shift))
                        semester_fee_count += 1
                        continue
                    try:
                        dynamic_fees = DYNAMIC_FEE_HEADS.get(fee_type.name, {})
                        total_amount = sum(dynamic_fees.values())
                        semester_fee = SemesterFee(
                            fee_type=fee_type,
                            is_active=True,
                            shift=shift,
                            dynamic_fees=dynamic_fees,
                            total_amount=total_amount
                        )
                        semester_fee.save()
                        semester_fees.append(semester_fee)
                        semester_fee_count += 1
                        print(f"{semester_fee_count} semester fee created: {fee_type.name} ({shift})")
                        logger.debug(f"SemesterFee {semester_fee_count}: {fee_type.name} ({shift})")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping SemesterFee for {fee_type.name} ({shift}) due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping SemesterFee for {fee_type.name} ({shift}): {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return semester_fees

def create_fee_to_programs(semester_fees, sessions, programs, semesters):
    """Create FeeToProgram records, saving each individually."""
    fee_to_programs = []
    fee_to_program_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if p.degree_type == 'BS']
                applicable_semesters = [s for s in semesters if s.session == session]
                for semester_fee in semester_fees:
                    for program in applicable_programs:
                        for semester in applicable_semesters:
                            if semester.program != program:
                                continue
                            if FeeToProgram.objects.filter(SemesterFee=semester_fee, academic_session=session, programs=program, semester_number=semester).exists():
                                skip_count += 1
                                print(f"Skipping existing FeeToProgram for {semester_fee.fee_type.name} in {session.name} (Skip #{skip_count})")
                                logger.debug(f"Skipping existing FeeToProgram for {semester_fee.fee_type.name}")
                                fee_to_programs.append(FeeToProgram.objects.get(SemesterFee=semester_fee, academic_session=session, programs=program, semester_number=semester))
                                fee_to_program_count += 1
                                continue
                            try:
                                fee_to_program = FeeToProgram(
                                    SemesterFee=semester_fee,
                                    academic_session=session
                                )
                                fee_to_program.save()
                                fee_to_program.programs.add(program)
                                fee_to_program.semester_number.add(semester)
                                fee_to_programs.append(fee_to_program)
                                fee_to_program_count += 1
                                print(f"{fee_to_program_count} fee to program created: {semester_fee.fee_type.name} in {session.name}")
                                logger.debug(f"FeeToProgram {fee_to_program_count}: {semester_fee.fee_type.name} in {session.name}")
                            except IntegrityError as e:
                                skip_count += 1
                                print(f"Skipping FeeToProgram for {semester_fee.fee_type.name} in {session.name} due to conflict: {str(e)} (Skip #{skip_count})")
                                logger.warning(f"Skipping FeeToProgram for {semester_fee.fee_type.name} in {session.name}: {str(e)}")
                                continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return fee_to_programs

def create_student_fee_payments(students, semester_fees):
    """Create StudentFeePayment records, saving each individually."""
    student_fee_payments = []
    payment_count = 0
    skip_count = 0
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for student in students:
                applicable_fees = [f for f in semester_fees if f.shift == student.applicant.shift]
                for semester_fee in applicable_fees:
                    if StudentFeePayment.objects.filter(student=student, semester_fee=semester_fee).exists():
                        skip_count += 1
                        print(f"Skipping existing StudentFeePayment for {student.user.email} in {semester_fee.fee_type.name} (Skip #{skip_count})")
                        logger.debug(f"Skipping existing StudentFeePayment for {student.user.email}")
                        student_fee_payments.append(StudentFeePayment.objects.get(student=student, semester_fee=semester_fee))
                        payment_count += 1
                        continue
                    try:
                        amount_paid = semester_fee.total_amount * random.uniform(0.8, 1.0)
                        payment = StudentFeePayment(
                            student=student,
                            semester_fee=semester_fee,
                            amount_paid=amount_paid,
                            remarks=random.choice(SENTENCES)
                        )
                        payment.save()
                        student_fee_payments.append(payment)
                        payment_count += 1
                        print(f"{payment_count} student fee payment created: {student.user.email} for {semester_fee.fee_type.name}")
                        logger.debug(f"StudentFeePayment {payment_count}: {student.user.email} for {semester_fee.fee_type.name}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping StudentFeePayment for {student.user.email} in {semester_fee.fee_type.name} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping StudentFeePayment for {student.user.email} in {semester_fee.fee_type.name}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return student_fee_payments

def create_fee_vouchers(students, semester_fees, semesters, offices, student_fee_payments):
    """Create FeeVoucher records, saving each individually."""
    fee_vouchers = []
    voucher_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for student in students:
                applicable_semesters = [s for s in semesters if s.program == student.program and s.session == student.applicant.session]
                applicable_fees = [f for f in semester_fees if f.shift == student.applicant.shift]
                if not applicable_semesters or not applicable_fees:
                    print(f"No applicable semesters or fees for {student.user.email}")
                    logger.warning(f"No applicable semesters or fees for {student.user.email}")
                    continue
                for semester in applicable_semesters:
                    for semester_fee in applicable_fees:
                        if FeeVoucher.objects.filter(student=student, semester=semester, semester_fee=semester_fee).exists():
                            skip_count += 1
                            print(f"Skipping existing FeeVoucher for {student.user.email} in {semester.name} (Skip #{skip_count})")
                            logger.debug(f"Skipping existing FeeVoucher for {student.user.email} in {semester.name}")
                            fee_vouchers.append(FeeVoucher.objects.get(student=student, semester=semester, semester_fee=semester_fee))
                            voucher_count += 1
                            continue
                        try:
                            due_date = semester.start_time + timedelta(days=30)
                            payment = random.choice([p for p in student_fee_payments if p.student == student and p.semester_fee == semester_fee]) if random.choice([True, False]) else None
                            voucher = FeeVoucher(
                                student=student,
                                semester_fee=semester_fee,
                                semester=semester,
                                due_date=due_date,
                                is_paid=(payment is not None),
                                paid_at=now if payment else None,
                                payment=payment,
                                office=random.choice(offices)
                            )
                            voucher.save()
                            fee_vouchers.append(voucher)
                            voucher_count += 1
                            print(f"{voucher_count} fee voucher created: {student.user.email} in {semester.name}")
                            logger.debug(f"FeeVoucher {voucher_count}: {student.user.email} in {semester.name}")
                        except IntegrityError as e:
                            skip_count += 1
                            print(f"Skipping FeeVoucher for {student.user.email} in {semester.name} due to conflict: {str(e)} (Skip #{skip_count})")
                            logger.warning(f"Skipping FeeVoucher for {student.user.email} in {semester.name}: {str(e)}")
                            continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return fee_vouchers

def create_merit_lists(sessions, programs, applicants):
    """Create MeritList and MeritListEntry records, saving each individually."""
    merit_lists = []
    merit_list_entries = []
    merit_list_count = 0
    entry_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for session in sessions:
                applicable_programs = [p for p in programs if p.degree_type == 'BS']
                for program in applicable_programs:
                    for shift in ['morning', 'evening']:
                        for list_number in range(1, NUM_MERIT_LISTS_PER_PROGRAM + 1):
                            if MeritList.objects.filter(program=program, list_number=list_number, shift=shift, session=session).exists():
                                skip_count += 1
                                print(f"Skipping existing MeritList for {program.name} ({shift}) list {list_number} (Skip #{skip_count})")
                                logger.debug(f"Skipping existing MeritList for {program.name} ({shift}) list {list_number}")
                                merit_lists.append(MeritList.objects.get(program=program, list_number=list_number, shift=shift, session=session))
                                merit_list_count += 1
                                continue
                            try:
                                merit_list = MeritList(
                                    program=program,
                                    session=session,
                                    list_number=list_number,
                                    shift=shift,
                                    is_published=random.choice([True, False]),
                                    published_at=now if random.choice([True, False]) else None,
                                    created_at=now,
                                    updated_at=now
                                )
                                merit_list.save()
                                merit_lists.append(merit_list)
                                merit_list_count += 1
                                print(f"{merit_list_count} merit list created: {program.name} ({shift}) list {list_number}")
                                logger.debug(f"MeritList {merit_list_count}: {program.name} ({shift}) list {list_number}")
                            except IntegrityError as e:
                                skip_count += 1
                                print(f"Skipping MeritList for {program.name} ({shift}) list {list_number} due to conflict: {str(e)} (Skip #{skip_count})")
                                logger.warning(f"Skipping MeritList for {program.name} ({shift}) list {list_number}: {str(e)}")
                                continue
                            # Create MeritListEntry for each applicable applicant
                            applicable_applicants = [a for a in applicants if a.program == program and a.session == session and a.shift == shift]
                            selected_applicants = random.sample(applicable_applicants, min(len(applicable_applicants), 5))
                            for rank, applicant in enumerate(selected_applicants, 1):
                                if MeritListEntry.objects.filter(merit_list=merit_list, applicant=applicant).exists():
                                    skip_count += 1
                                    print(f"Skipping existing MeritListEntry for {applicant.full_name} in {program.name} (Skip #{skip_count})")
                                    logger.debug(f"Skipping existing MeritListEntry for {applicant.full_name}")
                                    merit_list_entries.append(MeritListEntry.objects.get(merit_list=merit_list, applicant=applicant))
                                    entry_count += 1
                                    continue
                                try:
                                    entry = MeritListEntry(
                                        merit_list=merit_list,
                                        applicant=applicant,
                                        rank=rank,
                                        aggregate_score=random.uniform(60.0, 95.0),
                                        remarks=random.choice(SENTENCES)
                                    )
                                    entry.save()
                                    merit_list_entries.append(entry)
                                    entry_count += 1
                                    print(f"{entry_count} merit list entry created: {applicant.full_name} in {program.name}")
                                    logger.debug(f"MeritListEntry {entry_count}: {applicant.full_name} in {program.name}")
                                except IntegrityError as e:
                                    skip_count += 1
                                    print(f"Skipping MeritListEntry for {applicant.full_name} in {program.name} due to conflict: {str(e)} (Skip #{skip_count})")
                                    logger.warning(f"Skipping MeritListEntry for {applicant.full_name} in {program.name}: {str(e)}")
                                    continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return merit_lists, merit_list_entries

def create_study_materials(courses, teachers):
    """Create StudyMaterial records, saving each individually."""
    study_materials = []
    material_count = 0
    skip_count = 0
    now = timezone.now()
    output = StringIO()
    
    with redirect_stdout(output):
        with transaction.atomic():
            for course in courses:
                department_teachers = [t for t in teachers if t.department == course.department]
                if not department_teachers:
                    print(f"No teachers available for {course.name}")
                    logger.warning(f"No teachers available for {course.name}")
                    continue
                for _ in range(NUM_STUDY_MATERIALS_PER_COURSE):
                    title = f"{random.choice(STUDY_MATERIAL_TITLES)} - {course.code}"
                    if StudyMaterial.objects.filter(course=course, title=title).exists():
                        skip_count += 1
                        print(f"Skipping existing StudyMaterial '{title}' for {course.code} (Skip #{skip_count})")
                        logger.debug(f"Skipping existing StudyMaterial '{title}' for {course.code}")
                        study_materials.append(StudyMaterial.objects.get(course=course, title=title))
                        material_count += 1
                        continue
                    try:
                        material = StudyMaterial(
                            course=course,
                            teacher=random.choice(department_teachers),
                            title=title,
                            topic=random.choice(STUDY_MATERIAL_TOPICS),
                            description=random.choice(DESCRIPTIONS),
                            material_type=random.choice([choice[0] for choice in StudyMaterial.MATERIAL_TYPES]),
                            resource_link=random.choice(STUDY_MATERIAL_LINKS) if random.choice([True, False]) else None,
                            file=create_fake_file() if random.choice([True, False]) else None,
                            is_active=True,
                            created_at=now,
                            updated_at=now
                        )
                        material.save()
                        study_materials.append(material)
                        material_count += 1
                        print(f"{material_count} study material created: {title} for {course.code}")
                        logger.debug(f"StudyMaterial {material_count}: {title} for {course.code}")
                    except IntegrityError as e:
                        skip_count += 1
                        print(f"Skipping StudyMaterial '{title}' for {course.code} due to conflict: {str(e)} (Skip #{skip_count})")
                        logger.warning(f"Skipping StudyMaterial '{title}' for {course.code}: {str(e)}")
                        continue
        print(f"Total records skipped: {skip_count}")
        logger.debug(f"Total records skipped: {skip_count}")
    
    print(output.getvalue(), end='', flush=True)
    output.close()
    return study_materials

def main():
    """Main function to orchestrate fake data generation."""
    print("Starting fake data generation...")
    logger.info("Starting fake data generation")
    start_time = time.time()
    
    try:
        # Initialize sets for unique identifiers
        existing_emails = set(CustomUser.objects.values_list('email', flat=True))
        existing_course_codes = set(Course.objects.values_list('code', flat=True))
        
        # Create users
        total_users_needed = len(BS_SESSIONS) * STUDENTS_PER_SESSION + len(FACULTIES) * len(FACULTIES[0]['departments']) * TEACHERS_PER_DEPARTMENT + NUM_OFFICES * NUM_OFFICE_STAFF_PER_OFFICE
        users = create_users(total_users_needed, existing_emails)
        print(f"Created {len(users)} users")
        logger.info(f"Created {len(users)} users")
        
        # Create faculties, departments, and programs
        faculties, departments, programs = create_faculties_departments_programs()
        print(f"Created {len(faculties)} faculties, {len(departments)} departments, {len(programs)} programs")
        logger.info(f"Created {len(faculties)} faculties, {len(departments)} departments, {len(programs)} programs")
        
        # Create sessions and semesters
        sessions, semesters = create_sessions_semesters(programs)
        print(f"Created {len(sessions)} sessions, {len(semesters)} semesters")
        logger.info(f"Created {len(sessions)} sessions, {len(semesters)} semesters")
        
        # Create teachers
        user_index = 0
        teachers, user_index = create_teachers(departments, users, user_index)
        print(f"Created {len(teachers)} teachers")
        logger.info(f"Created {len(teachers)} teachers")
        
        # Create courses
        courses = create_courses(departments, existing_course_codes)
        print(f"Created {len(courses)} courses")
        logger.info(f"Created {len(courses)} courses")
        
        # Create course offerings
        course_offerings = create_course_offerings(semesters, courses, teachers)
        print(f"Created {len(course_offerings)} course offerings")
        logger.info(f"Created {len(course_offerings)} course offerings")
        
        # Create venues
        venues = create_venues(departments)
        print(f"Created {len(venues)} venues")
        logger.info(f"Created {len(venues)} venues")
        
        # Create timetable slots
        timetable_slots = create_timetable_slots(course_offerings, venues)
        print(f"Created {len(timetable_slots)} timetable slots")
        logger.info(f"Created {len(timetable_slots)} timetable slots")
        
        # Create admission cycles
        admission_cycles = create_admission_cycles(sessions, programs)
        print(f"Created {len(admission_cycles)} admission cycles")
        logger.info(f"Created {len(admission_cycles)} admission cycles")
        
        # Create applicants and students
        applicants, students, user_index = create_applicants_students(sessions, programs, users, user_index)
        print(f"Created {len(applicants)} applicants, {len(students)} students")
        logger.info(f"Created {len(applicants)} applicants, {len(students)} students")
        
        # Create academic qualifications
        academic_qualifications = create_academic_qualifications(applicants)
        print(f"Created {len(academic_qualifications)} academic qualifications")
        logger.info(f"Created {len(academic_qualifications)} academic qualifications")
        
        # Create extracurricular activities
        extracurricular_activities = create_extracurricular_activities(applicants)
        print(f"Created {len(extracurricular_activities)} extracurricular activities")
        logger.info(f"Created {len(extracurricular_activities)} extracurricular activities")
        
        # Create semester enrollments
        semester_enrollments = create_semester_enrollments(students, semesters)
        print(f"Created {len(semester_enrollments)} semester enrollments")
        logger.info(f"Created {len(semester_enrollments)} semester enrollments")
        
        # Create course enrollments
        course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)
        print(f"Created {len(course_enrollments)} course enrollments")
        logger.info(f"Created {len(course_enrollments)} course enrollments")
        
        # Create academic records
        attendances, assignments, assignment_submissions, exam_results = create_academic_records(semester_enrollments, course_offerings, teachers)
        print(f"Created {len(attendances)} attendances, {len(assignments)} assignments, {len(assignment_submissions)} submissions, {len(exam_results)} exam results")
        logger.info(f"Created {len(attendances)} attendances, {len(assignments)} assignments, {len(assignment_submissions)} submissions, {len(exam_results)} exam results")
        
        # Create notices
        notices = create_notices(sessions, programs, teachers)
        print(f"Created {len(notices)} notices")
        logger.info(f"Created {len(notices)} notices")
        
        # Create offices and office staff
        offices, office_staffs = create_offices_staff(users, user_index)
        print(f"Created {len(offices)} offices, {len(office_staffs)} office staff")
        logger.info(f"Created {len(offices)} offices, {len(office_staffs)} office staff")
        
        # Create fee types
        fee_types = create_fee_types()
        print(f"Created {len(fee_types)} fee types")
        logger.info(f"Created {len(fee_types)} fee types")
        
        # Create semester fees
        semester_fees = create_semester_fees(fee_types)
        print(f"Created {len(semester_fees)} semester fees")
        logger.info(f"Created {len(semester_fees)} semester fees")
        
        # Create fee to programs
        fee_to_programs = create_fee_to_programs(semester_fees, sessions, programs, semesters)
        print(f"Created {len(fee_to_programs)} fee to programs")
        logger.info(f"Created {len(fee_to_programs)} fee to programs")
        
        # Create student fee payments
        student_fee_payments = create_student_fee_payments(students, semester_fees)
        print(f"Created {len(student_fee_payments)} student fee payments")
        logger.info(f"Created {len(student_fee_payments)} student fee payments")
        
        # Create fee vouchers
        fee_vouchers = create_fee_vouchers(students, semester_fees, semesters, offices, student_fee_payments)
        print(f"Created {len(fee_vouchers)} fee vouchers")
        logger.info(f"Created {len(fee_vouchers)} fee vouchers")
        
        # # Create merit lists and entries
        # merit_lists, merit_list_entries = create_merit_lists(sessions, programs, applicants)
        # print(f"Created {len(merit_lists)} merit lists, {len(merit_list_entries)} merit list entries")
        # logger.info(f"Created {len(merit_lists)} merit lists, {len(merit_list_entries)} merit list entries")
        
        # Create study materials
        study_materials = create_study_materials(courses, teachers)
        print(f"Created {len(study_materials)} study materials")
        logger.info(f"Created {len(study_materials)} study materials")
        
    except Exception as e:
        print(f"Error during data generation: {str(e)}")
        logger.error(f"Error during data generation: {str(e)}")
        raise
    
    end_time = time.time()
    print(f"Data generation completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Data generation completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()