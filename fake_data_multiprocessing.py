import os
import django
import random
import sys
from datetime import datetime, date, timedelta, time
from faker import Faker
from django.utils import timezone
from django.core.files.base import ContentFile
import uuid   
from PIL import Image
import io
import string
from multiprocessing import Pool, Manager
import threading
import queue
from django.db import connections
from django.contrib.auth.hashers import make_password

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
import logging

# Configure root logger to suppress Faker logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set desired level for other logs
handler = logging.StreamHandler()
handler.addFilter(lambda record: not record.name.startswith('faker'))  # Filter out faker logs
logger.handlers = [handler]
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

exam_types = ['Matriculation', 'FSc', "Bachelor's", "Master's"]
boards = ['Lahore Board', 'Federal Board', 'Karachi Board', 'Punjab University']
subjects = ['Mathematics, Physics, Chemistry', 'Computer Science, Mathematics, Physics', 'English, Biology, Chemistry']
activities = ['Debate Club', 'Football Team', 'Drama Society', 'Science Club']
positions = ['Captain', 'Secretary', 'President', 'Member']
achievements = ['1st Prize', '2nd Prize', 'Best Performer', 'Certificate of Participation']

def generate_random_code(prefix):
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
    try:
        image = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4()}.png")
    except Exception as e:
        print(f"Error creating fake image: {e}")
        return None

def worker_init():
    """Initialize Django in each process."""
    try:
        django.setup()
        connections.close_all()
    except Exception as e:
        print(f"Error initializing worker: {e}")

def threaded_create(model, objects_queue, lock, model_name):
    """Thread worker to save objects to the database."""
    while True:
        try:
            obj_data = objects_queue.get_nowait()
            with lock:
                model.objects.create(**obj_data)
        except queue.Empty:
            break
        except Exception as e:
            print(f"Error creating {model_name}: {e}")

