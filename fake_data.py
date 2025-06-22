import os
import django
import random
import sys
from datetime import timedelta
from faker import Faker
from django.utils import timezone
from django.core.files.base import ContentFile
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from academics.models import Faculty, Department, Program, Semester
    from admissions.models import AcademicSession, AdmissionCycle, Applicant
    from courses.models import Course, CourseOffering
    from faculty_staff.models import Teacher
    from students.models import Student
    from users.models import CustomUser
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
# Expanded course list with 40 courses
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

def create_fake_image():
    from PIL import Image
    import io
    image = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4()}.png")

def create_fake_users(count):
    users = []  
    existing_emails = set(CustomUser.objects.values_list('email', flat=True))
    for _ in range(count):
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
    return users

def create_fake_faculties():
    faculties = []
    for name in university_faculties:
        try:
            faculty = Faculty.objects.create(
                name=name,
                slug=fake.slug(name),
                description=fake.text(max_nb_chars=300)
            )
            faculties.append(faculty)
        except Exception as e:
            print(f"Error creating faculty {name}: {e}")
    return faculties

def create_fake_departments(faculties):
    departments = []
    for faculty in faculties:
        available_depts = university_departments.get(faculty.name, [])
        for name in available_depts:
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
    return departments

def create_fake_programs(departments):
    programs = []
    for department in departments:
        available_programs = university_programs.get(department.name, [])
        for name in available_programs:
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
    return programs

def create_fake_semesters(programs, sessions):
    semesters = []
    semester_counts = {
        'BSCS': 8, 'BSIT': 6, 'BSEE': 4, 'BSMath': 2, 'BSPhysics': 2,
        'MSCS': 4, 'MSIT': 2
    }
    start_date = timezone.now().date()  # 2025-06-22, 05:34 PM PKT

    for program in programs:
        count = semester_counts.get(program.name, 2)  # Default to 2 if not specified
        available_sessions = sessions if program.degree_type == 'BS' else [s for s in sessions if s.name in ['2023-2025', '2024-2026']]
        
        # Create semesters sequentially for each session
        for session in available_sessions:
            for i in range(1, count + 1):
                try:
                    semester_start = start_date + timedelta(days=(i - 1) * 180)  # 6-month gap
                    semester_end = semester_start + timedelta(days=120)
                    semester = Semester.objects.create(
                        program=program,
                        session=session,
                        number=i,
                        name=f"Semester {i}",
                        start_time=semester_start,
                        end_time=semester_end,
                        is_active=(i == 1)  # Only the first semester is active
                    )
                    semesters.append(semester)
                except Exception as e:
                    print(f"Error creating semester {i} for program {program.name} and session {session.name}: {e}")
    
    return semesters

def create_fake_academic_sessions():
    sessions = []
    bs_sessions = [('2021-2025', 8), ('2022-2026', 6), ('2023-2027', 4), ('2024-2028', 2)]
    ms_sessions = [('2023-2025', 4), ('2024-2026', 2)]
    for name, _ in bs_sessions:
        start_year = int(name.split('-')[0])
        try:
            session = AcademicSession.objects.create(
                name=name,
                start_year=start_year,
                end_year=start_year + 4,
                is_active=(name == '2024-2028'),
                description=fake.text(max_nb_chars=300)
            )
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {name}: {e}")
    for name, _ in ms_sessions:
        start_year = int(name.split('-')[0])
        try:
            session = AcademicSession.objects.create(
                name=name,
                start_year=start_year,
                end_year=start_year + 2,
                is_active=(name == '2024-2026'),
                description=fake.text(max_nb_chars=300)
            )
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {name}: {e}")
    return sessions

