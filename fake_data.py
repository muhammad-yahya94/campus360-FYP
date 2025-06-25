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
from django.db import connections, transaction
import logging

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from academics.models import Faculty, Department, Program, Semester
    from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
    from courses.models import Course, CourseOffering, Venue, TimetableSlot, StudyMaterial, Assignment, AssignmentSubmission, Notice, ExamResult, Attendance
    from faculty_staff.models import Teacher, TeacherDetails
    from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
    from users.models import CustomUser
    from django.core.exceptions import ValidationError
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        logger.error(f"Error creating fake image: {e}")
        return None

def worker_init():
    """Initialize Django in each process."""
    try:
        django.setup()
        connections.close_all()
    except Exception as e:
        logger.error(f"Error initializing worker: {e}")

def threaded_create(model, objects_queue, lock, model_name):
    """Thread worker to save objects to the database."""
    while True:
        try:
            obj_data = objects_queue.get_nowait()
            with lock:
                with transaction.atomic():
                    model.objects.create(**obj_data)
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Error creating {model_name}: {e}")

def create_fake_users(count=600, result_dict=None, key=None):
    worker_init()
    existing_users = CustomUser.objects.count()
    if existing_users >= count:
        logger.info(f"Skipping user creation: {existing_users} users already exist")
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
            attempts = 0
            while email in existing_emails and attempts < 10:
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@example.com"
                attempts += 1
            if attempts >= 10:
                logger.warning(f"Could not generate unique email for {first_name} {last_name}")
                continue
            existing_emails.add(email)
            objects_queue.put({
                'email': email,
                'password': CustomUser.objects.make_random_password(),
                'first_name': first_name,
                'last_name': last_name,
                'info': fake.text(max_nb_chars=200),
                'is_active': True,
                'date_joined': timezone.now(),
                'last_login': timezone.now(),
            })
        except Exception as e:
            logger.error(f"Error queuing user {first_name} {last_name}: {e}")
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
        logger.error(f"Error in user creation threads: {e}")

    try:
        users = list(CustomUser.objects.all())
        logger.info(f"Created {len(users) - existing_users} new users")
        if result_dict is not None and key is not None:
            result_dict[key] = users
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        users = []
    return users

def create_fake_faculties(result_dict=None, key=None):
    worker_init()
    existing_faculties = Faculty.objects.count()
    if existing_faculties >= len(university_faculties):
        logger.info(f"Skipping faculty creation: {existing_faculties} faculties already exist")
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
                logger.error(f"Error queuing faculty {name}: {e}")
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
        logger.error(f"Error in faculty creation threads: {e}")

    try:
        faculties = list(Faculty.objects.all())
        logger.info(f"Created {len(faculties) - existing_faculties} new faculties")
        if result_dict is not None and key is not None:
            result_dict[key] = faculties
    except Exception as e:
        logger.error(f"Error retrieving faculties: {e}")
        faculties = []
    return faculties

def create_fake_departments(faculties, result_dict=None, key=None):
    worker_init()
    existing_departments = Department.objects.count()
    expected_departments = sum(len(depts) for depts in university_departments.values())
    if existing_departments >= expected_departments:
        logger.info(f"Skipping department creation: {existing_departments} departments already exist")
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
                        'introduction': fake.text(max_nb_chars=200),
                        'image': create_fake_image() if random.choice([True, False]) else None,
                        'details': fake.text(max_nb_chars=500) if random.choice([True, False]) else None
                    })
                except Exception as e:
                    logger.error(f"Error queuing department {name}: {e}")
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
        logger.error(f"Error in department creation threads: {e}")

    try:
        departments = list(Department.objects.all())
        logger.info(f"Created {len(departments) - existing_departments} new departments")
        if result_dict is not None and key is not None:
            result_dict[key] = departments
    except Exception as e:
        logger.error(f"Error retrieving departments: {e}")
        departments = []
    return departments

def create_fake_programs(departments, result_dict=None, key=None):
    worker_init()
    existing_programs = Program.objects.count()
    expected_programs = sum(len(progs) for progs in university_programs.values())
    if existing_programs >= expected_programs:
        logger.info(f"Skipping program creation: {existing_programs} programs already exist")
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
                    total_semesters = 8 if degree_type == 'BS' else 4
                    objects_queue.put({
                        'department': department,
                        'name': name,
                        'degree_type': degree_type,
                        'duration_years': duration_years,
                        'total_semesters': total_semesters,
                        'start_year': 2020,
                        'is_active': True,
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    })
                except Exception as e:
                    logger.error(f"Error queuing program {name}: {e}")
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
        logger.error(f"Error in program creation threads: {e}")

    try:
        programs = list(Program.objects.all())
        logger.info(f"Created {len(programs) - existing_programs} new programs")
        if result_dict is not None and key is not None:
            result_dict[key] = programs
    except Exception as e:
        logger.error(f"Error retrieving programs: {e}")
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
        logger.info(f"Skipping session creation: {existing_sessions} sessions already exist")
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
                    'description': fake.text(max_nb_chars=300),
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                })
            except Exception as e:
                logger.error(f"Error queuing session {name}: {e}")
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
        logger.error(f"Error in session creation threads: {e}")

    try:
        sessions = list(AcademicSession.objects.all())
        logger.info(f"Created {len(sessions) - existing_sessions} new sessions")
        if result_dict is not None and key is not None:
            result_dict[key] = sessions
    except Exception as e:
        logger.error(f"Error retrieving sessions: {e}")
        sessions = []
    return sessions

