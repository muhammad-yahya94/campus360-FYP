import os
import sys
import django
import random
import string
from datetime import time, datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from faker import Faker
import logging
from django.utils.text import slugify
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from academics.models import Faculty, Department, Program, Semester
    from admissions.models import AcademicSession, Applicant, AcademicQualification, ExtraCurricularActivity
    from courses.models import Course, CourseOffering, Venue, TimetableSlot
    from faculty_staff.models import Teacher, Office, OfficeStaff
    from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
    from users.models import CustomUser
    from payments.models import Payment
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.addFilter(lambda record: not record.name.startswith('faker'))
logger.handlers = [handler]
fake = Faker()

# Muslim names
muslim_first_names_male = ['Ahmed', 'Ali', 'Hassan', 'Omar', 'Ibrahim', 'Yousuf', 'Abdullah', 'Hamza', 'Bilal', 'Khalid']
muslim_first_names_female = ['Aisha', 'Fatima', 'Maryam', 'Zainab', 'Khadija', 'Amna', 'Hafsa', 'Sana', 'Noor', 'Sara']
muslim_last_names = ['Khan', 'Ahmed', 'Malik', 'Hussain', 'Shah', 'Iqbal', 'Chaudhry', 'Mahmood', 'Siddiqui', 'Zafar']

# University data
university_faculties = ['Faculty of Engineering and Technology']
university_departments = {
    'Faculty of Engineering and Technology': ['Computer Science', 'Electrical Engineering']
}
university_programs = {
    'Computer Science': ['BSCS', 'BSIT'],
    'Electrical Engineering': ['BSEE']
}
course_data = [
    ('CS101', 'Introduction to Programming', 3),
    ('CS102', 'Object-Oriented Programming', 3),
    ('CS201', 'Data Structures', 3),
    ('CS202', 'Algorithms', 3),
    ('CS203', 'Discrete Mathematics', 3),
    ('CS301', 'Database Systems', 3),
    ('CS302', 'Operating Systems', 3),
    ('CS303', 'Computer Architecture', 3),
    ('CS304', 'Software Engineering', 3),
    ('CS305', 'Artificial Intelligence', 3),
    ('CS306', 'Machine Learning', 3),
    ('CS307', 'Computer Networks', 3),
    ('CS308', 'Web Development', 3),
    ('CS309', 'Cybersecurity Fundamentals', 3),
    ('CS310', 'Cloud Computing', 3),
    ('CS311', 'Mobile Application Development', 3),
    ('CS312', 'Distributed Systems', 3),
    ('CS401', 'Advanced Programming', 3),
    ('CS402', 'Data Science', 3),
    ('CS403', 'Human-Computer Interaction', 3),
    ('EE101', 'Circuit Analysis', 3),
    ('EE202', 'Digital Electronics', 3)
]

exam_types = ['Matriculation', 'FSc', "Bachelor's"]
boards = ['Lahore Board', 'Federal Board', 'Karachi Board', 'Punjab University']
subjects = ['Mathematics, Physics, Chemistry', 'Computer Science, Mathematics, Physics', 'English, Biology, Chemistry']
activities = ['Debate Club', 'Football Team', 'Drama Society', 'Science Club']
positions = ['Captain', 'Secretary', 'President', 'Member']
achievements = ['1st Prize', '2nd Prize', 'Best Performer', 'Certificate of Participation']

venue_types = [
    ('LH', 'Lecture Hall', 50),
    ('CLB', 'Computer Lab', 30),
    ('SMR', 'Seminar Room', 40)
]

days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
morning_time_slots = [
    (time(8, 0), time(8, 40)),
    (time(8, 40), time(9, 20)),
    (time(9, 20), time(10, 0)),
    (time(10, 0), time(10, 40)),
    (time(10, 40), time(11, 20)),
    (time(11, 20), time(12, 0))
]
evening_time_slots = [
    (time(13, 0), time(13, 40)),
    (time(13, 40), time(14, 20)),
    (time(14, 20), time(15, 0))
]

def generate_random_code(prefix):
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{letters}{numbers}"

def delete_existing_data():
    """Delete all existing data in the specified models."""
    logger.info("Deleting existing data...")
    TimetableSlot.objects.all().delete()
    CourseOffering.objects.all().delete()
    CourseEnrollment.objects.all().delete()
    StudentSemesterEnrollment.objects.all().delete()
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    OfficeStaff.objects.all().delete()
    Office.objects.all().delete()
    Payment.objects.all().delete()
    AcademicQualification.objects.all().delete()
    ExtraCurricularActivity.objects.all().delete()
    Applicant.objects.all().delete()
    CustomUser.objects.all().delete()
    Venue.objects.all().delete()
    Course.objects.all().delete()
    Semester.objects.all().delete()
    Program.objects.all().delete()
    Department.objects.all().delete()
    Faculty.objects.all().delete()
    AcademicSession.objects.all().delete()
    logger.info("Existing data deleted.")