def create_fake_users(count=600, result_dict=None, key=None):
    worker_init()
    existing_users = CustomUser.objects.count()
    if existing_users >= count:
        print(f"Skipping user creation: {existing_users} users already exist")
        result = list(CustomUser.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    users = []
    existing_emails = set(CustomUser.objects.values_list('email', flat=True))
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for _ in range(count - existing_users):
        try:
            gender = random.choice(['male', 'female'])
            first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
            first_name = random.choice(first_names)
            last_name = random.choice(muslim_last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@example.com"
            while email in existing_emails:
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@example.com"
            existing_emails.add(email)
            objects_queue.put({
                'password': make_password('0000pppp'),
                'first_name': first_name,
                'last_name': last_name,
                'info': fake.text(max_nb_chars=200)
            })
        except Exception as e:
            print(f"Error queuing user: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(CustomUser, objects_queue, lock, 'user'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in user creation threads: {e}")

    try:
        users = list(CustomUser.objects.all())
        print(f"Created {len(users) - existing_users} new users")
        if result_dict is not None and key is not None:
            result_dict[key] = users
    except Exception as e:
        print(f"Error retrieving users: {e}")
        users = []
    return users

def create_fake_faculties(result_dict=None, key=None):
    worker_init()
    existing_faculties = Faculty.objects.count()
    if existing_faculties >= len(university_faculties):
        print(f"Skipping faculty creation: {existing_faculties} faculties already exist")
        result = list(Faculty.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    faculties = []
    existing_names = set(Faculty.objects.values_list('name', flat=True))
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for name in university_faculties:
        if name not in existing_names:
            try:
                objects_queue.put({
                    'name': name,
                    'slug': fake.slug(name),
                    'description': fake.text(max_nb_chars=300)
                })
            except Exception as e:
                print(f"Error queuing faculty {name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Faculty, objects_queue, lock, 'faculty'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in faculty creation threads: {e}")

    try:
        faculties = list(Faculty.objects.all())
        print(f"Created {len(faculties) - existing_faculties} new faculties")
        if result_dict is not None and key is not None:
            result_dict[key] = faculties
    except Exception as e:
        print(f"Error retrieving faculties: {e}")
        faculties = []
    return faculties

def create_fake_departments(faculties, result_dict=None, key=None):
    worker_init()
    existing_departments = Department.objects.count()
    expected_departments = sum(len(depts) for depts in university_departments.values())
    if existing_departments >= expected_departments:
        print(f"Skipping department creation: {existing_departments} departments already exist")
        result = list(Department.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    departments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for faculty in faculties:
        available_depts = university_departments.get(faculty.name, [])
        existing_depts = set(Department.objects.filter(faculty=faculty).values_list('name', flat=True))
        for name in available_depts:
            if name not in existing_depts:
                try:
                    objects_queue.put({
                        'faculty': faculty,
                        'name': name,
                        'slug': fake.slug(name),
                        'code': fake.lexify(text="???").upper(),
                        'introduction': fake.text(max_nb_chars=200)
                    })
                except Exception as e:
                    print(f"Error queuing department {name}: {e}")
                    continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Department, objects_queue, lock, 'department'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in department creation threads: {e}")

    try:
        departments = list(Department.objects.all())
        print(f"Created {len(departments) - existing_departments} new departments")
        if result_dict is not None and key is not None:
            result_dict[key] = departments
    except Exception as e:
        print(f"Error retrieving departments: {e}")
        departments = []
    return departments

def create_fake_programs(departments, result_dict=None, key=None):
    worker_init()
    existing_programs = Program.objects.count()
    expected_programs = sum(len(progs) for progs in university_programs.values())
    if existing_programs >= expected_programs:
        print(f"Skipping program creation: {existing_programs} programs already exist")
        result = list(Program.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    programs = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for department in departments:
        available_programs = university_programs.get(department.name, [])
        existing_progs = set(Program.objects.filter(department=department).values_list('name', flat=True))
        for name in available_programs:
            if name not in existing_progs:
                try:
                    degree_type = 'BS' if name.startswith('BS') else 'MS'
                    duration_years = 4 if degree_type == 'BS' else 2
                    total_semesters = 8 if name == 'BSCS' else 6 if name == 'BSIT' else 4 if name.startswith('MS') else 2
                    objects_queue.put({
                        'department': department,
                        'name': name,
                        'degree_type': degree_type,
                        'duration_years': duration_years,
                        'total_semesters': total_semesters,
                        'start_year': 2020,
                        'is_active': True
                    })
                except Exception as e:
                    print(f"Error queuing program {name}: {e}")
                    continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Program, objects_queue, lock, 'program'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in program creation threads: {e}")

    try:
        programs = list(Program.objects.all())
        print(f"Created {len(programs) - existing_programs} new programs")
        if result_dict is not None and key is not None:
            result_dict[key] = programs
    except Exception as e:
        print(f"Error retrieving programs: {e}")
        programs = []
    return programs

def create_fake_academic_sessions(result_dict=None, key=None):
    worker_init()
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
        result = list(AcademicSession.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    sessions = []
    existing_names = set(AcademicSession.objects.values_list('name', flat=True))
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for name, years, _ in session_data:
        if name not in existing_names:
            try:
                start_year = int(name.split('-')[0])
                objects_queue.put({
                    'name': name,
                    'start_year': start_year,
                    'end_year': start_year + years,
                    'is_active': (name in ['2024-2028', '2024-2026']),
                    'description': fake.text(max_nb_chars=300)
                })
            except Exception as e:
                print(f"Error queuing session {name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(AcademicSession, objects_queue, lock, 'academic session'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in session creation threads: {e}")

    try:
        sessions = list(AcademicSession.objects.all())
        print(f"Created {len(sessions) - existing_sessions} new sessions")
        if result_dict is not None and key is not None:
            result_dict[key] = sessions
    except Exception as e:
        print(f"Error retrieving sessions: {e}")
        sessions = []
    return sessions

def create_fake_student_semester_enrollments(students, semesters, result_dict=None, key=None):
    worker_init()
    existing_enrollments = StudentSemesterEnrollment.objects.count()
    expected_enrollments = len(students) * 2  # Assume each student is enrolled in up to 2 semesters on average
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping semester enrollment creation: {existing_enrollments} enrollments already exist")
        result = list(StudentSemesterEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for student in students:
        try:
            # Filter semesters for the student's program and session
            program_semesters = [s for s in semesters if s.program == student.program and s.session == student.applicant.session]
            if not program_semesters:
                print(f"No valid semesters found for {student.applicant.full_name} in program {student.program.name}")
                continue
            # Determine how many semesters the student should be enrolled in
            session_start_year = student.applicant.session.start_year
            current_date = timezone.now().date()
            years_elapsed = current_date.year - session_start_year
            max_semesters = min(student.program.total_semesters, max(1, years_elapsed * 2))  # 2 semesters per year
            num_semesters = random.randint(1, max_semesters)  # Randomly enroll in 1 to max_semesters
            # Get existing semesters for this student to avoid duplicates
            existing_semesters = set(StudentSemesterEnrollment.objects.filter(student=student).values_list('semester__number', flat=True))
            # Select semesters up to num_semesters, starting from 1
            available_semesters = sorted([s for s in program_semesters if s.number not in existing_semesters], key=lambda s: s.number)
            selected_semesters = available_semesters[:num_semesters]
            for semester in selected_semesters:
                try:
                    # Generate enrollment date within the semester's duration
                    enrollment_date = fake.date_between(
                        start_date=semester.start_time,
                        end_date=min(current_date, semester.end_time)
                    )
                    enrollment_date = timezone.make_aware(datetime.combine(enrollment_date, time(random.randint(0, 23), random.randint(0, 59))))
                    objects_queue.put({
                        'student': student,
                        'semester': semester,
                        'enrollment_date': enrollment_date,
                        'status': 'enrolled',
                        'grade_point': round(random.uniform(2.0, 4.0), 2) if random.choice([True, False]) else None,
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    })
                except Exception as e:
                    print(f"Error queuing semester enrollment for {student.applicant.full_name} in {semester.name}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing semester enrollments for {student.applicant.full_name}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(StudentSemesterEnrollment, objects_queue, lock, 'semester enrollment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in semester enrollment creation threads: {e}")

    try:
        enrollments = list(StudentSemesterEnrollment.objects.all())
        print(f"Created {len(enrollments) - existing_enrollments} new semester enrollments")
        if result_dict is not None and key is not None:
            result_dict[key] = enrollments
    except Exception as e:
        print(f"Error retrieving semester enrollments: {e}")
        enrollments = []
    return enrollments

def create_fake_admission_cycles(programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_cycles = AdmissionCycle.objects.count()
    expected_cycles = sum(len([s for s in sessions if (
        (p.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
        (p.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
    )]) for p in programs)
    if existing_cycles >= expected_cycles:
        print(f"Skipping admission cycle creation: {existing_cycles} admission cycles already exist")
        result = list(AdmissionCycle.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    admission_cycles = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

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
                        objects_queue.put({
                            'program': program,
                            'session': session,
                            'application_start': application_start_dt,
                            'application_end': application_end_dt,
                            'is_open': session.is_active
                        })
                    except Exception as e:
                        print(f"Error queuing admission cycle for {program.name}: {e}")
                        continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(AdmissionCycle, objects_queue, lock, 'admission cycle'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in admission cycle creation threads: {e}")

    try:
        admission_cycles = list(AdmissionCycle.objects.all())
        print(f"Created {len(admission_cycles) - existing_cycles} new admission cycles")
        if result_dict is not None and key is not None:
            result_dict[key] = admission_cycles
    except Exception as e:
        print(f"Error retrieving admission cycles: {e}")
        admission_cycles = []
    return admission_cycles

def create_fake_applicants(users, faculties, departments, programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_applicants = Applicant.objects.count()
    expected_applicants = min(260, sum(50 if p.degree_type == 'BS' else 20 for p in programs))
    if existing_applicants >= expected_applicants:
        print(f"Skipping applicant creation: {existing_applicants} applicants already exist")
        result = list(Applicant.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    applicants = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists()]
    shifts = ['morning', 'evening']
    session_counts = {s.name: Applicant.objects.filter(session=s).count() for s in sessions}
    max_per_session = expected_applicants // len(sessions) + 50
    program_applicants = {p.name: 0 for p in programs}
    objects_queue = queue.Queue()
    lock = threading.Lock()

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
            try:
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
                objects_queue.put({
                    'user': user,
                    'faculty': program.department.faculty,
                    'department': program.department,
                    'program': program,
                    'session': session,
                    'status': 'accepted',
                    'full_name': full_name,
                    'religion': 'Islam',
                    'cnic': cnic,
                    'dob': fake.date_of_birth(minimum_age=18, maximum_age=25),
                    'contact_no': f"0{random.randint(3000000000,9999999999):010d}",
                    'father_name': f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                    'father_occupation': fake.job(),
                    'permanent_address': fake.address().replace('\n', ', '),
                    'shift': program_shifts[i % len(program_shifts)],
                    'declaration': True
                })
                available_users.remove(user)
            except Exception as e:
                print(f"Error queuing applicant for {program.name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Applicant, objects_queue, lock, 'applicant'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in applicant creation threads: {e}")

    try:
        applicants = list(Applicant.objects.all())
        print(f"Created {len(applicants) - existing_applicants} new applicants")
        if result_dict is not None and key is not None:
            result_dict[key] = applicants
    except Exception as e:
        print(f"Error retrieving applicants: {e}")
        applicants = []
    return applicants

def create_fake_academic_qualifications(applicants, result_dict=None, key=None):
    worker_init()
    existing_qualifications = AcademicQualification.objects.count()
    expected_qualifications = sum(random.randint(2, 3) for _ in applicants)
    if existing_qualifications >= expected_qualifications:
        print(f"Skipping academic qualification creation: {existing_qualifications} qualifications already exist")
        result = list(AcademicQualification.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    qualifications = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for applicant in applicants:
        existing_count = AcademicQualification.objects.filter(applicant=applicant).count()
        needed = random.randint(2, 3) - existing_count
        for _ in range(max(0, needed)):
            try:
                exam_passed = random.choice(exam_types)
                total_marks = random.choice([800, 1100, 1200])
                marks_obtained = random.randint(int(total_marks * 0.6), total_marks)
                objects_queue.put({
                    'applicant': applicant,
                    'exam_passed': exam_passed,
                    'passing_year': fake.year(),
                    'marks_obtained': marks_obtained,
                    'total_marks': total_marks,
                    'division': random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                    'subjects': random.choice(subjects),
                    'board': random.choice(boards),
                    'certificate_file': create_fake_image()
                })
            except Exception as e:
                print(f"Error queuing academic qualification for {applicant.full_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(AcademicQualification, objects_queue, lock, 'academic qualification'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in academic qualification creation threads: {e}")

    try:
        qualifications = list(AcademicQualification.objects.all())
        print(f"Created {len(qualifications) - existing_qualifications} new academic qualifications")
        if result_dict is not None and key is not None:
            result_dict[key] = qualifications
    except Exception as e:
        print(f"Error retrieving academic qualifications: {e}")
        qualifications = []
    return qualifications

def create_fake_extra_curricular_activities(applicants, result_dict=None, key=None):
    worker_init()
    existing_activities = ExtraCurricularActivity.objects.count()
    expected_activities = sum(random.randint(1, 2) for _ in applicants)
    if existing_activities >= expected_activities:
        print(f"Skipping extra-curricular activity creation: {existing_activities} activities already exist")
        result = list(ExtraCurricularActivity.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    activities_list = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for applicant in applicants:
        existing_count = ExtraCurricularActivity.objects.filter(applicant=applicant).count()
        needed = random.randint(1, 2) - existing_count
        for _ in range(max(0, needed)):
            try:
                objects_queue.put({
                    'applicant': applicant,
                    'activity': random.choice(activities),
                    'position': random.choice(positions),
                    'achievement': random.choice(achievements),
                    'activity_year': fake.year(),
                    'certificate_file': create_fake_image()
                })
            except Exception as e:
                print(f"Error queuing extra-curricular activity for {applicant.full_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(ExtraCurricularActivity, objects_queue, lock, 'extra-curricular activity'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in extra-curricular activity creation threads: {e}")

    try:
        activities_list = list(ExtraCurricularActivity.objects.all())
        print(f"Created {len(activities_list) - existing_activities} new extra-curricular activities")
        if result_dict is not None and key is not None:
            result_dict[key] = activities_list
    except Exception as e:
        print(f"Error retrieving extra-curricular activities: {e}")
        activities_list = []
    return activities_list

def create_fake_teachers(users, departments, result_dict=None, key=None):
    worker_init()
    existing_teachers = Teacher.objects.count()
    expected_teachers = len(departments) * 25
    if existing_teachers >= expected_teachers:
        print(f"Skipping teacher creation: {existing_teachers} teachers already exist")
        result = list(Teacher.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    teachers = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists() and not Teacher.objects.filter(user=u).exists()]
    designations = ['Professor'] * 10 + ['Associate Professor'] * 8 + ['Assistant Professor'] * 5 + ['Head of Department'] * 2
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for department in departments:
        existing_count = Teacher.objects.filter(department=department).count()
        needed = 25 - existing_count
        dept_designations = designations.copy()
        random.shuffle(dept_designations)
        for _ in range(max(0, needed)):
            if not available_users:
                print(f"Warning: Not enough users for teachers in {department.name}, created {25 - needed} teachers")
                break
            try:
                user = random.choice(available_users)
                objects_queue.put({
                    'user': user,
                    'department': department,
                    'designation': dept_designations.pop(),
                    'contact_no': f"0{random.randint(3000000000,9999999999):010d}",
                    'qualification': fake.job(),
                    'hire_date': fake.date_this_decade(),
                    'is_active': True,
                    'experience': fake.text(max_nb_chars=300)
                })
                available_users.remove(user)
            except Exception as e:
                print(f"Error queuing teacher for {department.name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Teacher, objects_queue, lock, 'teacher'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in teacher creation threads: {e}")

    try:
        teachers = list(Teacher.objects.all())
        print(f"Created {len(teachers) - existing_teachers} new teachers")
        if result_dict is not None and key is not None:
            result_dict[key] = teachers
    except Exception as e:
        print(f"Error retrieving teachers: {e}")
        teachers = []
    return teachers

def create_fake_course_enrollments(semester_enrollments, offerings, result_dict=None, key=None):
    worker_init()
    existing_enrollments = CourseEnrollment.objects.count()
    expected_enrollments = sum(min(4, len([o for o in offerings if o.semester == e.semester])) for e in semester_enrollments)
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping course enrollment creation: {existing_enrollments} course enrollments already exist")
        result = list(CourseEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for enrollment in semester_enrollments:
        try:
            # Filter course offerings for the student's semester and program
            available_offerings = [
                o for o in offerings
                if o.semester == enrollment.semester and o.program == enrollment.student.program
            ]
            if not available_offerings:
                print(f"No course offerings found for {enrollment.student.applicant.full_name} in {enrollment.semester.name}")
                continue
            # Avoid duplicate course enrollments
            existing_offerings = set(CourseEnrollment.objects.filter(
                student_semester_enrollment=enrollment).values_list('course_offering_id', flat=True))
            available_offerings = [o for o in available_offerings if o.id not in existing_offerings]
            selected_offerings = random.sample(available_offerings, min(4, len(available_offerings)))
            for offering in selected_offerings:
                try:
                    enrollment_date = fake.date_between(
                        start_date=enrollment.semester.start_time,
                        end_date=min(timezone.now().date(), enrollment.semester.end_time)
                    )
                    enrollment_date = timezone.make_aware(datetime.combine(enrollment_date, time(random.randint(0, 23), random.randint(0, 59))))
                    objects_queue.put({
                        'student_semester_enrollment': enrollment,
                        'course_offering': offering,
                        'enrollment_date': enrollment_date,
                        'status': 'enrolled',
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    })
                except Exception as e:
                    print(f"Error queuing course enrollment for {enrollment.student.applicant.full_name} in {offering.course.code}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing course enrollments for {enrollment.student.applicant.full_name}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(CourseEnrollment, objects_queue, lock, 'course enrollment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in course enrollment creation threads: {e}")

    try:
        enrollments = list(CourseEnrollment.objects.all())
        print(f"Created {len(enrollments) - existing_enrollments} new course enrollments")
        if result_dict is not None and key is None:
            result_dict[key] = enrollments
    except Exception as e:
        print(f"Error retrieving course enrollments: {e}")
        enrollments = []
    return enrollments

venues = []
for prefix, name, base_capacity in venue_types:
    count = random.randint(12, 15)
    for i in range(count):
        code = generate_random_code(prefix)
        capacity = int(base_capacity * random.uniform(0.8, 1.2))
        venues.append((f"{name} {code}", capacity))

def create_fake_venues(departments, result_dict=None, key=None):
    worker_init()
    existing_venues = Venue.objects.count()
    expected_venues = len(departments) * len(venues)
    if existing_venues >= expected_venues:
        print(f"Skipping venue creation: {existing_venues} venues already exist")
        result = list(Venue.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    venues_list = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for department in departments:
        existing_names = set(Venue.objects.filter(department=department).values_list('name', flat=True))
        for venue_name, capacity in venues:
            full_name = f"{venue_name} - {department.name}"
            if full_name not in existing_names:
                try:
                    objects_queue.put({
                        'name': full_name,
                        'department': department,
                        'capacity': capacity,
                        'is_active': True
                    })
                except Exception as e:
                    print(f"Error queuing venue {full_name}: {e}")
                    continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Venue, objects_queue, lock, 'venue'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in venue creation threads: {e}")

    try:
        venues_list = list(Venue.objects.all())
        print(f"Created {len(venues_list) - existing_venues} new venues")
        if result_dict is not None and key is not None:
            result_dict[key] = venues_list
    except Exception as e:
        print(f"Error retrieving venues: {e}")
        venues_list = []
    return venues_list

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, result_dict=None, key=None):
    worker_init()
    existing_offerings = CourseOffering.objects.count()
    expected_offerings = len(courses) * len(semesters) // 2
    if existing_offerings >= expected_offerings:
        print(f"Skipping course offering creation: {existing_offerings} offerings already exist")
        result = list(CourseOffering.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    offerings = []
    if not teachers:
        print("Error: No teachers available for course offerings")
        if result_dict is not None and key is not None:
            result_dict[key] = []
        return []
    offering_types = ['regular', 'elective', 'core']
    shifts = ['morning', 'evening', 'both']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for program in programs:
        program_semesters = [s for s in semesters if s.program == program]
        relevant_courses = [c for c in courses if c.code.startswith(program.department.name[:2].upper()) or c.code.startswith('CS')]
        for semester in program_semesters:
            selected_courses = random.sample(relevant_courses, min(len(relevant_courses), 5))
            for course in selected_courses:
                if not CourseOffering.objects.filter(course=course, semester=semester).exists():
                    try:
                        objects_queue.put({
                            'course': course,
                            'teacher': random.choice(teachers),
                            'department': program.department,
                            'program': program,
                            'academic_session': semester.session,
                            'semester': semester,
                            'is_active': semester.is_active,
                            'current_enrollment': random.randint(10, 20),
                            'offering_type': random.choice(offering_types),
                            'shift': random.choice(shifts)
                        })
                    except Exception as e:
                        print(f"Error queuing course offering for {course.code}: {e}")
                        continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(CourseOffering, objects_queue, lock, 'course offering'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in course offering creation threads: {e}")

    try:
        offerings = list(CourseOffering.objects.all())
        print(f"Created {len(offerings) - existing_offerings} new course offerings")
        if result_dict is not None and key is not None:
            result_dict[key] = offerings
    except Exception as e:
        print(f"Error retrieving course offerings: {e}")
        offerings = []
    return offerings

def create_fake_timetable_slots(offerings, venues, teachers, result_dict=None, key=None):
    worker_init()
    existing_slots = TimetableSlot.objects.count()
    expected_slots = sum(1 for _ in offerings)
    if existing_slots >= expected_slots:
        print(f"Skipping timetable slot creation: {existing_slots} slots already exist")
        result = list(TimetableSlot.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    slots = []
    max_retries = 30
    objects_queue = queue.Queue()
    lock = threading.Lock()

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
                                objects_queue.put({
                                    'course_offering': offering,
                                    'day': day,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'venue': venue
                                })
                                used_combinations.add((day, start_time, venue.id, teacher.id))
                                slot_count += 1
                                break
                            except Exception as e:
                                print(f"Error queuing timetable slot for {offering.course.code}: {e}")
                                continue
                    if slot_count >= needed:
                        break
                if slot_count >= needed:
                    break
            if slot_count < needed:
                print(f"Warning: Could not create slot {i+1} for {offering.course.code} on a unique day")

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(TimetableSlot, objects_queue, lock, 'timetable slot'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in timetable slot creation threads: {e}")

    try:
        slots = list(TimetableSlot.objects.all())
        print(f"Created {len(slots) - existing_slots} new timetable slots")
        if result_dict is not None and key is not None:
            result_dict[key] = slots
    except Exception as e:
        print(f"Error retrieving timetable slots: {e}")
        slots = []
    return slots

def create_fake_study_materials(offerings, teachers, result_dict=None, key=None):
    worker_init()
    existing_materials = StudyMaterial.objects.count()
    expected_materials = sum(10 for _ in offerings)
    if existing_materials >= expected_materials:
        print(f"Skipping study material creation: {existing_materials} materials already exist")
        result = list(StudyMaterial.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    materials = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        existing_count = StudyMaterial.objects.filter(course_offering=offering).count()
        needed = 10 - existing_count
        for i in range(max(0, needed)):
            try:
                objects_queue.put({
                    'course_offering': offering,
                    'teacher': offering.teacher,
                    'title': fake.sentence(nb_words=4),
                    'description': fake.text(max_nb_chars=200)
                })
            except Exception as e:
                print(f"Error queuing study material for {offering.course.code}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(StudyMaterial, objects_queue, lock, 'study material'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in study material creation threads: {e}")

    try:
        materials = list(StudyMaterial.objects.all())
        print(f"Created {len(materials) - existing_materials} new study materials")
        if result_dict is not None and key is not None:
            result_dict[key] = materials
    except Exception as e:
        print(f"Error retrieving study materials: {e}")
        materials = []
    return materials

def create_fake_assignments(offerings, teachers, result_dict=None, key=None):
    worker_init()
    existing_assignments = Assignment.objects.count()
    expected_assignments = sum(5 for _ in offerings)
    if existing_assignments >= expected_assignments:
        print(f"Skipping assignment creation: {existing_assignments} assignments already exist")
        result = list(Assignment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    assignments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        existing_count = Assignment.objects.filter(course_offering=offering).count()
        needed = 5 - existing_count
        for i in range(max(0, needed)):
            try:
                semester_start = offering.semester.start_time
                semester_end = offering.semester.end_time
                if isinstance(semester_start, date) and not isinstance(semester_start, datetime):
                    semester_start = datetime.combine(semester_start, time(0, 0))
                if isinstance(semester_end, date) and not isinstance(semester_end, datetime):
                    semester_end = datetime.combine(semester_end, time(23, 59))
                semester_duration = (semester_end - semester_start).days
                due_offset_days = random.randint(30, max(30, semester_duration - 30))
                due_date = semester_start + timedelta(days=due_offset_days)
                if not timezone.is_aware(due_date):
                    due_date = timezone.make_aware(due_date)
                objects_queue.put({
                    'course_offering': offering,
                    'teacher': offering.teacher,
                    'title': f"{fake.sentence(nb_words=4)} {i+1}",
                    'description': fake.text(max_nb_chars=200),
                    'due_date': due_date,
                    'max_points': random.choice([50, 100, 200]),
                    'resource_file': create_fake_image() if random.choice([True, False]) else None
                })
            except Exception as e:
                print(f"Error queuing assignment for {offering.course.code}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Assignment, objects_queue, lock, 'assignment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in assignment creation threads: {e}")

    try:
        assignments = list(Assignment.objects.all())
        print(f"Created {len(assignments) - existing_assignments} new assignments")
        if result_dict is not None and key is not None:
            result_dict[key] = assignments
    except Exception as e:
        print(f"Error retrieving assignments: {e}")
        assignments = []
    return assignments

def create_fake_assignment_submissions(assignments, students, result_dict=None, key=None):
    worker_init()
    existing_submissions = AssignmentSubmission.objects.count()
    # Fetch students directly from the database
    students = list(Student.objects.all())
    expected_submissions = sum(min(10, len(students)) for _ in assignments)
    if existing_submissions >= expected_submissions:
        print(f"Skipping assignment submission creation: {existing_submissions} submissions already exist")
        result = list(AssignmentSubmission.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    submissions = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for assignment in assignments:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=assignment.course_offering).exists()]
            existing_students = set(
                AssignmentSubmission.objects.filter(assignment=assignment).values_list('student__applicant_id', flat=True)
            )
            available_students = [s for s in relevant_students if s.applicant_id not in existing_students]
            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                try:
                    submit_offset_days = random.randint(0, 5)
                    submitted_at = assignment.due_date - timedelta(days=submit_offset_days)
                    semester_start = assignment.course_offering.semester.start_time
                    if isinstance(semester_start, date) and not isinstance(semester_start, datetime):
                        semester_start = assignment.course_offering.semester.start_time
                    if isinstance(semester_start, date) and not isinstance(semester_start, datetime):
                        semester_start = datetime.combine(semester_start, time(0, 0))

                    if timezone.is_naive(semester_start):
                        semester_start = timezone.make_aware(semester_start)

                    if timezone.is_naive(submitted_at):
                        submitted_at = timezone.make_aware(submitted_at)

                    submitted_at = max(submitted_at, semester_start)  

                    objects_queue.put({  
                        'assignment': assignment,
                        'student': student,
                        'file': create_fake_image() if random.choice([True, False]) else None,
                        'submitted_at': submitted_at,
                        'marks': random.randint(0, assignment.max_points) if random.choice([True, False]) else None,
                        'feedback': fake.sentence(nb_words=15) if random.choice([True, False]) else None,
                        'graded_by': assignment.teacher if random.choice([True, False]) else None
                    })
                except Exception as e:
                    print(f"Error queuing submission for {student.applicant.full_name} on {assignment.title}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing submissions for {assignment.title}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(AssignmentSubmission, objects_queue, lock, 'assignment submission'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in assignment submission creation threads: {e}")

    try:
        submissions = list(AssignmentSubmission.objects.all())
        print(f"Created {len(submissions) - existing_submissions} new assignment submissions")
        if result_dict is not None and key is not None:
            result_dict[key] = submissions
    except Exception as e:
        print(f"Error retrieving submissions: {e}")
        submissions = []
    return submissions

def create_fake_notices(teachers, result_dict=None, key=None):
    worker_init()
    existing_notices = Notice.objects.count()
    expected_notices = sum(random.randint(2, 4) for _ in teachers)
    if existing_notices >= expected_notices:
        print(f"Skipping notice creation: {existing_notices} notices already exist")
        result = list(Notice.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    notices = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for teacher in teachers:
        existing_count = Notice.objects.filter(created_by=teacher).count()
        needed = random.randint(2, 4) - existing_count
        for _ in range(max(0, needed)):
            try:
                objects_queue.put({
                    'created_by': teacher,
                    'title': fake.sentence(nb_words=4),
                    'content': fake.text(max_nb_chars=300),
                    'is_active': random.choice([True, False])
                })
            except Exception as e:
                print(f"Error queuing notice for {teacher.user.first_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Notice, objects_queue, lock, 'notice'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in notice creation threads: {e}")

    try:
        notices = list(Notice.objects.all())
        print(f"Created {len(notices) - existing_notices} new notices")
        if result_dict is not None and key is not None:
            result_dict[key] = notices
    except Exception as e:
        print(f"Error retrieving notices: {e}")
        notices = []
    return notices

def create_fake_exam_results(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_results = ExamResult.objects.count()
    # Fetch students directly from the database
    students = list(Student.objects.all())
    expected_results = sum(min(10, len(students)) for _ in offerings)
    if existing_results >= expected_results:
        print(f"Skipping exam result creation: {existing_results} results already exist")
        result = list(ExamResult.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    results = []
    exam_types = ['Midterm', 'Final', 'Test', 'Project', 'Practical']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
            student_semester_enrollment__student=s, course_offering=offering).exists()]
            existing_students = set(
                ExamResult.objects.filter(course_offering=offering).values_list('student__applicant_id', flat=True)
            )
            available_students = [s for s in relevant_students if s.applicant_id not in existing_students]

            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                exam_type = random.choice(exam_types)
                if not ExamResult.objects.filter(course_offering=offering, student=student, exam_type=exam_type).exists():
                    try:
                        total_marks = random.choice([50, 100, 200])
                        objects_queue.put({  
                            'course_offering': offering,
                            'student': student,
                            'exam_type': exam_type,
                            'total_marks': total_marks,
                            'marks_obtained': random.randint(int(total_marks * 0.6), total_marks),
                            'graded_by': offering.teacher,
                            'remarks': fake.sentence(nb_words=15) if random.choice([True, False]) else None,
                        })
                    except Exception as e:
                        print(f"Error queuing exam result for {student.applicant.full_name} in {offering.course.code}: {e}")
                        continue
        except Exception as e:
            print(f"Error processing exam results for {offering.course.code}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(ExamResult, objects_queue, lock, 'exam result'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in exam result creation threads: {e}")

    try:
        results = list(ExamResult.objects.all())
        print(f"Created {len(results) - existing_results} new exam results")
        if result_dict is not None and key is not None:
            result_dict[key] = results
    except Exception as e:
        print(f"Error retrieving exam results: {e}")
        results = []
    return results

def create_fake_attendance(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_attendance = Attendance.objects.count()
    # Estimate expected attendance based on timetable slots
    expected_attendance = sum(
        len(TimetableSlot.objects.filter(course_offering=o)) * 20 * len([
            s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=o
            ).exists()
        ]) for o in offerings
    )
    if existing_attendance >= expected_attendance:
        print(f"Skipping attendance creation: {existing_attendance} attendance records already exist")
        result = list(Attendance.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    attendance_records = []
    status_choices = ['present', 'absent', 'leave']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        try:
            # Get students enrolled in this course offering
            relevant_students = [
                s for s in students if CourseEnrollment.objects.filter(
                    student_semester_enrollment__student=s, course_offering=offering
                ).exists()
            ]
            # Get timetable slots for this course offering
            timetable_slots = TimetableSlot.objects.filter(course_offering=offering)
            if not timetable_slots:
                print(f"No timetable slots found for {offering.course.code}")
                continue

            # Get allowed days from timetable slots
            allowed_days = {slot.day.lower() for slot in timetable_slots}
            semester_start = offering.semester.start_time  # DateField
            semester_end = offering.semester.end_time      # DateField

            for student in relevant_students:
                existing_count = Attendance.objects.filter(
                    student=student, course_offering=offering
                ).count()
                needed = 20 - existing_count
                if needed <= 0:
                    continue

                # Generate a list of possible attendance dates based on allowed days
                available_dates = []
                current_date = semester_start
                while current_date <= semester_end:
                    if current_date.strftime('%A').lower() in allowed_days:
                        # Find corresponding timetable slot for the day
                        matching_slots = [
                            slot for slot in timetable_slots
                            if slot.day.lower() == current_date.strftime('%A').lower()
                        ]
                        for slot in matching_slots:
                            available_dates.append((current_date, slot.start_time))
                    current_date += timedelta(days=1)

                # Select up to 'needed' unique dates for attendance
                available_dates = sorted(set(available_dates), key=lambda x: x[0])
                selected_dates = random.sample(
                    available_dates,
                    min(needed, len(available_dates))
                )

                for date, start_time in selected_dates:
                    try:
                        attendance_date = datetime.combine(date, start_time)
                        if not timezone.is_aware(attendance_date):
                            attendance_date = timezone.make_aware(attendance_date)
                        if not Attendance.objects.filter(
                            student=student,
                            course_offering=offering,
                            date=attendance_date
                        ).exists():
                            objects_queue.put({
                                'student': student,
                                'course_offering': offering,
                                'date': attendance_date,
                                'status': random.choice(status_choices),
                                'shift': offering.shift,
                                'recorded_by': offering.teacher
                            })
                    except Exception as e:
                        print(f"Error queuing attendance for {student.applicant.full_name} in {offering.course.code}: {e}")
                        continue
        except Exception as e:
            print(f"Error processing attendance for {offering.course.code}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(
                target=threaded_create,
                args=(Attendance, objects_queue, lock, 'attendance record')
            )
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in attendance creation threads: {e}")

    try:
        attendance_records = list(Attendance.objects.all())
        print(f"Created {len(attendance_records) - existing_attendance} new attendance records")
        if result_dict is not None and key is not None:
            result_dict[key] = attendance_records
    except Exception as e:
        print(f"Error retrieving attendance records: {e}")
        attendance_records = []
    return attendance_records


def create_fake_students(applicants, programs, result_dict=None, key=None):
    worker_init()
    existing_students = Student.objects.count()
    expected_students = len([a for a in applicants if a.status == 'accepted'])
    if existing_students >= expected_students:
        print(f"Skipping student creation: {existing_students} students already exist")
        result = list(Student.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    students = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for applicant in applicants:
        if applicant.status == 'accepted' and not Student.objects.filter(applicant=applicant).exists():
            try:
                start_date = datetime(applicant.session.start_year, 1, 1).date()
                end_date = min(datetime.now().date(), datetime(applicant.session.start_year + 1, 1, 1).date())
                enrollment_date = fake.date_between(start_date=start_date, end_date=end_date)
            except Exception as e:
                print(f"Error generating enrollment_date for {applicant.full_name}: {e}")
                enrollment_date = datetime.now().date()
            try:
                objects_queue.put({
                    'applicant': applicant,
                    'user': applicant.user,
                    'university_roll_no': random.randint(100000, 999999),
                    'college_roll_no': random.randint(100000, 999999),
                    'program': applicant.program,
                    'enrollment_date': enrollment_date,
                    'current_status': 'active',
                    'emergency_contact': f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                    'emergency_phone': f"0{random.randint(3000000000,9999999999):010d}"
                })
            except Exception as e:
                print(f"Error queuing student for {applicant.full_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Student, objects_queue, lock, 'student'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in student creation threads: {e}")

    try:
        students = list(Student.objects.all())
        print(f"Created {len(students) - existing_students} new students")
        if result_dict is not None and key is not None:
            result_dict[key] = students
    except Exception as e:
        print(f"Error retrieving students: {e}")
        students = []
    return students

def create_fake_student_semester_enrollments(students, semesters, result_dict=None, key=None):
    worker_init()
    existing_enrollments = StudentSemesterEnrollment.objects.count()
    expected_enrollments = len(students)
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping semester enrollment creation: {existing_enrollments} enrollments already exist")
        result = list(StudentSemesterEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for student in students:
        if not StudentSemesterEnrollment.objects.filter(student=student).exists():
            try:
                semester = [s for s in semesters if s.program == student.program and s.session == student.applicant.session and s.number == 1]
                if not semester:
                    print(f"No matching semester found for {student.applicant.full_name}")
                    continue
                objects_queue.put({
                    'student': student,
                    'semester': semester[0],
                    'status': 'enrolled'
                })
            except Exception as e:
                print(f"Error queuing semester enrollment for {student.applicant.full_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(StudentSemesterEnrollment, objects_queue, lock, 'semester enrollment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in semester enrollment creation threads: {e}")

    try:
        enrollments = list(StudentSemesterEnrollment.objects.all())
        print(f"Created {len(enrollments) - existing_enrollments} new semester enrollments")
        if result_dict is not None and key is not None:
            result_dict[key] = enrollments
    except Exception as e:
        print(f"Error retrieving semester enrollments: {e}")
        enrollments = []
    return enrollments

def create_fake_course_enrollments(semester_enrollments, offerings, result_dict=None, key=None):
    worker_init()
    existing_enrollments = CourseEnrollment.objects.count()
    expected_enrollments = sum(min(4, len([o for o in offerings if o.semester == e.semester])) for e in semester_enrollments)
    if existing_enrollments >= expected_enrollments:
        print(f"Skipping course enrollment creation: {existing_enrollments} course enrollments already exist")
        result = list(CourseEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for enrollment in semester_enrollments:
        try:
            available_offerings = [o for o in offerings if o.semester == enrollment.semester]
            existing_offerings = set(CourseEnrollment.objects.filter(
                student_semester_enrollment=enrollment).values_list('course_offering_id', flat=True))
            available_offerings = [o for o in available_offerings if o.id not in existing_offerings]
            selected_offerings = random.sample(available_offerings, min(4, len(available_offerings)))
            for offering in selected_offerings:
                try:
                    # start_time and end_time are date objects (DateField)
                    enrollment_date = fake.date_between(
                        start_date=enrollment.semester.start_time,
                        end_date=enrollment.semester.end_time
                    )
                    objects_queue.put({
                        'student_semester_enrollment': enrollment,
                        'course_offering': offering,
                        'enrollment_date': enrollment_date,
                        'status': 'enrolled'
                    })
                except Exception as e:
                    print(f"Error queuing course enrollment for {enrollment.student.applicant.full_name} in {offering.course.code}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing course enrollments for {enrollment.student.applicant.full_name}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(CourseEnrollment, objects_queue, lock, 'course enrollment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in course enrollment creation threads: {e}")

    try:
        enrollments = list(CourseEnrollment.objects.all())
        print(f"Created {len(enrollments) - existing_enrollments} new course enrollments")
        if result_dict is not None and key is not None:
            result_dict[key] = enrollments
    except Exception as e:
        print(f"Error retrieving course enrollments: {e}")
        enrollments = []
    return enrollments

def clear_existing_data():
    models_to_clear = [
        CustomUser, Faculty, Department, Program, Semester, AcademicSession,
        AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity,
        Teacher, Course, CourseOffering, Venue, TimetableSlot, StudyMaterial, Assignment,
        AssignmentSubmission, Notice, ExamResult, Attendance,
        Student, StudentSemesterEnrollment, CourseEnrollment
    ]
    for model in models_to_clear:
        try:
            model.objects.all().delete()
            print(f"Cleared data for {model.__name__}")
        except Exception as e:
            print(f"Error clearing data for {model.__name__}: {e}")

def execute_task(func, args):
    """Execute a function with given arguments, replacing lambda for multiprocessing."""
    return func(*args)

def main():
    print("Creating fake data...")
    clear_data = input("Clear existing data? (yes/no): ")
    if clear_data.lower() == 'yes':
        clear_existing_data()

    manager = Manager()
    result_dict = manager.dict()

    # Independent tasks (no dependencies)
    independent_tasks = [
        (create_fake_users, (600, result_dict, 'users')),
        (create_fake_faculties, (result_dict, 'faculties')),
        (create_fake_academic_sessions, (result_dict, 'sessions')),
        (create_fake_course_enrollments, (result_dict, 'courses')),
    ]

    # Run independent tasks in parallel
    with Pool(processes=4, initializer=worker_init) as pool:
        pool.starmap(execute_task, independent_tasks)

    users = result_dict.get('users', [])
    faculties = result_dict.get('faculties', [])
    sessions = result_dict.get('sessions', [])
    courses = result_dict.get('courses', [])   

    # Sequential tasks with dependencies
    departments = create_fake_departments(faculties, result_dict, 'departments')
    programs = create_fake_programs(departments, result_dict, 'programs')
    semesters = create_fake_student_semester_enrollments(programs, sessions, result_dict, 'semesters')

    # Parallelize tasks with dependencies
    dependent_tasks = [
        (create_fake_admission_cycles, (programs, sessions, result_dict, 'admission_cycles')),
        (create_fake_applicants, (users, faculties, departments, programs, sessions, result_dict, 'applicants')),
        (create_fake_teachers, (users, departments, result_dict, 'teachers')),
        (create_fake_venues, (departments, result_dict, 'venues')),
    ]

    with Pool(processes=4, initializer=worker_init) as pool:
        pool.starmap(execute_task, dependent_tasks)

    admission_cycles = result_dict.get('admission_cycles', [])
    applicants = result_dict.get('applicants', [])
    teachers = result_dict.get('teachers', [])
    venues = result_dict.get('venues', [])

    # Sequential task
    offerings = create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, result_dict, 'offerings')

    # Parallelize tasks dependent on offerings
    offering_tasks = [
        (create_fake_timetable_slots, (offerings, venues, teachers, result_dict, 'timetable_slots')),
        (create_fake_study_materials, (offerings, teachers, result_dict, 'study_materials')),
        (create_fake_assignments, (offerings, teachers, result_dict, 'assignments')),
    ]

    with Pool(processes=4, initializer=worker_init) as pool:
        pool.starmap(execute_task, offering_tasks)

    timetable_slots = result_dict.get('timetable_slots', [])
    study_materials = result_dict.get('study_materials', [])
    assignments = result_dict.get('assignments', [])

    # Sequential tasks
    students = create_fake_students(applicants, programs, result_dict, 'students')
    semester_enrollments = create_fake_student_semester_enrollments(students, semesters, result_dict, 'semester_enrollments')

    # Parallelize remaining tasks
    final_tasks = [
        (create_fake_academic_qualifications, (applicants, result_dict, 'academic_qualifications')),
        (create_fake_extra_curricular_activities, (applicants, result_dict, 'extra_curricular_activities')),
        (create_fake_assignment_submissions, (assignments, students, result_dict, 'assignment_submissions')),
        (create_fake_notices, (teachers, result_dict, 'notices')),
        (create_fake_exam_results, (offerings, students, teachers, result_dict, 'exam_results')),
        (create_fake_attendance, (offerings, students, teachers, result_dict, 'attendance')),
        (create_fake_course_enrollments, (semester_enrollments, offerings, result_dict, 'course_enrollments')),
    ]

    with Pool(processes=8, initializer=worker_init) as pool:
        pool.starmap(execute_task, final_tasks)

    academic_qualifications = result_dict.get('academic_qualifications', [])
    extra_curricular_activities = result_dict.get('extra_curricular_activities', [])
    assignment_submissions = result_dict.get('assignment_submissions', [])
    notices = result_dict.get('notices', [])
    exam_results = result_dict.get('exam_results', [])
    attendance = result_dict.get('attendance', [])
    course_enrollments = result_dict.get('course_enrollments', [])

    print(f"Total users: {len(users)}")
    print(f"Total faculties: {len(faculties)}")
    print(f"Total departments: {len(departments)}")
    print(f"Total programs: {len(programs)}")
    print(f"Total academic sessions: {len(sessions)}")
    print(f"Total semesters: {len(semesters)}")
    print(f"Total admission cycles: {len(admission_cycles)}")
    print(f"Total applicants: {len(applicants)}")
    print(f"Total academic qualifications: {len(academic_qualifications)}")
    print(f"Total extra-curricular activities: {len(extra_curricular_activities)}")
    print(f"Total teachers: {len(teachers)}")
    print(f"Total courses: {len(courses)}")
    print(f"Total venues: {len(venues)}")
    print(f"Total course offerings: {len(offerings)}")
    print(f"Total timetable slots: {len(timetable_slots)}")
    print(f"Total study materials: {len(study_materials)}")
    # print(f"Total assignments: {len(assignments)}")
    print(f"Total students: {len(students)}")
    # print(f"Total assignment submissions: {len(assignment_submissions)}")
    print(f"Total notices: {len(notices)}")   
    print(f"Total exam results: {len(exam_results)}")
    print(f"Total attendance records: {len(attendance)}")
    print(f"Total semester enrollments: {len(semester_enrollments)}")
    print(f"Total course enrollments: {len(course_enrollments)}")
    print("Fake data creation completed!")

if __name__ == "__main__":
    main()