def create_fake_semesters(programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_semesters = Semester.objects.count()
    session_data = {
        '2021-2025': 8, '2022-2026': 8, '2023-2027': 8, '2024-2028': 8,
        '2023-2025': 4, '2024-2026': 4
    }
    expected_semesters = sum(session_data.get(s.name, 4) for s in sessions for p in programs)
    if existing_semesters >= expected_semesters:
        logger.info(f"Skipping semester creation: {existing_semesters} semesters already exist")
        result = list(Semester.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    semesters = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for program in programs:
        available_sessions = [s for s in sessions if (
            (program.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
            (program.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
        )]
        for session in available_sessions:
            semester_count = session_data.get(session.name, 4)
            session_start_year = int(session.name.split('-')[0])
            for i in range(1, semester_count + 1):
                if not Semester.objects.filter(program=program, session=session, number=i).exists():
                    try:
                        months_offset = (i - 1) * 6
                        semester_start = date(session_start_year, 1, 1) + timedelta(days=int(months_offset * 30.42))
                        semester_end = semester_start + timedelta(days=180)
                        objects_queue.put({
                            'program': program,
                            'session': session,
                            'number': i,
                            'name': f"Semester {i}",
                            'start_time': semester_start,
                            'end_time': semester_end,
                            'is_active': (i == 1 and session.is_active),
                            'description': fake.text(max_nb_chars=200)
                        })
                    except Exception as e:
                        logger.error(f"Error queuing semester {i} for {program.name} in {session.name}: {e}")
                        continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Semester, objects_queue, lock, 'semester'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in semester creation threads: {e}")

    try:
        semesters = list(Semester.objects.all())
        logger.info(f"Created {len(semesters) - existing_semesters} new semesters")
        if result_dict is not None and key is not None:
            result_dict[key] = semesters
    except Exception as e:
        logger.error(f"Error retrieving semesters: {e}")
        semesters = []
    return semesters

def create_fake_admission_cycles(programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_cycles = AdmissionCycle.objects.count()
    expected_cycles = sum(len([s for s in sessions if (
        (p.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
        (p.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
    )]) for p in programs)
    if existing_cycles >= expected_cycles:
        logger.info(f"Skipping admission cycle creation: {existing_cycles} admission cycles already exist")
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
                        start_year = int(session.name.split('-')[0])
                        application_start = date(start_year, 1, 1)
                        application_end = application_start + timedelta(days=30)
                        objects_queue.put({
                            'program': program,
                            'session': session,
                            'application_start': application_start,
                            'application_end': application_end,
                            'is_open': session.is_active
                        })
                    except Exception as e:
                        logger.error(f"Error queuing admission cycle for {program.name} in {session.name}: {e}")
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
        logger.error(f"Error in admission cycle creation threads: {e}")

    try:
        admission_cycles = list(AdmissionCycle.objects.all())
        logger.info(f"Created {len(admission_cycles) - existing_cycles} new admission cycles")
        if result_dict is not None and key is not None:
            result_dict[key] = admission_cycles
    except Exception as e:
        logger.error(f"Error retrieving admission cycles: {e}")
        admission_cycles = []
    return admission_cycles

def create_fake_applicants(users, faculties, departments, programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_applicants = Applicant.objects.count()
    expected_applicants = min(260, sum(50 if p.degree_type == 'BS' else 20 for p in programs))
    if existing_applicants >= expected_applicants:
        logger.info(f"Skipping applicant creation: {existing_applicants} applicants already exist")
        result = list(Applicant.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    applicants = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists() and not Teacher.objects.filter(user=u).exists()]
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
                logger.warning(f"No available users for applicants for program {program.name}")
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
                max_attempts = 10
                while Applicant.objects.filter(cnic=cnic).exists() and attempts < max_attempts:
                    cnic = f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}"
                    attempts += 1
                if attempts >= max_attempts:
                    logger.warning(f"Could not generate unique CNIC for {full_name}")
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
                    'father_cnic': f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}",
                    'monthly_income': random.randint(20000, 100000),
                    'relationship': 'father',
                    'permanent_address': fake.address().replace('\n', ', '),
                    'shift': program_shifts[i % len(program_shifts)],
                    'declaration': True,
                    'applicant_photo': create_fake_image() if random.choice([True, False]) else None,
                    'created_at': timezone.now()
                })
                available_users.remove(user)
            except Exception as e:
                logger.error(f"Error queuing applicant for {program.name}: {e}")
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
        logger.error(f"Error in applicant creation threads: {e}")

    try:
        applicants = list(Applicant.objects.all())
        logger.info(f"Created {len(applicants) - existing_applicants} new applicants")
        if result_dict is not None and key is not None:
            result_dict[key] = applicants
    except Exception as e:
        logger.error(f"Error retrieving applicants: {e}")
        applicants = []
    return applicants

def create_fake_academic_qualifications(applicants, result_dict=None, key=None):
    worker_init()
    existing_qualifications = AcademicQualification.objects.count()
    expected_qualifications = sum(random.randint(2, 3) for _ in applicants)
    if existing_qualifications >= expected_qualifications:
        logger.info(f"Skipping academic qualification creation: {existing_qualifications} qualifications already exist")
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
                    'passing_year': random.randint(2015, 2023),
                    'marks_obtained': marks_obtained,
                    'total_marks': total_marks,
                    'division': random.choice(['1st Division', '2nd Division', 'A+', 'A']),
                    'subjects': random.choice(subjects),
                    'board': random.choice(boards),
                    'certificate_file': create_fake_image() if random.choice([True, False]) else None
                })
            except Exception as e:
                logger.error(f"Error queuing academic qualification for {applicant.full_name}: {e}")
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
        logger.error(f"Error in academic qualification creation threads: {e}")

    try:
        qualifications = list(AcademicQualification.objects.all())
        logger.info(f"Created {len(qualifications) - existing_qualifications} new academic qualifications")
        if result_dict is not None and key is not None:
            result_dict[key] = qualifications
    except Exception as e:
        logger.error(f"Error retrieving academic qualifications: {e}")
        qualifications = []
    return qualifications

def create_fake_extra_curricular_activities(applicants, result_dict=None, key=None):
    worker_init()
    existing_activities = ExtraCurricularActivity.objects.count()
    expected_activities = sum(random.randint(1, 2) for _ in applicants)
    if existing_activities >= expected_activities:
        logger.info(f"Skipping extra-curricular activity creation: {existing_activities} activities already exist")
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
                    'activity_year': random.randint(2015, 2023),
                    'certificate_file': create_fake_image() if random.choice([True, False]) else None
                })
            except Exception as e:
                logger.error(f"Error queuing extra-curricular activity for {applicant.full_name}: {e}")
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
        logger.error(f"Error in extra-curricular activity creation threads: {e}")

    try:
        activities_list = list(ExtraCurricularActivity.objects.all())
        logger.info(f"Created {len(activities_list) - existing_activities} new extra-curricular activities")
        if result_dict is not None and key is not None:
            result_dict[key] = activities_list
    except Exception as e:
        logger.error(f"Error retrieving extra-curricular activities: {e}")
        activities_list = []
    return activities_list