def create_faculties():
    """Create 1 faculty."""
    faculties = []
    for faculty_name in university_faculties:
        faculty, created = Faculty.objects.get_or_create(
            name=faculty_name,
            slug=slugify(faculty_name),
            description=fake.text(max_nb_chars=200)
        )
        faculties.append(faculty)
        logger.info(f"Created faculty: {faculty_name}")
    return faculties

def create_departments(faculties):
    """Create 2 departments for the faculty."""
    departments = []
    for faculty in faculties:
        for dept_name in university_departments[faculty.name]:
            dept, created = Department.objects.get_or_create(
                faculty=faculty,
                name=dept_name,
                slug=slugify(dept_name),
                code=dept_name[:2].upper(),
                introduction=fake.text(max_nb_chars=300),
                details=fake.text(max_nb_chars=500)
            )
            departments.append(dept)
            logger.info(f"Created department: {dept_name} under {faculty.name}")
    return departments

def create_programs(departments):
    """Create 2 programs per department."""
    programs = []
    for dept in departments:
        for prog_name in university_programs[dept.name][:2]:
            program, created = Program.objects.get_or_create(
                department=dept,
                name=prog_name,
                degree_type='BS',
                duration_years=4,
                total_semesters=8,
                start_year=2020,
                is_active=True
            )
            programs.append(program)
            logger.info(f"Created program: {prog_name} in {dept.name}")
    return programs

def create_courses():
    """Create 22 courses."""
    courses = []
    for code, name, credits in course_data:
        course, created = Course.objects.get_or_create(
            code=code,
            name=name,
            credits=credits,
            description=fake.text(max_nb_chars=200),
            is_active=True
        )
        courses.append(course)
        logger.info(f"Created course: {code} - {name}")
    return courses

def create_academic_sessions():
    """Create academic sessions for 2023-2027, 2024-2028, and 2025-2029."""
    sessions = []
    for start_year, end_year in [(2023, 2027), (2024, 2028), (2025, 2029)]:
        session, created = AcademicSession.objects.get_or_create(
            name=f"{start_year}-{end_year}",
            start_year=start_year,
            end_year=end_year,
            is_active=start_year <= 2025,
            description=fake.text(max_nb_chars=200)
        )
        sessions.append(session)
        logger.info(f"Created academic session: {session.name}")
    return sessions