def create_fake_admission_cycles(programs, sessions):
    admission_cycles = []
    for program in programs:
        for session in sessions:
            if (program.degree_type == 'BS' and session.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or \
               (program.degree_type == 'MS' and session.name in ['2023-2025', '2024-2026']):
                try:
                    admission_cycle = AdmissionCycle.objects.create(
                        program=program,
                        session=session,
                        application_start=fake.date_this_year(),
                        application_end=fake.date_this_year() + timedelta(days=30),
                        is_open=session.is_active
                    )
                    admission_cycles.append(admission_cycle)
                except Exception as e:
                    print(f"Error creating admission cycle for program {program.name}: {e}")
    return admission_cycles

def create_fake_applicants(users, faculties, departments, programs, sessions):
    applicants = []
    available_users = users.copy()
    shifts = ['morning', 'evening']
    for program in programs:
        student_count = 20 if program.degree_type == 'BS' else 10
        program_shifts = [shift for shift in shifts for _ in range(student_count // 2)]
        random.shuffle(program_shifts)
        for i in range(student_count):
            if not available_users:
                print(f"Warning: Not enough unique users for applicants for program {program.name}")
                break
            user = random.choice(available_users)
            gender = random.choice(['male', 'female'])
            first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
            full_name = f"{random.choice(first_names)} {random.choice(muslim_last_names)}"
            if program.degree_type == 'BS':
                session = random.choice([s for s in sessions if s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']])
            else:
                session = random.choice([s for s in sessions if s.name in ['2023-2025', '2024-2026']])
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
                    cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}",
                    dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                    contact_no=f"0{random.randint(3000000000,9999999999):010d}",
                    father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                    father_occupation=fake.job(),
                    permanent_address=fake.address().replace('\n', ', '),
                    shift=program_shifts[i],
                    declaration=True
                )
                applicants.append(applicant)
                available_users.remove(user)
            except Exception as e:
                print(f"Error creating applicant {full_name}: {e}")
    print(f"Remaining users after applicants: {len(available_users)}")
    return applicants

def create_fake_teachers(users, departments):
    teachers = []
    available_users = users.copy()
    designations = ['Professor'] * 9 + ['Head of Department']  # 1 HOD + 9 Professors per department
    for department in departments:
        print(f"Processing teachers for department: {department.name}")
        # Reinitialize designations for each department
        dept_designations = designations.copy()
        random.shuffle(dept_designations)
        dept_teachers = 0
        for _ in range(10):  # 10 teachers per department
            if not available_users:
                print(f"Warning: Not enough users for teachers in {department.name}, created {dept_teachers} teachers")
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
                dept_teachers += 1
            except Exception as e:
                print(f"Error creating teacher for {department.name}: {e}")
        print(f"Created {dept_teachers} teachers for {department.name}")
    print(f"Total teachers created: {len(teachers)}")
    print(f"Remaining users after teachers: {len(available_users)}")
    return teachers

def create_fake_courses():
    courses = []
    for code, name in course_data:
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
    return courses

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters):
    offerings = []
    if not teachers:
        print("Error: No teachers available for course offerings")
        return []
    offering_types = ['regular', 'elective', 'core']
    shifts = ['morning', 'evening', 'both']
    # Ensure at least 15 courses are offered for BSCS
    bscs_program = next(p for p in programs if p.name == 'BSCS')
    cs_courses = [c for c in courses if c.code.startswith('CS')]
    for course in cs_courses[:15]:  # First 15 CS courses for BSCS to ensure coverage
        try:
            offering = CourseOffering.objects.create(
                course=course,
                teacher=random.choice(teachers),
                department=bscs_program.department,
                program=bscs_program,
                academic_session=random.choice(sessions),
                semester=random.choice([s for s in semesters if s.program == bscs_program]),
                is_active=True,
                current_enrollment=5,
                offering_type=random.choice(offering_types),
                shift=random.choice(shifts)
            )
            offerings.append(offering)
        except Exception as e:
            print(f"Error creating course offering for course {course.code}: {e}")
    # Offer remaining courses to other programs
    remaining_courses = [c for c in courses if c not in cs_courses[:15]]
    for course in remaining_courses:
        try:
            offering = CourseOffering.objects.create(
                course=course,
                teacher=random.choice(teachers),
                department=random.choice(departments),
                program=random.choice(programs),
                academic_session=random.choice(sessions),
                semester=random.choice(semesters),
                is_active=True,
                current_enrollment=5,
                offering_type=random.choice(offering_types),
                shift=random.choice(shifts)
            )
            offerings.append(offering)
        except Exception as e:
            print(f"Error creating course offering for course {course.code}: {e}")
    return offerings

def create_fake_students(applicants, programs):
    students = []
    for applicant in applicants:
        try:
            # program_semesters = [s for s in semesters if s.program == applicant.program and s.number == 1]
            # if not program_semesters:
            #     print(f"Warning: No Semester 1 for program {applicant.program.name}")
            #     continue
            student = Student.objects.create(
                applicant=applicant,
                user=applicant.user,
                university_roll_no=7000 + random.randint(1, 9999),
                college_roll_no=100 + random.randint(1, 9999),
                enrollment_date=fake.date_this_year(),
                program=applicant.program,
                current_status='active',
                emergency_contact=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                emergency_phone=f"0{random.randint(3000000000,9999999999):010d}"
            )
            students.append(student)
        except Exception as e:
            print(f"Error creating student for {applicant.full_name}: {e}")
    return students

def clear_existing_data():
    models_to_clear = [
        CustomUser, Faculty, Department, Program, Semester, AcademicSession,
        AdmissionCycle, Applicant, Teacher, Course, CourseOffering, Student
    ]
    for model in models_to_clear:
        try:
            model.objects.all().delete()
            print(f"Cleared data for {model.__name__}")
        except Exception as e:
            print(f"Error clearing data for {model.__name__}: {e}")

def main():
    print("Creating fake data...")
    if input("Clear existing data? (yes/no): ").lower() == 'yes':
        clear_existing_data()

    users = create_fake_users(250)
    print(f"Created {len(users)} users")  

    faculties = create_fake_faculties()
    print(f"Created {len(faculties)} faculties")

    departments = create_fake_departments(faculties)
    print(f"Created {len(departments)} departments")

    programs = create_fake_programs(departments)
    print(f"Created {len(programs)} programs")

    sessions = create_fake_academic_sessions()
    print(f"Created {len(sessions)} sessions")

    # semesters = create_fake_semesters(programs, sessions)  # Pass both programs and sessions
    # print(f"Created {len(semesters)} semesters")

    admission_cycles = create_fake_admission_cycles(programs, sessions)
    print(f"Created {len(admission_cycles)} admission cycles")

    applicants = create_fake_applicants(users, faculties, departments, programs, sessions)
    print(f"Created {len(applicants)} applicants")

    teachers = create_fake_teachers(users, departments)
    print(f"Created {len(teachers)} teachers")

    courses = create_fake_courses()
    print(f"Created {len(courses)} courses")

    # course_offerings = create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters)
    # print(f"Created {len(course_offerings)} course offerings")

    students = create_fake_students(applicants, programs)
    print(f"Created {len(students)} students")

    print("Fake data creation completed!")

if __name__ == "__main__":
    main()