def create_fake_teachers(users, departments, result_dict=None, key=None):
    worker_init()
    existing_teachers = Teacher.objects.count()
    expected_teachers = len(departments) * 25
    if existing_teachers >= expected_teachers:
        logger.info(f"Skipping teacher creation: {existing_teachers} teachers already exist")
        result = list(Teacher.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    teachers = []
    available_users = [u for u in users if not Applicant.objects.filter(user=u).exists() and not Teacher.objects.filter(user=u).exists()]
    designations = ['professor'] * 10 + ['associate_professor'] * 8 + ['assistant_professor'] * 6 + ['head_of_department'] * 1
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for department in departments:
        existing_count = Teacher.objects.filter(department=department).count()
        needed = 25 - existing_count
        dept_designations = designations.copy()
        random.shuffle(dept_designations)
        head_assigned = Teacher.objects.filter(department=department, designation='head_of_department').exists()
        for _ in range(max(0, needed)):
            if not available_users:
                logger.warning(f"Not enough users for teachers in {department.name}, created {25 - needed} teachers")
                break
            try:
                user = random.choice(available_users)
                designation = dept_designations.pop()
                if designation == 'head_of_department' and head_assigned:
                    designation = random.choice(['professor', 'associate_professor', 'assistant_professor'])
                if designation == 'head_of_department':
                    head_assigned = True
                objects_queue.put({
                    'user': user,
                    'department': department,
                    'designation': designation,
                    'contact_no': f"0{random.randint(3000000000,9999999999):010d}",
                    'qualification': fake.job(),
                    'hire_date': fake.date_between(start_date='-10y', end_date='today'),
                    'is_active': True,
                    'linkedin_url': f"https://linkedin.com/in/{fake.user_name()}" if random.choice([True, False]) else None,
                    'twitter_url': f"https://twitter.com/{fake.user_name()}" if random.choice([True, False]) else None,
                    'personal_website': f"https://{fake.domain_name()}" if random.choice([True, False]) else None,
                    'experience': fake.text(max_nb_chars=300)
                })
                available_users.remove(user)
            except Exception as e:
                logger.error(f"Error queuing teacher for {department.name}: {e}")
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
        logger.error(f"Error in teacher creation threads: {e}")

    try:
        teachers = list(Teacher.objects.all())
        logger.info(f"Created {len(teachers) - existing_teachers} new teachers")
        if result_dict is not None and key is not None:
            result_dict[key] = teachers
    except Exception as e:
        logger.error(f"Error retrieving teachers: {e}")
        teachers = []
    return teachers

def create_fake_teacher_details(teachers, result_dict=None, key=None):
    worker_init()
    existing_details = TeacherDetails.objects.count()
    expected_details = len(teachers)
    if existing_details >= expected_details:
        logger.info(f"Skipping teacher details creation: {existing_details} teacher details already exist")
        result = list(TeacherDetails.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    details = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for teacher in teachers:
        if not TeacherDetails.objects.filter(teacher=teacher).exists():
            try:
                employment_types = ['visitor', 'contract', 'permanent']
                statuses = ['on_break', 'on_lecture', 'on_leave', 'available']
                objects_queue.put({
                    'teacher': teacher,
                    'employment_type': random.choice(employment_types),
                    'salary_per_lecture': random.uniform(1000, 5000) if random.choice([True, False]) else None,
                    'fixed_salary': random.uniform(50000, 200000) if random.choice([True, False]) else None,
                    'status': random.choice(statuses),
                    'last_updated': timezone.now()
                })
            except Exception as e:
                logger.error(f"Error queuing teacher details for {teacher.user.first_name}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(TeacherDetails, objects_queue, lock, 'teacher details'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in teacher details creation threads: {e}")

    try:
        details = list(TeacherDetails.objects.all())
        logger.info(f"Created {len(details) - existing_details} new teacher details")
        if result_dict is not None and key is not None:
            result_dict[key] = details
    except Exception as e:
        logger.error(f"Error retrieving teacher details: {e}")
        details = []
    return details

def create_fake_courses(result_dict=None, key=None):
    worker_init()
    existing_courses = Course.objects.count()
    if existing_courses >= len(course_data):
        logger.info(f"Skipping course creation: {existing_courses} courses already exist")
        result = list(Course.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    courses = []
    existing_codes = set(Course.objects.values_list('code', flat=True))
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for code, name in course_data:
        if code not in existing_codes:
            try:
                objects_queue.put({
                    'code': code,
                    'name': name,
                    'credits': random.randint(2, 4),
                    'lab_work': random.randint(0, 2) if code.startswith('CS') or code.startswith('EE') else 0,
                    'is_active': True,
                    'description': fake.text(max_nb_chars=300)
                })
            except Exception as e:
                logger.error(f"Error queuing course {code}: {e}")
                continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Course, objects_queue, lock, 'course'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in course creation threads: {e}")

    try:
        courses = list(Course.objects.all())
        logger.info(f"Created {len(courses) - existing_courses} new courses")
        if result_dict is not None and key is not None:
            result_dict[key] = courses
    except Exception as e:
        logger.error(f"Error retrieving courses: {e}")
        courses = []
    return courses

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
        logger.info(f"Skipping venue creation: {existing_venues} venues already exist")
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
                    logger.error(f"Error queuing venue {full_name}: {e}")
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
        logger.error(f"Error in venue creation threads: {e}")

    try:
        venues_list = list(Venue.objects.all())
        logger.info(f"Created {len(venues_list) - existing_venues} new venues")
        if result_dict is not None and key is not None:
            result_dict[key] = venues_list
    except Exception as e:
        logger.error(f"Error retrieving venues: {e}")
        venues_list = []
    return venues_list

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, result_dict=None, key=None):
    worker_init()
    existing_offerings = CourseOffering.objects.count()
    expected_offerings = len(courses) * len(semesters) // 2
    if existing_offerings >= expected_offerings:
        logger.info(f"Skipping course offering creation: {existing_offerings} offerings already exist")
        result = list(CourseOffering.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    offerings = []
    if not teachers:
        logger.error("No teachers available for course offerings")
        if result_dict is not None and key is not None:
            result_dict[key] = []
        return []
    offering_types = ['core', 'elective', 'major', 'minor', 'foundation', 'gen_ed', 'lab', 'seminar', 'capstone']
    shifts = ['morning', 'evening', 'both']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for program in programs:
        program_semesters = [s for s in semesters if s.program == program]
        relevant_courses = [c for c in courses if c.code.startswith(program.department.name[:2].upper())]
        if not relevant_courses:
            relevant_courses = [c for c in courses if c.code.startswith('CS')]
        for semester in program_semesters:
            selected_courses = random.sample(relevant_courses, min(len(relevant_courses), 5))
            for course in selected_courses:
                if not CourseOffering.objects.filter(course=course, semester=semester).exists():
                    try:
                        teacher = random.choice([t for t in teachers if t.department == program.department])
                        objects_queue.put({
                            'course': course,
                            'teacher': teacher,
                            'department': program.department,
                            'program': program,
                            'academic_session': semester.session,
                            'semester': semester,
                            'is_active': semester.is_active,
                            'current_enrollment': random.randint(10, 50),
                            'offering_type': random.choice(offering_types),
                            'shift': random.choice(shifts)
                        })
                    except Exception as e:
                        logger.error(f"Error queuing course offering for {course.code} in {semester.name}: {e}")
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
        logger.error(f"Error in course offering creation threads: {e}")

    try:
        offerings = list(CourseOffering.objects.all())
        logger.info(f"Created {len(offerings) - existing_offerings} new course offerings")
        if result_dict is not None and key is not None:
            result_dict[key] = offerings
    except Exception as e:
        logger.error(f"Error retrieving course offerings: {e}")
        offerings = []
    return offerings

def create_fake_timetable_slots(offerings, venues, teachers, result_dict=None, key=None):
    worker_init()
    existing_slots = TimetableSlot.objects.count()
    expected_slots = len(offerings) * 2  # Two slots per offering
    if existing_slots >= expected_slots:
        logger.info(f"Skipping timetable slot creation: {existing_slots} slots already exist")
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
        needed = 2 - existing_count
        available_days = days.copy()
        random.shuffle(available_days)
        available_venues = [v for v in venues if v.department == offering.department]
        random.shuffle(available_venues)
        available_teachers = [t for t in teachers if t.department == offering.department]
        random.shuffle(available_teachers)
        slot_count = 0
        retries = 0
        while slot_count < needed and available_days and retries < max_retries:
            day = available_days.pop(0)
            day_slots = [(start, end) for start, end in time_slots]
            random.shuffle(day_slots)
            for start_time, end_time in day_slots:
                for venue in available_venues:
                    if slot_count >= needed:
                        break
                    try:
                        teacher = offering.teacher
                        if TimetableSlot.objects.filter(
                            course_offering__academic_session=offering.academic_session,
                            day=day,
                            venue=venue,
                            start_time__lt=end_time,
                            end_time__gt=start_time
                        ).exists():
                            continue
                        if TimetableSlot.objects.filter(
                            course_offering__teacher=teacher,
                            course_offering__academic_session=offering.academic_session,
                            day=day,
                            start_time__lt=end_time,
                            end_time__gt=start_time
                        ).exists():
                            continue
                        objects_queue.put({
                            'course_offering': offering,
                            'day': day,
                            'start_time': start_time,
                            'end_time': end_time,
                            'venue': venue
                        })
                        slot_count += 1
                        break
                    except Exception as e:
                        logger.error(f"Error queuing timetable slot for {offering.course.code}: {e}")
                        retries += 1
                        continue
                if slot_count >= needed:
                    break
            if slot_count < needed:
                retries += 1
        if slot_count < needed:
            logger.warning(f"Could only create {slot_count} of {needed} timetable slots for {offering.course.code}")

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(TimetableSlot, objects_queue, lock, 'timetable slot'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in timetable slot creation threads: {e}")

    try:
        slots = list(TimetableSlot.objects.all())
        logger.info(f"Created {len(slots) - existing_slots} new timetable slots")
        if result_dict is not None and key is not None:
            result_dict[key] = slots
    except Exception as e:
        logger.error(f"Error retrieving timetable slots: {e}")
        slots = []
    return slots

def create_fake_study_materials(offerings, teachers, result_dict=None, key=None):
    worker_init()
    existing_materials = StudyMaterial.objects.count()
    expected_materials = len(offerings) * 10
    if existing_materials >= expected_materials:
        logger.info(f"Skipping study material creation: {existing_materials} materials already exist")
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
                    'topic': fake.sentence(nb_words=4),
                    'title': f"Material {i+1} for {offering.course.name}",
                    'description': fake.text(max_nb_chars=200),
                    'useful_links': '\n'.join([fake.url() for _ in range(random.randint(0, 3))]),
                    'video_link': fake.url() if random.choice([True, False]) else None,
                    'image': create_fake_image() if random.choice([True, False]) else None,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                })
            except Exception as e:
                logger.error(f"Error queuing study material for {offering.course.code}: {e}")
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
        logger.error(f"Error in study material creation threads: {e}")

    try:
        materials = list(StudyMaterial.objects.all())
        logger.info(f"Created {len(materials) - existing_materials} new study materials")
        if result_dict is not None and key is not None:
            result_dict[key] = materials
    except Exception as e:
        logger.error(f"Error retrieving study materials: {e}")
        materials = []
    return materials

def create_fake_assignments(offerings, teachers, result_dict=None, key=None):
    worker_init()
    existing_assignments = Assignment.objects.count()
    expected_assignments = len(offerings) * 5
    if existing_assignments >= expected_assignments:
        logger.info(f"Skipping assignment creation: {existing_assignments} assignments already exist")
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
        semester_start = offering.semester.start_time
        semester_end = offering.semester.end_time
        for i in range(max(0, needed)):
            try:
                due_date = fake.date_between(start_date=semester_start, end_date=semester_end)
                due_date = timezone.make_aware(datetime.combine(due_date, time(23, 59)))
                objects_queue.put({
                    'course_offering': offering,
                    'teacher': offering.teacher,
                    'title': f"Assignment {i+1} for {offering.course.name}",
                    'description': fake.text(max_nb_chars=200),
                    'due_date': due_date,
                    'max_points': random.choice([50, 100, 200]),
                    'resource_file': create_fake_image() if random.choice([True, False]) else None,
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                })
            except Exception as e:
                logger.error(f"Error queuing assignment for {offering.course.code}: {e}")
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
        logger.error(f"Error in assignment creation threads: {e}")

    try:
        assignments = list(Assignment.objects.all())
        logger.info(f"Created {len(assignments) - existing_assignments} new assignments")
        if result_dict is not None and key is not None:
            result_dict[key] = assignments
    except Exception as e:
        logger.error(f"Error retrieving assignments: {e}")
        assignments = []
    return assignments

def create_fake_assignment_submissions(assignments, students, result_dict=None, key=None):
    worker_init()
    existing_submissions = AssignmentSubmission.objects.count()
    expected_submissions = sum(min(10, len([s for s in students if CourseEnrollment.objects.filter(
        student_semester_enrollment__student=s, course_offering=a.course_offering).exists()])) for a in assignments)
    if existing_submissions >= expected_submissions:
        logger.info(f"Skipping assignment submission creation: {existing_submissions} submissions already exist")
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
            existing_students = set(AssignmentSubmission.objects.filter(assignment=assignment).values_list('student__id', flat=True))
            available_students = [s for s in relevant_students if s.id not in existing_students]
            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                try:
                    semester_start = assignment.course_offering.semester.start_time
                    submit_date = fake.date_between(start_date=semester_start, end_date=assignment.due_date)
                    submitted_at = timezone.make_aware(datetime.combine(submit_date, time(random.randint(0, 23), random.randint(0, 59))))
                    objects_queue.put({
                        'assignment': assignment,
                        'student': student,
                        'file': create_fake_image() if random.choice([True, False]) else None,
                        'submitted_at': submitted_at,
                        'marks_obtained': random.randint(0, assignment.max_points) if random.choice([True, False]) else None,
                        'feedback': fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None,
                        'graded_by': assignment.teacher if random.choice([True, False]) else None,
                        'graded_at': timezone.now() if random.choice([True, False]) else None
                    })
                except Exception as e:
                    logger.error(f"Error queuing submission for {student.applicant.full_name} on {assignment.title}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error processing submissions for {assignment.title}: {e}")
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
        logger.error(f"Error in assignment submission creation threads: {e}")

    try:
        submissions = list(AssignmentSubmission.objects.all())
        logger.info(f"Created {len(submissions) - existing_submissions} new assignment submissions")
        if result_dict is not None and key is not None:
            result_dict[key] = submissions
    except Exception as e:
        logger.error(f"Error retrieving submissions: {e}")
        submissions = []
    return submissions

def create_fake_notices(teachers, result_dict=None, key=None):
    worker_init()
    existing_notices = Notice.objects.count()
    expected_notices = sum(random.randint(2, 4) for _ in teachers)
    if existing_notices >= expected_notices:
        logger.info(f"Skipping notice creation: {existing_notices} notices already exist")
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
                    'is_active': random.choice([True, False]),
                    'created_at': timezone.now()
                })
            except Exception as e:
                logger.error(f"Error queuing notice for {teacher.user.first_name}: {e}")
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
        logger.error(f"Error in notice creation threads: {e}")

    try:
        notices = list(Notice.objects.all())
        logger.info(f"Created {len(notices) - existing_notices} new notices")
        if result_dict is not None and key is not None:
            result_dict[key] = notices
    except Exception as e:
        logger.error(f"Error retrieving notices: {e}")
        notices = []
    return notices