def create_semesters(programs, sessions):
    """Create semesters for each program and session up to August 2025."""
    semesters = []
    current_date = timezone.now().date()
    for session in sessions:
        start_year = int(session.name.split('-')[0])
        for program in programs:
            for sem_num in range(1, 9):  # 8 semesters
                semester_start = datetime(start_year + (sem_num - 1) // 2, 8 if sem_num % 2 == 1 else 2, 1).date()
                semester_end = semester_start + timedelta(days=180)
                if semester_start <= current_date:
                    semester, created = Semester.objects.get_or_create(
                        program=program,
                        session=session,
                        number=sem_num,
                        name=f"Semester {sem_num}",
                        description=fake.text(max_nb_chars=200),
                        start_time=semester_start,
                        end_time=semester_end,
                        is_active=semester_start <= current_date <= semester_end
                    )
                    semesters.append(semester)
                    logger.info(f"Created semester: {semester} for {program.name}")
    return semesters

def create_users_and_applicants(programs, sessions):
    """Create 10 applicants (5 male, 5 female) with payment details, academic qualifications, and extracurricular activities."""
    users = []
    applicants = []
    session_2024 = AcademicSession.objects.get(name='2024-2028')
    cs_dept = Department.objects.get(name='Computer Science')
    program_bscs = Program.objects.get(name='BSCS')
    faculty = Faculty.objects.get(name='Faculty of Engineering and Technology')

    for i in range(10):
        gender = 'male' if i < 5 else 'female'
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        first_name = random.choice(first_names)
        last_name = random.choice(muslim_last_names)
        email = f"{first_name.lower}.{last_name.lower}{i}@example.com"

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'password': 'password123',
                'is_active': True
            }
        )
        users.append(user)

        applicant, created = Applicant.objects.get_or_create(
            user=user,
            session=session_2024,
            faculty=faculty,
            department=cs_dept,
            program=program_bscs,
            defaults={
                'status': 'accepted',
                'full_name': f"{first_name} {last_name}",
                'religion': 'Islam',
                'caste': random.choice(['', 'Jutt', 'Rajput', 'Sheikh']),
                'cnic': fake.numerify('#####-#######-#'),
                'dob': fake.date_of_birth(minimum_age=18, maximum_age=25),
                'contact_no': fake.phone_number()[:15],
                'identification_mark': fake.text(max_nb_chars=50) if random.choice([True, False]) else '',
                'gender': gender,
                'father_name': random.choice(muslim_first_names_male) + ' ' + random.choice(muslim_last_names),
                'father_occupation': random.choice(['Engineer', 'Doctor', 'Teacher', 'Businessman']),
                'father_cnic': fake.numerify('#####-#######-#'),
                'monthly_income': random.randint(50000, 200000),
                'relationship': 'father',
                'permanent_address': fake.address(),
                'shift': 'morning',
                'declaration': True
            }
        )
        applicants.append(applicant)

        # Create academic qualifications
        for exam in ['Matriculation', 'FSc']:
            AcademicQualification.objects.get_or_create(
                applicant=applicant,
                exam_passed=exam,
                defaults={
                    'passing_year': random.randint(2018, 2023),
                    'marks_obtained': random.randint(700, 1000),
                    'total_marks': 1100,
                    'division': random.choice(['1st Division', '2nd Division']),
                    'subjects': random.choice(subjects),
                    'board': random.choice(boards)
                }
            )

        # Create extracurricular activities
        for _ in range(random.randint(1, 3)):
            ExtraCurricularActivity.objects.get_or_create(
                applicant=applicant,
                activity=random.choice(activities),
                defaults={
                    'position': random.choice(positions),
                    'achievement': random.choice(achievements),
                    'activity_year': random.randint(2018, 2023)
                }
            )

        # Create payment details
        Payment.objects.get_or_create(
            user=applicant,
            stripe_session_id=generate_random_code('STRIPE'),
            defaults={
                'stripe_payment_intent': generate_random_code('PI'),
                'amount': Decimal(random.uniform(5000, 50000)).quantize(Decimal('0.01')),
                'status': random.choice(['pending', 'paid', 'failed'])
            }
        )

        logger.info(f"Created applicant: {applicant} with payment details")
    return users, applicants

def create_students(applicants, programs):
    """Create 10 students from applicants with CR and GR roles."""
    students = []
    program_bscs = Program.objects.get(name='BSCS')
    cr_assigned = False
    gr_assigned = False

    for i, applicant in enumerate(applicants):
        gender = applicant.gender
        student, created = Student.objects.get_or_create(
            applicant=applicant,
            defaults={
                'user': applicant.user,
                'Registration_number': generate_random_code('REG'),
                'university_roll_no': 2024000 + i,
                'college_roll_no': 2024000 + i,
                'enrollment_date': '2024-08-01',
                'program': program_bscs,
                'current_status': 'active',
                'emergency_contact': fake.name(),
                'emergency_phone': fake.phone_number()[:15],
                'role': 'CR' if not cr_assigned and gender == 'male' else 'GR' if not gr_assigned and gender == 'female' else None
            }
        )
        if student.role == 'CR':
            cr_assigned = True
        elif student.role == 'GR':
            gr_assigned = True
        students.append(student)
        logger.info(f"Created student: {student}")
    return students

def create_teachers(departments):
    """Create 5 teachers for the Computer Science department."""
    teachers = []
    cs_dept = Department.objects.get(name='Computer Science')
    designations = ['professor', 'associate_professor', 'assistant_professor', 'lecturer']
    
    for i in range(5):
        first_name = random.choice(muslim_first_names_male + muslim_first_names_female)
        last_name = random.choice(muslim_last_names)
        email = f"{first_name.lower}.{last_name.lower}{i}@uni.edu"
        
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'password': 'password123',
                'is_active': True
            }
        )
        
        teacher, created = Teacher.objects.get_or_create(
            user=user,
            defaults={
                'department': cs_dept,
                'designation': random.choice(designations),
                'contact_no': fake.phone_number()[:15],
                'qualification': f"PhD in {random.choice(['Computer Science', 'Software Engineering'])}",
                'hire_date': fake.date_between(start_date='-5y', end_date='today'),
                'is_active': True,
                'gender': random.choice(['male', 'female']),
                'linkedin_url': f"https://linkedin.com/in/{first_name.lower}{last_name.lower}",
                'experience': fake.text(max_nb_chars=300)
            }
        )
        teachers.append(teacher)
        logger.info(f"Created teacher: {teacher}")
    return teachers

