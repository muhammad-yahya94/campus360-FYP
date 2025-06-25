import os
import django
import random
import sys
from datetime import timedelta, datetime, time
from faker import Faker
from django.utils import timezone
from django.core.files.base import ContentFile
import uuid
from PIL import Image
import io
import string

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from academics.models import Faculty, Department, Program, Semester
    from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
    from courses.models import Course, CourseOffering, Venue, TimetableSlot, StudyMaterial, Assignment, AssignmentSubmission, Notice, ExamResult, Attendance
    from faculty_staff.models import Teacher
    from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
    from users.models import CustomUser
    from django.core.exceptions import ValidationError
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

fake = Faker()

# Muslim names
muslim_first_names_male = ['Ahmed', 'Ali', 'Hassan', 'Omar', 'Ibrahim', 'Yousuf', 'Abdullah', 'Hamza', 'Bilal', 'Khalid']
muslim_first_names_female = ['Aisha', 'Fatima', 'Maryam', 'Zainab', 'Khadija', 'Amna', 'Hafsa', 'Sana', 'Noor', 'Sara']
muslim_last_names = ['Khan', 'Ahmed', 'Malik', 'Hussain', 'Shah', 'Iqbal', 'Chaudhry', 'Mahmood', 'Siddiqui', 'Zafar']

# University data
university_faculties = [
    'Faculty of Engineering and Technology',
    'Faculty of Sciences'
]
university_departments = {
    'Faculty of Engineering and Technology': ['Computer Science', 'Electrical Engineering'],
    'Faculty of Sciences': ['Mathematics', 'Physics']
}
university_programs = {
    'Computer Science': ['BSCS', 'BSIT', 'MSCS', 'MSIT'],
    'Electrical Engineering': ['BSEE'],
    'Mathematics': ['BSMath'],
    'Physics': ['BSPhysics']
}
course_data = [
    ('CS101', 'Introduction to Programming'),
    ('CS102', 'Object-Oriented Programming'),
    ('CS201', 'Data Structures'),
    ('CS202', 'Algorithms'),
    ('CS203', 'Discrete Mathematics'),
    ('CS301', 'Database Systems'),
    ('CS302', 'Operating Systems'),
    ('CS303', 'Computer Architecture'),
    ('CS304', 'Software Engineering'),
    ('CS305', 'Artificial Intelligence'),
    ('CS306', 'Machine Learning'),
    ('CS307', 'Computer Networks'),
    ('CS308', 'Web Development'),
    ('CS309', 'Cybersecurity Fundamentals'),
    ('CS310', 'Cloud Computing'),
    ('CS311', 'Mobile Application Development'),
    ('CS312', 'Distributed Systems'),
    ('CS401', 'Advanced Programming'),
    ('CS402', 'Data Science'),
    ('CS403', 'Human-Computer Interaction'),
    ('CS404', 'Internet of Things (IoT)'),
    ('CS405', 'Compiler Design'),
    ('CS406', 'Parallel Computing'),
    ('CS407', 'Big Data Analytics'),
    ('CS408', 'Software Testing'),
    ('CS409', 'Blockchain Technology'),
    ('CS410', 'Game Development'),
    ('CS411', 'Natural Language Processing'),
    ('CS412', 'Computer Graphics'),
    ('CS413', 'Embedded Systems'),
    ('EE101', 'Circuit Analysis'),
    ('EE202', 'Digital Electronics'),
    ('EE303', 'Signal Processing'),
    ('EE404', 'Power Systems'),
    ('MATH101', 'Calculus I'),
    ('MATH202', 'Linear Algebra'),
    ('MATH303', 'Probability and Statistics'),
    ('PHYS101', 'Mechanics'),
    ('PHYS202', 'Electromagnetism'),
    ('PHYS303', 'Quantum Physics')
]

# Additional data for new models
exam_types = ['Matriculation', 'FSc', "Bachelor's", "Master's"]
boards = ['Lahore Board', 'Federal Board', 'Karachi Board', 'Punjab University']
subjects = ['Mathematics, Physics, Chemistry', 'Computer Science, Mathematics, Physics', 'English, Biology, Chemistry']
activities = ['Debate Club', 'Football Team', 'Drama Society', 'Science Club']
positions = ['Captain', 'Secretary', 'President', 'Member']
achievements = ['1st Prize', '2nd Prize', 'Best Performer', 'Certificate of Participation']