def create_fake_exam_results(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_results = ExamResult.objects.count()
    expected_results = sum(min(10, len([s for s in students if CourseEnrollment.objects.filter(
        student_semester_enrollment__student=s, course_offering=o).exists()])) * 2 for o in offerings)
    if existing_results >= expected_results:
        logger.info(f"Skipping exam result creation: {existing_results} results already exist")
        result = list(ExamResult.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    results = []
    exam_types = ['midterm', 'final']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=offering).exists()]
            existing_students = set(ExamResult.objects.filter(course_offering=offering).values_list('student__id', flat=True))
            available_students = [s for s in relevant_students if s.id not in existing_students]
            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                for exam_type in exam_types:
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
                                'graded_at': timezone.now(),
                                'remarks': fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None
                            })
                        except Exception as e:
                            logger.error(f"Error queuing exam result for {student.applicant.full_name} in {offering.course.code}: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error processing exam results for {offering.course.code}: {e}")
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
        logger.error(f"Error in exam result creation threads: {e}")

    try:
        results = list(ExamResult.objects.all())
        logger.info(f"Created {len(results) - existing_results} new exam results")
        if result_dict is not None and key is not None:
            result_dict[key] = results
    except Exception as e:
        logger.error(f"Error retrieving exam results: {e}")
        results = []
    return results