def create_office_and_staff():
    """Create 1 office and 2 office staff."""
    office, created = Office.objects.get_or_create(
        name='Registrar Office',
        slug='registrar-office',
        description=fake.text(max_nb_chars=200),
        location=fake.address(),
        contact_email='registrar@uni.edu',
        contact_phone=fake.phone_number()[:15]
    )
    logger.info(f"Created office: {office}")

    staff = []
    for i in range(2):
        first_name = random.choice(muslim_first_names_male + muslim_first_names_female)
        last_name = random.choice(muslim_last_names)
        email = f"{first_name.lower}.{last_name.lower}{i}@office.uni.edu"
        
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'password': 'password123',
                'is_active': True
            }
        )
        
        staff_member, created = OfficeStaff.objects.get_or_create(
            user=user,
            office=office,
            defaults={
                'position': random.choice(['Registrar', 'Assistant Registrar']),
                'contact_no': fake.phone_number()[:15],
                'gender': random.choice(['male', 'female'])
            }
        )
        staff.append(staff_member)
        logger.info(f"Created office staff: {staff_member}")
    return office, staff

def create_venues(departments):
    """Create venues for course offerings."""
    venues = []
    cs_dept = Department.objects.get(name='Computer Science')
    for prefix, name, capacity in venue_types:
        venue, created = Venue.objects.get_or_create(
            name=f"{name} {generate_random_code(prefix)}",
            department=cs_dept,
            capacity=capacity,
            is_active=True
        )
        venues.append(venue)
        logger.info(f"Created venue: {venue}")
    return venues

def create_course_offerings_and_timetables(courses, semesters, teachers, venues):
    """Create course offerings and timetable slots for morning and evening shifts."""
    cs_dept = Department.objects.get(name='Computer Science')
    bscs_program = Program.objects.get(name='BSCS')
    session_2024 = AcademicSession.objects.get(name='2024-2028')
    semester_1 = Semester.objects.get(program=bscs_program, session=session_2024, number=1)

    for course in courses[:5]:  # Select 5 courses for semester 1
        for shift in ['morning', 'evening']:
            teacher = random.choice(teachers)
            offering, created = CourseOffering.objects.get_or_create(
                course=course,
                teacher=teacher,
                department=cs_dept,
                program=bscs_program,
                academic_session=session_2024,
                semester=semester_1,
                is_active=True,
                current_enrollment=10,
                shift=shift,
                offering_type='core'
            )
            
            time_slots = morning_time_slots if shift == 'morning' else evening_time_slots
            for day in random.sample(days, 2):  # 2 classes per week
                start_time, end_time = random.choice(time_slots)
                try:
                    slot, created = TimetableSlot.objects.get_or_create(
                        course_offering=offering,
                        day=day,
                        start_time=start_time,
                        end_time=end_time,
                        venue=random.choice(venues)
                    )
                    logger.info(f"Created timetable slot: {slot}")
                except ValidationError as e:
                    logger.warning(f"Timetable slot creation failed: {e}")
    
    logger.info("Created course offerings and timetable slots.")

def create_student_enrollments(students, semesters, course_offerings):
    """Enroll students in semester and courses."""
    semester_1 = semesters[0]  # First semester of 2024-2028
    for student in students:
        enrollment, created = StudentSemesterEnrollment.objects.get_or_create(
            student=student,
            semester=semester_1,
            status='enrolled'
        )
        for offering in course_offerings.filter(semester=semester_1, shift='morning')[:3]:
            CourseEnrollment.objects.get_or_create(
                student_semester_enrollment=enrollment,
                course_offering=offering,
                status='enrolled'
            )
        logger.info(f"Enrolled student: {student} in {semester_1}")

def main():
    """Main function to generate fake data."""
    print("Starting script...")
    delete_existing_data()
    
    faculties = create_faculties()
    departments = create_departments(faculties)
    programs = create_programs(departments)
    courses = create_courses()
    sessions = create_academic_sessions()
    semesters = create_semesters(programs, sessions)
    users, applicants = create_users_and_applicants(programs, sessions)
    students = create_students(applicants, programs)
    teachers = create_teachers(departments)
    office, staff = create_office_and_staff()
    venues = create_venues(departments)
    create_course_offerings_and_timetables(courses, semesters, teachers, venues)
    create_student_enrollments(students, semesters, CourseOffering.objects.all())
    
    logger.info("Fake data generation completed.")

if __name__ == "__main__":
    main()