def generate_random_code(prefix):
    """Generate a random code like AX123 or ZY789."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{letters}{numbers}"

venue_types = [
    ('LH', 'Lecture Hall', 50),
    ('CLB', 'Computer Lab', 30),
    ('PLB', 'Physics Lab', 25),
    ('CHM', 'Chemistry Lab', 25),
    ('SMR', 'Seminar Room', 40),
    ('AUD', 'Auditorium', 100),
    ('CFR', 'Conference Room', 20),
    ('STR', 'Study Room', 15)
]

days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
time_slots = [
    (time(7, 30), time(8, 15)),
    (time(8, 15), time(9, 0)),
    (time(9, 0), time(9, 45)),
    (time(9, 45), time(10, 30)),
    (time(10, 30), time(11, 15)),
    (time(11, 15), time(12, 0)),
    (time(12, 0), time(12, 45)),
    (time(12, 45), time(13, 30)),
    (time(13, 30), time(14, 15)),
    (time(14, 15), time(15, 0)),
    (time(15, 0), time(15, 45)),
    (time(15, 45), time(16, 30)),
    (time(16, 30), time(17, 15)),
    (time(17, 15), time(18, 0)),
    (time(18, 0), time(18, 45)),
    (time(18, 45), time(19, 30)),
    (time(19, 30), time(20, 15)),
    (time(20, 15), time(21, 0))
]

def create_fake_image():
    image = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4()}.png")

def create_fake_users(count=400):
    existing_users = CustomUser.objects.count()
    if existing_users >= count:
        print(f"Skipping user creation: {existing_users} users already exist")
        return list(CustomUser.objects.all())
    users = []
    existing_emails = set(CustomUser.objects.values_list('email', flat=True))
    for _ in range(count - existing_users):
        gender = random.choice(['male', 'female'])
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        first_name = random.choice(first_names)
        last_name = random.choice(muslim_last_names)
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@example.com"
        while email in existing_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@example.com"
        existing_emails.add(email)
        try:
            user = CustomUser.objects.create_user(
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                info=fake.text(max_nb_chars=200)
            )
            users.append(user)
        except Exception as e:
            print(f"Error creating user {email}: {e}")
    print(f"Created {len(users)} new users")
    return list(CustomUser.objects.all())

def create_fake_faculties():
    existing_faculties = Faculty.objects.count()
    if existing_faculties >= len(university_faculties):
        print(f"Skipping faculty creation: {existing_faculties} faculties already exist")
        return list(Faculty.objects.all())
    faculties = []
    existing_names = set(Faculty.objects.values_list('name', flat=True))
    for name in university_faculties:
        if name not in existing_names:
            try:
                faculty = Faculty.objects.create(
                    name=name,
                    slug=fake.slug(name),
                    description=fake.text(max_nb_chars=300)
                )
                faculties.append(faculty)
            except Exception as e:
                print(f"Error creating faculty {name}: {e}")
    print(f"Created {len(faculties)} new faculties")
    return list(Faculty.objects.all())

def create_fake_departments(faculties):
    existing_departments = Department.objects.count()
    expected_departments = sum(len(depts) for depts in university_departments.values())
    if existing_departments >= expected_departments:
        print(f"Skipping department creation: {existing_departments} departments already exist")
        return list(Department.objects.all())
    departments = []
    for faculty in faculties:
        available_depts = university_departments.get(faculty.name, [])
        existing_depts = set(Department.objects.filter(faculty=faculty).values_list('name', flat=True))
        for name in available_depts:
            if name not in existing_depts:
                try:
                    department = Department.objects.create(
                        faculty=faculty,
                        name=name,
                        slug=fake.slug(name),
                        code=fake.lexify(text="???").upper(),
                        introduction=fake.text(max_nb_chars=200)
                    )
                    departments.append(department)
                except Exception as e:
                    print(f"Error creating department {name}: {e}")
    print(f"Created {len(departments)} new departments")
    return list(Department.objects.all())

def create_fake_programs(departments):
    existing_programs = Program.objects.count()
    expected_programs = sum(len(progs) for progs in university_programs.values())
    if existing_programs >= expected_programs:
        print(f"Skipping program creation: {existing_programs} programs already exist")
        return list(Program.objects.all())
    programs = []
    for department in departments:
        available_programs = university_programs.get(department.name, [])
        existing_progs = set(Program.objects.filter(department=department).values_list('name', flat=True))
        for name in available_programs:
            if name not in existing_progs:
                try:
                    degree_type = 'BS' if name.startswith('BS') else 'MS'
                    duration_years = 4 if degree_type == 'BS' else 2
                    total_semesters = 8 if name == 'BSCS' else 6 if name == 'BSIT' else 4 if name.startswith('MS') else 2
                    program = Program.objects.create(
                        department=department,
                        name=name,
                        degree_type=degree_type,
                        duration_years=duration_years,
                        total_semesters=total_semesters,
                        start_year=2020,
                        is_active=True
                    )
                    programs.append(program)
                except Exception as e:
                    print(f"Error creating program {name}: {e}")
    print(f"Created {len(programs)} new programs")
    return list(Program.objects.all())

def create_fake_academic_sessions():
    existing_sessions = AcademicSession.objects.count()
    session_data = [
        ('2021-2025', 4, 8),
        ('2022-2026', 4, 8),
        ('2023-2027', 4, 8),
        ('2024-2028', 4, 8),
        ('2023-2025', 2, 4),
        ('2024-2026', 2, 4)
    ]
    expected_sessions = len(session_data)
    if existing_sessions >= expected_sessions:
        print(f"Skipping session creation: {existing_sessions} sessions already exist")
        return list(AcademicSession.objects.all())
    sessions = []
    existing_names = set(AcademicSession.objects.values_list('name', flat=True))
    for name, years, _ in session_data:
        if name not in existing_names:
            start_year = int(name.split('-')[0])
            try:
                session = AcademicSession.objects.create(
                    name=name,
                    start_year=start_year,
                    end_year=start_year + years,
                    is_active=(name in ['2024-2028', '2024-2026']),
                    description=fake.text(max_nb_chars=300)
                )
                sessions.append(session)
            except Exception as e:
                print(f"Error creating academic session {name}: {e}")
    print(f"Created {len(sessions)} new sessions")
    return list(AcademicSession.objects.all())

def create_fake_semesters(programs, sessions):
    existing_semesters = Semester.objects.count()
    session_data = {
        '2021-2025': 8, '2022-2026': 8, '2023-2027': 8, '2024-2028': 8,
        '2023-2025': 4, '2024-2026': 4
    }
    expected_semesters = sum(session_data.get(s.name, 2) for s in sessions for p in programs)
    if existing_semesters >= expected_semesters:
        print(f"Skipping semester creation: {existing_semesters} semesters already exist")
        return list(Semester.objects.all())
    semesters = []
    for program in programs:
        available_sessions = [s for s in sessions if (
            (program.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
            (program.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
        )]
        for session in available_sessions:
            semester_count = session_data.get(session.name, 2)
            session_start_year = int(session.name.split('-')[0])
            for i in range(1, semester_count + 1):
                if not Semester.objects.filter(program=program, session=session, number=i).exists():
                    try:
                        months_offset = (i - 1) * 6
                        semester_start = datetime(session_start_year, 1, 1) + timedelta(days=months_offset * 30.42)
                        semester_end = semester_start + timedelta(days=180)
                        if not timezone.is_aware(semester_start):
                            semester_start = timezone.make_aware(semester_start)
                        if not timezone.is_aware(semester_end):
                            semester_end = timezone.make_aware(semester_end)
                        semester = Semester.objects.create(
                            program=program,
                            session=session,
                            number=i,
                            name=f"Semester {i}",
                            start_time=semester_start,
                            end_time=semester_end,
                            is_active=(i == 1 and session.is_active),
                            description=fake.text(max_nb_chars=200)
                        )
                        semesters.append(semester)
                    except Exception as e:
                        print(f"Error creating semester {i} for program {program.name} and session {session.name}: {e}")
    print(f"Created {len(semesters)} new semesters")
    return list(Semester.objects.all())

def create_fake_admission_cycles(programs, sessions):
    existing_cycles = AdmissionCycle.objects.count()
    expected_cycles = sum(len([s for s in sessions if (
        (p.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
        (p.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
    )]) for p in programs)
    if existing_cycles >= expected_cycles:
        print(f"Skipping admission cycle creation: {existing_cycles} admission cycles already exist")
        return list(AdmissionCycle.objects.all())
    admission_cycles = []
    for program in programs:
        for session in sessions:
            if (
                (program.degree_type == 'BS' and session.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
                (program.degree_type == 'MS' and session.name in ['2023-2025', '2024-2026'])
            ):
                if not AdmissionCycle.objects.filter(program=program, session=session).exists():
                    try:
                        application_start = fake.date_this_year()
                        application_end = application_start + timedelta(days=30)
                        application_start_dt = datetime.combine(application_start, time(0, 0))
                        application_end_dt = datetime.combine(application_end, time(23, 59))
                        if not timezone.is_aware(application_start_dt):
                            application_start_dt = timezone.make_aware(application_start_dt)
                        if not timezone.is_aware(application_end_dt):
                            application_end_dt = timezone.make_aware(application_end_dt)
                        admission_cycle = AdmissionCycle.objects.create(
                            program=program,
                            session=session,
                            application_start=application_start_dt,
                            application_end=application_end_dt,
                            is_open=session.is_active
                        )
                        admission_cycles.append(admission_cycle)
                    except Exception as e:
                        print(f"Error creating admission cycle for program {program.name}: {e}")
    print(f"Created {len(admission_cycles)} new admission cycles")
    return list(AdmissionCycle.objects.all())

def create_fake_applicants(users, faculties, departments, programs, sessions):
    existing_applicants = Applicant.objects.count()
    expected_applicants = min(260, sum(50 if p.degree_type == 'BS' else 20 for p in programs))
    if existing_applicants >= expected_applicants:
        print(f"Skipping applicant creation: {existing_applicants} applicants already exist")
        return list(Applicant.objects.all())
    applicants = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists()]
    shifts = ['morning', 'evening']
    session_counts = {s.name: Applicant.objects.filter(session=s).count() for s in sessions}
    max_per_session = expected_applicants // len(sessions) + 50
    program_applicants = {p.name: 0 for p in programs}
    for program in programs:
        student_count = 50 if program.degree_type == 'BS' else 20
        program_shifts = [shift for shift in shifts for _ in range(student_count // 2)]
        random.shuffle(program_shifts)
        existing_for_program = Applicant.objects.filter(program=program).count()
        needed = max(0, student_count - existing_for_program)
        valid_sessions = [s for s in sessions if (
            (program.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
            (program.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
        )]
        if not valid_sessions:
            valid_sessions = sessions[:]
        for i in range(needed):
            if not available_users:
                print(f"Warning: No available users for applicants for program {program.name}. Stopping applicant creation.")
                break
            user = random.choice(available_users)
            gender = random.choice(['male', 'female'])
            first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
            full_name = f"{random.choice(first_names)} {random.choice(muslim_last_names)}"
            if valid_sessions:
                session = min(valid_sessions, key=lambda s: session_counts.get(s.name, 0), default=None)
                if session and session_counts.get(session.name, 0) >= max_per_session:
                    valid_sessions.remove(session)
                    if not valid_sessions:
                        session = random.choice(sessions)
                if not session:
                    session = random.choice(sessions)
            else:
                session = random.choice(sessions)
            session_counts[session.name] = session_counts.get(session.name, 0) + 1
            program_applicants[program.name] += 1
            cnic = f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}"
            attempts = 0
            max_attempts = 5
            while Applicant.objects.filter(cnic=cnic).exists() and attempts < max_attempts:
                cnic = f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}"
                attempts += 1
            if attempts >= max_attempts:
                print(f"Warning: Could not generate unique CNIC for {full_name} after {max_attempts} attempts")
                continue
            try:
                applicant = Applicant.objects.create(
                    user=user,
                    faculty=program.department.faculty,
                    department=program.department,
                    program=program,
                    session=session,
                    status='accepted',
                    full_name=full_name,
                    religion='Islam',
                    cnic=cnic,
                    dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                    contact_no=f"0{random.randint(3000000000,9999999999):010d}",
                    father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                    father_occupation=fake.job(),
                    permanent_address=fake.address().replace('\n', ', '),
                    shift=program_shifts[i % len(program_shifts)],
                    declaration=True
                )
                applicants.append(applicant)
                available_users.remove(user)
            except Exception as e:
                print(f"Error creating applicant {full_name} for {program.name}: {e}")
                continue
        print(f"Created {program_applicants[program.name]} applicants for {program.name} (target: {student_count})")
    print(f"Created {len(applicants)} new applicants")
    return list(Applicant.objects.all())

def create_fake_academic_qualifications(applicants):
    existing_qualifications = AcademicQualification.objects.count()
    expected_qualifications = sum(random.randint(2, 3) for _ in applicants)
    if existing_qualifications >= expected_qualifications:
        print(f"Skipping academic qualification creation: {existing_qualifications} qualifications already exist")
        return list(AcademicQualification.objects.all())
    qualifications = []
    for applicant in applicants:
        existing_count = AcademicQualification.objects.filter(applicant=applicant).count()
        needed = random.randint(2, 3) - existing_count
        for _ in range(max(0, needed)):
            try:
                exam_passed = random.choice(exam_types)
                total_marks = random.choice([800, 1100, 1200])
                marks_obtained = random.randint(int(total_marks * 0.6), total_marks)
                qualification = AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=exam_passed,
                    passing_year=fake.year(),
                    marks_obtained=marks_obtained,
                    total_marks=total_marks,
                    division=random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                    subjects=random.choice(subjects),
                    board=random.choice(boards),
                    certificate_file=create_fake_image()
                )
                qualifications.append(qualification)
            except Exception as e:
                print(f"Error creating academic qualification for {applicant.full_name}: {e}")
    print(f"Created {len(qualifications)} new academic qualifications")
    return list(AcademicQualification.objects.all())

def create_fake_extra_curricular_activities(applicants):
    existing_activities = ExtraCurricularActivity.objects.count()
    expected_activities = sum(random.randint(1, 2) for _ in applicants)
    if existing_activities >= expected_activities:
        print(f"Skipping extra-curricular activity creation: {existing_activities} activities already exist")
        return list(ExtraCurricularActivity.objects.all())
    activities_list = []
    for applicant in applicants:
        existing_count = ExtraCurricularActivity.objects.filter(applicant=applicant).count()
        needed = random.randint(1, 2) - existing_count
        for _ in range(max(0, needed)):
            try:
                activity = ExtraCurricularActivity.objects.create(
                    applicant=applicant,
                    activity=random.choice(activities),
                    position=random.choice(positions),
                    achievement=random.choice(achievements),
                    activity_year=fake.year(),
                    certificate_file=create_fake_image()
                )
                activities_list.append(activity)
            except Exception as e:
                print(f"Error creating extra-curricular activity for {applicant.full_name}: {e}")
    print(f"Created {len(activities_list)} new extra-curricular activities")
    return list(ExtraCurricularActivity.objects.all())

def create_fake_teachers(users, departments):
    existing_teachers = Teacher.objects.count()
    expected_teachers = len(departments) * 25
    if existing_teachers >= expected_teachers:
        print(f"Skipping teacher creation: {existing_teachers} teachers already exist")
        return list(Teacher.objects.all())
    teachers = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists() and not Teacher.objects.filter(user=u).exists()]
    designations = ['Professor'] * 10 + ['Associate Professor'] * 8 + ['Assistant Professor'] * 5 + ['Head of Department'] * 2
    for department in departments:
        existing_count = Teacher.objects.filter(department=department).count()
        needed = 25 - existing_count
        dept_designations = designations.copy()
        random.shuffle(dept_designations)
        for _ in range(max(0, needed)):
            if not available_users:
                print(f"Warning: Not enough users for teachers in {department.name}, created {25 - needed} teachers")
                break
            user = random.choice(available_users)
            try:
                teacher = Teacher.objects.create(
                    user=user,
                    department=department,
                    designation=dept_designations.pop(),
                    contact_no=f"0{random.randint(3000000000,9999999999):010d}",
                    qualification=fake.job(),
                    hire_date=fake.date_this_decade(),
                    is_active=True,
                    experience=fake.text(max_nb_chars=300)
                )
                teachers.append(teacher)
                available_users.remove(user)
            except Exception as e:
                print(f"Error creating teacher for {department.name}: {e}")
    print(f"Created {len(teachers)} new teachers")
    return list(Teacher.objects.all())

def create_fake_courses():
    existing_courses = Course.objects.count()
    if existing_courses >= len(course_data):
        print(f"Skipping course creation: {existing_courses} courses already exist")
        return list(Course.objects.all())
    courses = []
    existing_codes = set(Course.objects.values_list('code', flat=True))
    for code, name in course_data:
        if code not in existing_codes:
            try:
                course = Course.objects.create(
                    code=code,
                    name=name,
                    credits=3,
                    lab_work=0,
                    is_active=True,
                    description=fake.text(max_nb_chars=300)
                )
                courses.append(course)
            except Exception as e:
                print(f"Error creating course {code}: {e}")
    print(f"Created {len(courses)} new courses")
    return list(Course.objects.all())

venues = []
for prefix, name, base_capacity in venue_types:
    count = random.randint(12, 15)
    for i in range(count):
        code = generate_random_code(prefix)
        capacity = int(base_capacity * random.uniform(0.8, 1.2))
        venues.append((f"{name} {code}", capacity))

def create_fake_venues(departments):
    existing_venues = Venue.objects.count()
    expected_venues = len(departments) * len(venues)
    if existing_venues >= expected_venues:
        print(f"Skipping venue creation: {existing_venues} venues already exist")
        return list(Venue.objects.all())
    venues_list = []
    for department in departments:
        existing_names = set(Venue.objects.filter(department=department).values_list('name', flat=True))
        for venue_name, capacity in venues:
            full_name = f"{venue_name} - {department.name}"
            if full_name not in existing_names:
                try:
                    venue = Venue.objects.create(
                        name=full_name,
                        department=department,
                        capacity=capacity,
                        is_active=True
                    )
                    venues_list.append(venue)
                except Exception as e:
                    print(f"Error creating venue {full_name} for {department.name}: {e}")
    print(f"Created {len(venues_list)} new venues")
    return list(Venue.objects.all())

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters):
    existing_offerings = CourseOffering.objects.count()
    expected_offerings = len(courses) * len(semesters) // 2
    if existing_offerings >= expected_offerings:
        print(f"Skipping course offering creation: {existing_offerings} offerings already exist")
        return list(CourseOffering.objects.all())
    offerings = []
    if not teachers:
        print("Error: No teachers available for course offerings")
        return []
    offering_types = ['regular', 'elective', 'core']
    shifts = ['morning', 'evening', 'both']
    for program in programs:
        program_semesters = [s for s in semesters if s.program == program]
        relevant_courses = [c for c in courses if c.code.startswith(program.department.name[:2].upper()) or c.code.startswith('CS')]
        for semester in program_semesters:
            selected_courses = random.sample(relevant_courses, min(len(relevant_courses), 5))
            for course in selected_courses:
                if not CourseOffering.objects.filter(course=course, semester=semester).exists():
                    try:
                        offering = CourseOffering.objects.create(
                            course=course,
                            teacher=random.choice(teachers),
                            department=program.department,
                            program=program,
                            academic_session=semester.session,
                            semester=semester,
                            is_active=semester.is_active,
                            current_enrollment=random.randint(10, 20),
                            offering_type=random.choice(offering_types),
                            shift=random.choice(shifts)
                        )
                        offerings.append(offering)
                    except Exception as e:
                        print(f"Error creating course offering for {course.code}: {e}")
    print(f"Created {len(offerings)} new course offerings")
    return list(CourseOffering.objects.all())

def create_fake_timetable_slots(offerings, venues, teachers):
    existing_slots = TimetableSlot.objects.count()
    expected_slots = sum(1 for _ in offerings)
    if existing_slots >= expected_slots:
        print(f"Skipping timetable slot creation: {existing_slots} slots already exist")
        return list(TimetableSlot.objects.all())
    slots = []
    max_retries = 30
    for offering in offerings:
        existing_count = TimetableSlot.objects.filter(course_offering=offering).count()
        needed = 1 - existing_count
        used_days = set(slot.day for slot in TimetableSlot.objects.filter(course_offering=offering))
        available_days = [day for day in days if day not in used_days]
        random.shuffle(available_days)
        used_combinations = {(slot.day, slot.start_time, slot.venue_id, slot.course_offering.teacher_id)
                            for slot in TimetableSlot.objects.filter(course_offering=offering)}
        available_venues = list(venues)
        random.shuffle(available_venues)
        available_teachers = [t for t in teachers if t.department == offering.department]
        random.shuffle(available_teachers)
        slot_count = 0
        for i in range(needed):
            if not available_days:
                print(f"Warning: Not enough days for {offering.course.code}, created {slot_count} of {needed} slots")
                break
            day = available_days.pop(0)
            day_slots = [(start, end) for start, end in time_slots]
            random.shuffle(day_slots)
            for start_time, end_time in day_slots:
                for venue in available_venues:
                    for teacher in available_teachers:
                        if slot_count >= needed:
                            break
                        if teacher != offering.teacher:
                            try:
                                offering.teacher = teacher
                                offering.save()
                            except Exception as e:
                                print(f"Error updating teacher for {offering.course.code}: {e}")
                                continue
                        teacher_conflict = TimetableSlot.objects.filter(
                            course_offering__teacher=teacher,
                            day=day,
                            start_time=start_time,
                            course_offering__semester=offering.semester
                        ).exists()
                        venue_conflict = TimetableSlot.objects.filter(
                            venue=venue,
                            day=day,
                            start_time=start_time,
                            course_offering__semester=offering.semester
                        ).exists()
                        slot_used = (day, start_time, venue.id, teacher.id) in used_combinations
                        if not teacher_conflict and not venue_conflict and not slot_used:
                            try:
                                slot = TimetableSlot.objects.create(
                                    course_offering=offering,
                                    day=day,
                                    start_time=start_time,
                                    end_time=end_time,
                                    venue=venue
                                )
                                slot.clean()
                                slots.append(slot)
                                used_combinations.add((day, start_time, venue.id, teacher.id))
                                slot_count += 1
                                break
                            except Exception as e:
                                print(f"Error creating timetable slot for {offering.course.code}: {e}")
                                continue
                    if slot_count >= needed:
                        break
                if slot_count >= needed:
                    break
            if slot_count < needed:
                print(f"Warning: Could not create slot {i+1} for {offering.course.code} on a unique day")
    print(f"Created {len(slots)} new timetable slots")
    return list(TimetableSlot.objects.all())

def create_fake_study_materials(offerings, teachers):
    existing_materials = StudyMaterial.objects.count()
    expected_materials = sum(10 for _ in offerings)
    if existing_materials >= expected_materials:
        print(f"Skipping study material creation: {existing_materials} materials already exist")
        return list(StudyMaterial.objects.all())
    materials = []
    for offering in offerings:
        existing_count = StudyMaterial.objects.filter(course_offering=offering).count()
        needed = 10 - existing_count
        for i in range(max(0, needed)):
            try:
                material = StudyMaterial.objects.create(
                    course_offering=offering,
                    teacher=offering.teacher,
                    title=fake.sentence(nb_words=4),
                    description=fake.text(max_nb_chars=200),
                    links=fake.url() if random.choice([True, False]) else None,
                    video=fake.url() if random.choice([True, False]) else None,
                    image=create_fake_image() if random.choice([True, False]) else None
                )
                materials.append(material)
            except Exception as e:
                print(f"Error creating study material for {offering.course.code}: {e}")
    print(f"Created {len(materials)} new study materials")
    return list(StudyMaterial.objects.all())

def create_fake_assignments(offerings, teachers):
    existing_assignments = Assignment.objects.count()
    expected_assignments = sum(5 for _ in offerings)
    if existing_assignments >= expected_assignments:
        print(f"Skipping assignment creation: {existing_assignments} assignments already exist")
        return list(Assignment.objects.all())
    assignments = []
    for offering in offerings:
        existing_count = Assignment.objects.filter(course_offering=offering).count()
        needed = 5 - existing_count
        for i in range(max(0, needed)):
            try:
                semester_start = offering.semester.start_time
                semester_end = offering.semester.end_time
                semester_duration = (semester_end - semester_start).days
                due_offset_days = random.randint(30, max(30, semester_duration - 30))
                due_date = semester_start + timedelta(days=due_offset_days, hours=23, minutes=59)
                if not timezone.is_aware(due_date):
                    due_date = timezone.make_aware(due_date)
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    teacher=offering.teacher,
                    title=f"{fake.sentence(nb_words=4)} {i+1}",
                    description=fake.text(max_nb_chars=200),
                    due_date=due_date,
                    max_points=random.choice([50, 100, 200]),
                    resource_file=create_fake_image() if random.choice([True, False]) else None
                )
                assignments.append(assignment)
            except Exception as e:
                print(f"Error creating assignment for {offering.course.code}: {e}")
    print(f"Created {len(assignments)} new assignments")
    return list(Assignment.objects.all())

def create_fake_assignment_submissions(assignments, students):
    existing_submissions = AssignmentSubmission.objects.count()
    expected_submissions = sum(min(10, len(students)) for _ in assignments)
    if existing_submissions >= expected_submissions:
        print(f"Skipping assignment submission creation: {existing_submissions} submissions already exist")
        return list(AssignmentSubmission.objects.all())
    submissions = []
    for assignment in assignments:
        relevant_students = [s for s in students if CourseEnrollment.objects.filter(
            student_semester_enrollment__student=s, course_offering=assignment.course_offering).exists()]
        existing_students = set(AssignmentSubmission.objects.filter(assignment=assignment).values_list('student_id', flat=True))
        available_students = [s for s in relevant_students if s.id not in existing_students]
        selected_students = random.sample(available_students, min(10, len(available_students)))
        for student in selected_students:
            try:
                submit_offset_days = random.randint(0, 5)
                submitted_at = assignment.due_date - timedelta(days=submit_offset_days)
                semester_start = assignment.course_offering.semester.start_time
                submitted_at = max(submitted_at, semester_start)
                if not timezone.is_aware(submitted_at):
                    submitted_at = timezone.make_aware(submitted_at)
                submission = AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=student,
                    file=create_fake_image() if random.choice([True, False]) else None,
                    submitted_at=submitted_at,
                    mark=random.randint(0, assignment.max_points) if random.choice([True, False]) else None,
                    feedback=fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None,
                    graded_by=assignment.teacher if random.choice([True, False]) else None
                )
                submissions.append(submission)
            except Exception as e:
                print(f"Error creating submission for {assignment.title} by {student.applicant.full_name}: {e}")
    print(f"Created {len(submissions)} new assignment submissions")
    return list(AssignmentSubmission.objects.all())

def create_fake_notices(teachers):
    existing_notices = Notice.objects.count()
    expected_notices = sum(random.randint(2, 4) for _ in teachers)
    if existing_notices >= expected_notices:
        print(f"Skipping notice creation: {existing_notices} notices already exist")
        return list(Notice.objects.all())
    notices = []
    for teacher in teachers:
        existing_count = Notice.objects.filter(created_by=teacher).count()
        needed = random.randint(2, 4) - existing_count
        for _ in range(max(0, needed)):
            try:
                notice = Notice.objects.create(
                    created_by=teacher,
                    title=fake.sentence(nb_words=4),
                    content=fake.text(max_nb_chars=300),
                    is_active=random.choice([True, False])
                )
                notices.append(notice)
            except Exception as e:
                print(f"Error creating notice by {teacher.user.get_full_name()}: {e}")
    print(f"Created {len(notices)} new notices")
    return list(Notice.objects.all())

def create_fake_exam_results(offerings, students, teachers):
    existing_results = ExamResult.objects.count()
    expected_results = sum(min(10, len(students)) for _ in offerings)
    if existing_results >= expected_results:
        print(f"Skipping exam result creation: {existing_results} results already exist")
        return list(ExamResult.objects.all())
    results = []
    exam_types = ['Midterm', 'Final', 'Test', 'Project', 'Practical']
    for offering in offerings:
        relevant_students = [s for s in students if CourseEnrollment.objects.filter(
            student_semester_enrollment__student=s, course_offering=offering).exists()]
        existing_students = set(ExamResult.objects.filter(course_offering=offering).values_list('student_id', flat=True))
        available_students = [s for s in relevant_students if s.id not in existing_students]
        selected_students = random.sample(available_students, min(10, len(available_students)))
        for student in selected_students:
            exam_type = random.choice(exam_types)
            if not ExamResult.objects.filter(course_offering=offering, student=student, exam_type=exam_type).exists():
                try:
                    total_marks = random.choice([50, 100, 200])
                    result = ExamResult.objects.create(
                        course_offering=offering,
                        student=student,
                        exam_type=exam_type,
                        total_marks=total_marks,
                        marks_obtained=random.randint(int(total_marks * 0.6), total_marks),
                        graded_by=offering.teacher,
                        remarks=fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error creating exam result for {offering.course.code} by {student.applicant.full_name}: {e}")
    print(f"Created {len(results)} new exam results")
    return list(ExamResult.objects.all())

def create_fake_attendance(offerings, students, teachers):
    existing_attendance = Attendance.objects.count()
    expected_attendance = sum(20 * len([s for s in students if CourseEnrollment.objects.filter(
        student_semester_enrollment__student=s, course_offering=o).exists()]) for o in offerings)
    if existing_attendance >= expected_attendance:
        print(f"Skipping attendance creation: {existing_attendance} attendance records already exist")
        return list(Attendance.objects.all())
    attendance_records = []
    status_choices = ['present', 'absent', 'leave']
    for offering in offerings:
        relevant_students = [s for s in students if CourseEnrollment.objects.filter(
            student_semester_enrollment__student=s, course_offering=offering).exists()]
        timetable_slots = TimetableSlot.objects.filter(course_offering=offering)
        semester_start = offering.semester.start_time
        semester_end = offering.semester.end_time
        for student in relevant_students:
            existing_count = Attendance.objects.filter(student=student, course_offering=offering).count()
            needed = 20 - existing_count
            available_slots = []
            for slot in timetable_slots:
                current_date = semester_start.date()
                while current_date <= semester_end.date():
                    if slot.day.lower() == current_date.strftime('%A').lower():
                        available_slots.append((current_date, slot.start_time))
                    current_date += timedelta(days=1)
            available_slots = sorted(set(available_slots))[:needed]
            for date, start_time in available_slots:
                try:
                    attendance_date = datetime.combine(date, start_time)
                    if not timezone.is_aware(attendance_date):
                        attendance_date = timezone.make_aware(attendance_date)
                    if not Attendance.objects.filter(
                        student=student,
                        course_offering=offering,
                        date=attendance_date
                    ).exists():
                        attendance = Attendance.objects.create(
                            student=student,
                            course_offering=offering,
                            date=attendance_date,
                            status=random.choice(status_choices),
                            shift=offering.shift,
                            recorded_by=offering.teacher
                        )
                        attendance_records.append(attendance)
                except Exception as e:
                    print(f"Error creating attendance for {offering.course.code} by {student.applicant.full_name} on {date}: {e}")
    print(f"Created {len(attendance_records)} new attendance records")
    return list(Attendance.objects.all())

def create_fake_students(applicants, programs):
    existing_students = Student.objects.count()
    expected_students = len([a for a in applicants if a.status == 'accepted'])
    if existing_students >= expected_students:
        print(f"Skipping student creation: {existing_students} students already exist")
        return list(Student.objects.all())
    students = []
    for applicant in applicants:
        if applicant.status == 'accepted' and not Student.objects.filter(applicant=applicant).exists():
            try:
                student = Student.objects.create(
                    applicant=applicant,
                    registration_no=generate_random_code("STU"),
                    program=applicant.program,
                    session=applicant.session,
                    current_semester=1,
                    enrollment_date=fake.date_between(start_date=applicant.session.start_year, end_date='today')
                )
                students.append(student)
            except Exception as e:
                print(f"Error creating student for {applicant.full_name}: {e}")
    print(f"Created {len(students)} new students")
    return list(Student.objects.all())

def create_fake_student_semester_enrollments(students, semesters):
    existing_enrollments = StudentSemesterEnrollment.objects.count()
    expected_enrollments = len(students)
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping semester enrollment creation: {existing_enrollments} enrollments already exist")
        return list(StudentSemesterEnrollment.objects.all())
    enrollments = []
    for student in students:
        if not StudentSemesterEnrollment.objects.filter(student=student).exists():
            semester = [s for s in semesters if s.program == student.program and s.session == student.session and s.number == student.current_semester]
            if semester:
                try:
                    enrollment = StudentSemesterEnrollment.objects.create(
                        student=student,
                        semester=semester[0],
                        status='enrolled'
                    )
                    enrollments.append(enrollment)
                except Exception as e:
                    print(f"Error enrolling student {student.applicant.full_name} in {semester[0].name}: {e}")
    print(f"Created {len(enrollments)} new semester enrollments")
    return list(StudentSemesterEnrollment.objects.all())

def create_fake_course_enrollments(semester_enrollments, offerings):
    existing_enrollments = CourseEnrollment.objects.count()
    expected_enrollments = sum(min(4, len([o for o in offerings if o.semester == e.semester])) for e in semester_enrollments)
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping course enrollment creation: {existing_enrollments} course enrollments already exist")
        return list(CourseEnrollment.objects.all())
    enrollments = []
    for enrollment in semester_enrollments:
        available_offerings = [o for o in offerings if o.semester == enrollment.semester]
        existing_offerings = set(CourseEnrollment.objects.filter(student_semester_enrollment=enrollment).values_list('course_offering_id', flat=True))
        available_offerings = [o for o in available_offerings if o.id not in existing_offerings]
        selected_offerings = random.sample(available_offerings, min(4, len(available_offerings)))
        for offering in selected_offerings:
            try:
                course_enrollment = CourseEnrollment.objects.create(
                    student_semester_enrollment=enrollment,
                    course_offering=offering,
                    status='enrolled'
                )
                enrollments.append(course_enrollment)
            except Exception as e:
                print(f"Error enrolling {enrollment.student.applicant.full_name} in {offering.course.code}: {e}")
    print(f"Created {len(enrollments)} new course enrollments")
    return list(CourseEnrollment.objects.all())

def clear_existing_data():
    models_to_clear = [
        CustomUser, Faculty, Department, Program, Semester, AcademicSession,
        AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity,
        Teacher, Course, CourseOffering, Venue, TimetableSlot, StudyMaterial,
        Assignment, AssignmentSubmission, Notice, ExamResult, Attendance,
        Student, StudentSemesterEnrollment, CourseEnrollment
    ]
    for model in models_to_clear:
        try:
            model.objects.all().delete()
            print(f"Cleared data for {model.__name__}")
        except Exception as e:
            print(f"Error clearing data for {model.__name__}: {e}")

def main():
    print("Creating fake data...")
    clear_data = input("Clear existing data? (yes/no): ")
    if clear_data.lower() == 'yes':
        clear_existing_data()

    users = create_fake_users()
    print(f"Total users: {len(users)}")

    faculties = create_fake_faculties()
    print(f"Total faculties: {len(faculties)}")

    departments = create_fake_departments(faculties)
    print(f"Total departments: {len(departments)}")

    programs = create_fake_programs(departments)
    print(f"Total programs: {len(programs)}")

    sessions = create_fake_academic_sessions()
    print(f"Total academic sessions: {len(sessions)}")

    semesters = create_fake_semesters(programs, sessions)
    print(f"Total semesters: {len(semesters)}")

    admission_cycles = create_fake_admission_cycles(programs, sessions)
    print(f"Total admission cycles: {len(admission_cycles)}")

    applicants = create_fake_applicants(users, faculties, departments, programs, sessions)
    print(f"Total applicants: {len(applicants)}")

    academic_qualifications = create_fake_academic_qualifications(applicants)
    print(f"Total academic qualifications: {len(academic_qualifications)}")

    extra_curricular_activities = create_fake_extra_curricular_activities(applicants)
    print(f"Total extra-curricular activities: {len(extra_curricular_activities)}")

    teachers = create_fake_teachers(users, departments)
    print(f"Total teachers: {len(teachers)}")

    courses = create_fake_courses()
    print(f"Total courses: {len(courses)}")

    venues = create_fake_venues(departments)
    print(f"Total venues: {len(venues)}")

    offerings = create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters)
    print(f"Total course offerings: {len(offerings)}")

    timetable_slots = create_fake_timetable_slots(offerings, venues, teachers)
    print(f"Total timetable slots: {len(timetable_slots)}")

    study_materials = create_fake_study_materials(offerings, teachers)
    print(f"Total study materials: {len(study_materials)}")

    assignments = create_fake_assignments(offerings, teachers)
    print(f"Total assignments: {len(assignments)}")

    students = create_fake_students(applicants, programs)
    print(f"Total students: {len(students)}")

    assignment_submissions = create_fake_assignment_submissions(assignments, students)
    print(f"Total assignment submissions: {len(assignment_submissions)}")

    notices = create_fake_notices(teachers)
    print(f"Total notices: {len(notices)}")

    exam_results = create_fake_exam_results(offerings, students, teachers)
    print(f"Total exam results: {len(exam_results)}")

    attendance = create_fake_attendance(offerings, students, teachers)
    print(f"Total attendance records: {len(attendance)}")

    semester_enrollments = create_fake_student_semester_enrollments(students, semesters)
    print(f"Total semester enrollments: {len(semester_enrollments)}")

    course_enrollments = create_fake_course_enrollments(semester_enrollments, offerings)
    print(f"Total course enrollments: {len(course_enrollments)}")

    print("Fake data creation completed!")

if __name__ == "__main__":
    main()