def create_fake_attendance(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_attendance = Attendance.objects.count()
    expected_attendance = sum(20 * len([s for s in students if CourseEnrollment.objects.filter(
        student_semester_enrollment__student=s, course_offering=o).exists()]) for o in offerings)
    if existing_attendance >= expected_attendance:
        logger.info(f"Skipping attendance creation: {existing_attendance} attendance records already exist")
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
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=offering).exists()]
            timetable_slots = TimetableSlot.objects.filter(course_offering=offering)
            semester_start = offering.semester.start_time
            semester_end = offering.semester.end_time
            for student in relevant_students:
                existing_count = Attendance.objects.filter(student=student, course_offering=offering).count()
                needed = 20 - existing_count
                available_dates = []
                for slot in timetable_slots:
                    current_date = semester_start
                    while current_date <= semester_end:
                        if slot.day.lower() == current_date.strftime('%A').lower():
                            available_dates.append(current_date)
                        current_date += timedelta(days=1)
                available_dates = random.sample(available_dates, min(needed, len(available_dates)))
                for date in available_dates:
                    try:
                        if not Attendance.objects.filter(
                            student=student,
                            course_offering=offering,
                            date=date,
                            shift=offering.shift
                        ).exists():
                            objects_queue.put({
                                'student': student,
                                'course_offering': offering,
                                'date': date,
                                'status': random.choice(status_choices),
                                'shift': offering.shift,
                                'recorded_by': offering.teacher,
                                'recorded_at': timezone.make_aware(datetime.combine(date, time(random.randint(0, 23), random.randint(0, 59))))
                            })
                    except Exception as e:
                        logger.error(f"Error queuing attendance for {student.applicant.full_name} in {offering.course.code}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error processing attendance for {offering.course.code}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Attendance, objects_queue, lock, 'attendance record'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in attendance creation threads: {e}")

    try:
        attendance_records = list(Attendance.objects.all())
        logger.info(f"Created {len(attendance_records) - existing_attendance} new attendance records")
        if result_dict is not None and key is not None:
            result_dict[key] = attendance_records
    except Exception as e:
        logger.error(f"Error retrieving attendance records: {e}")
        attendance_records = []
    return attendance_records

def create_fake_students(applicants, programs, result_dict=None, key=None):
    worker_init()
    existing_students = Student.objects.count()
    expected_students = len([a for a in applicants if a.status == 'accepted'])
    if existing_students >= expected_students:
        logger.info(f"Skipping student creation: {existing_students} students already exist")
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
                start_date = date(applicant.session.start_year, 1, 1)
                end_date = min(timezone.now().date(), date(applicant.session.start_year + 1, 1, 1))
                enrollment_date = fake.date_between(start_date=start_date, end_date=end_date)
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
                logger.error(f"Error queuing student for {applicant.full_name}: {e}")
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
        logger.error(f"Error in student creation threads: {e}")

    try:
        students = list(Student.objects.all())
        logger.info(f"Created {len(students) - existing_students} new students")
        if result_dict is not None and key is not None:
            result_dict[key] = students
    except Exception as e:
        logger.error(f"Error retrieving students: {e}")
        students
        
def create_fake_student_semester_enrollments(students, semesters, result_dict=None, key=None):
    worker_init()
    existing_enrollments = StudentSemesterEnrollment.objects.count()
    expected_enrollments = len(students) * 2  # Assume each student is enrolled in at least 2 semesters
    if existing_enrollments >= expected_enrollments:
        logger.info(f"Skipping student semester enrollment creation: {existing_enrollments} enrollments already exist")
        result = list(StudentSemesterEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for student in students:
        try:
            program_semesters = [s for s in semesters if s.program == student.program and s.session == student.applicant.session]
            if not program_semesters:
                logger.warning(f"No valid semesters found for student {student.applicant.full_name} in program {student.program.name}")
                continue
            existing_semesters = set(StudentSemesterEnrollment.objects.filter(student=student).values_list('semester__id', flat=True))
            available_semesters = [s for s in program_semesters if s.id not in existing_semesters]
            selected_semesters = random.sample(available_semesters, min(2, len(available_semesters)))
            for semester in selected_semesters:
                try:
                    enrollment_date = fake.date_between(start_date=semester.start_time, end_date=min(timezone.now().date(), semester.end_time))
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
                    logger.error(f"Error queuing semester enrollment for {student.applicant.full_name} in {semester.name}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error processing semester enrollments for {student.applicant.full_name}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(StudentSemesterEnrollment, objects_queue, lock, 'student semester enrollment'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        logger.error(f"Error in student semester enrollment creation threads: {e}")

    try:
        enrollments = list(StudentSemesterEnrollment.objects.all())
        logger.info(f"Created {len(enrollments) - existing_enrollments} new student semester enrollments")
        if result_dict is not None and key is not None:
            result_dict[key] = enrollments
    except Exception as e:
        logger.error(f"Error retrieving student semester enrollments: {e}")
        enrollments = []
    return enrollments

def create_fake_course_enrollments(student_semester_enrollments, course_offerings, result_dict=None, key=None):
    worker_init()
    existing_enrollments = CourseEnrollment.objects.count()
    expected_enrollments = len(student_semester_enrollments) * 4  # Assume 4 courses per student per semester
    if existing_enrollments >= expected_enrollments:
        logger.info(f"Skipping course enrollment creation: {existing_enrollments} enrollments already exist")
        result = list(CourseEnrollment.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    enrollments = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for sse in student_semester_enrollments:
        try:
            relevant_offerings = [co for co in course_offerings if co.semester == sse.semester and co.program == sse.student.program]
            if not relevant_offerings:
                logger.warning(f"No course offerings found for {sse.student.applicant.full_name} in {sse.semester.name}")
                continue
            existing_offerings = set(CourseEnrollment.objects.filter(student_semester_enrollment=sse).values_list('course_offering__id', flat=True))
            available_offerings = [co for co in relevant_offerings if co.id not in existing_offerings]
            selected_offerings = random.sample(available_offerings, min(4, len(available_offerings)))
            for offering in selected_offerings:
                try:
                    enrollment_date = fake.date_between(start_date=sse.semester.start_time, end_date=min(timezone.now().date(), sse.semester.end_time))
                    enrollment_date = timezone.make_aware(datetime.combine(enrollment_date, time(random.randint(0, 23), random.randint(0, 59))))
                    objects_queue.put({
                        'student_semester_enrollment': sse,
                        'course_offering': offering,
                        'enrollment_date': enrollment_date,
                        'status': 'enrolled',
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    })
                except Exception as e:
                    logger.error(f"Error queuing course enrollment for {sse.student.applicant.full_name} in {offering.course.code}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error processing course enrollments for {sse.student.applicant.full_name}: {e}")
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
        logger.error(f"Error in course enrollment creation threads: {e}")

    try:
        enrollments = list(CourseEnrollment.objects.all())
        logger.info(f"Created {len(enrollments) - existing_enrollments} new course enrollments")
        if result_dict is not None and key is not None:
            result_dict[key] = enrollments
    except Exception as e:
        logger.error(f"Error retrieving course enrollments: {e}")
        enrollments = []
    return enrollments

def execute_task(func, args):
    """Helper function to execute a task with given arguments."""
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"Error executing task {func.__name__}: {e}")
        return None

def main():
    logger.info("Starting fake data generation")
    manager = Manager()
    result_dict = manager.dict()

    # Define tasks for parallel execution
    tasks = [
        (create_fake_users, (600, result_dict, 'users')),
        (create_fake_faculties, (result_dict, 'faculties')),
        (create_fake_departments, (result_dict.get('faculties', []), result_dict, 'departments')),
        (create_fake_programs, (result_dict.get('departments', []), result_dict, 'programs')),
        (create_fake_academic_sessions, (result_dict, 'sessions')),
        (create_fake_semesters, (result_dict.get('programs', []), result_dict.get('sessions', []), result_dict, 'semesters')),
        (create_fake_admission_cycles, (result_dict.get('programs', []), result_dict.get('sessions', []), result_dict, 'admission_cycles')),
        (create_fake_applicants, (result_dict.get('users', []), result_dict.get('faculties', []), result_dict.get('departments', []), result_dict.get('programs', []), result_dict.get('sessions', []), result_dict, 'applicants')),
        (create_fake_academic_qualifications, (result_dict.get('applicants', []), result_dict, 'qualifications')),
        (create_fake_extra_curricular_activities, (result_dict.get('applicants', []), result_dict, 'activities')),
        (create_fake_teachers, (result_dict.get('users', []), result_dict.get('departments', []), result_dict, 'teachers')),
        (create_fake_teacher_details, (result_dict.get('teachers', []), result_dict, 'teacher_details')),
        (create_fake_courses, (result_dict, 'courses')),
        (create_fake_venues, (result_dict.get('departments', []), result_dict, 'venues')),
        (create_fake_course_offerings, (result_dict.get('courses', []), result_dict.get('teachers', []), result_dict.get('departments', []), result_dict.get('programs', []), result_dict.get('sessions', []), result_dict.get('semesters', []), result_dict, 'course_offerings')),
        (create_fake_timetable_slots, (result_dict.get('course_offerings', []), result_dict.get('venues', []), result_dict.get('teachers', []), result_dict, 'timetable_slots')),
        (create_fake_study_materials, (result_dict.get('course_offerings', []), result_dict.get('teachers', []), result_dict, 'study_materials')),
        (create_fake_assignments, (result_dict.get('course_offerings', []), result_dict.get('teachers', []), result_dict, 'assignments')),
        (create_fake_notices, (result_dict.get('teachers', []), result_dict, 'notices')),
        (create_fake_students, (result_dict.get('applicants', []), result_dict.get('programs', []), result_dict, 'students')),
        (create_fake_student_semester_enrollments, (result_dict.get('students', []), result_dict.get('semesters', []), result_dict, 'student_semester_enrollments')),
        (create_fake_course_enrollments, (result_dict.get('student_semester_enrollments', []), result_dict.get('course_offerings', []), result_dict, 'course_enrollments')),
        (create_fake_assignment_submissions, (result_dict.get('assignments', []), result_dict.get('students', []), result_dict, 'assignment_submissions')),
        (create_fake_exam_results, (result_dict.get('course_offerings', []), result_dict.get('students', []), result_dict.get('teachers', []), result_dict, 'exam_results')),
        (create_fake_attendance, (result_dict.get('course_offerings', []), result_dict.get('students', []), result_dict.get('teachers', []), result_dict, 'attendance'))
    ]

    # Execute tasks in parallel
    with Pool(processes=4, initializer=worker_init) as pool:
        try:
            pool.starmap(execute_task, tasks)
        except Exception as e:
            logger.error(f"Error in parallel task execution: {e}")
        finally:
            pool.close()
            pool.join()

    logger.info("Fake data generation completed")