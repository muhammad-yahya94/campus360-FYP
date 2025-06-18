import os
import django
import random
import sys
from datetime import timedelta
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')

try:
    django.setup()
    from django.utils import timezone
    from django.core.files.base import ContentFile
    from academics.models import Faculty, Department, Program, Semester
    from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
    from courses.models import Course, CourseOffering, StudyMaterial, Assignment, AssignmentSubmission, ExamResult
    from faculty_staff.models import Teacher, Office, OfficeStaff
    from payment.models import Payment
    from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
    from users.models import CustomUser
    import uuid
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

fake = Faker()

# Muslim names and university data (unchanged from your provided script)
muslim_first_names_male = [
    'Ahmed', 'Ali', 'Hassan', 'Hussain', 'Omar', 'Ibrahim', 'Yousuf', 'Abdullah', 'Hamza', 'Bilal',
    'Khalid', 'Saad', 'Zain', 'Arham', 'Rayyan', 'Taha', 'Adeel', 'Faisal', 'Imran', 'Noman'
]
muslim_first_names_female = [
    'Aisha', 'Fatima', 'Maryam', 'Zainab', 'Khadija', 'Amna', 'Hafsa', 'Sana', 'Noor', 'Sara',
    'Ayesha', 'Hina', 'Mahnoor', 'Iqra', 'Rabia', 'Bushra', 'Sumaira', 'Zara', 'Lubna', 'Eman'
]
muslim_last_names = [
    'Khan', 'Ahmed', 'Malik', 'Siddiqui', 'Hussain', 'Shah', 'Raza', 'Iqbal', 'Anwar', 'Chaudhry',
    'Mahmood', 'Abbasi', 'Qureshi', 'Farooqi', 'Sheikh', 'Javed', 'Aslam', 'Baig', 'Nawaz', 'Zafar'
]
university_faculties = [
    'Faculty of Engineering and Technology', 'Faculty of Sciences', 'Faculty of Arts and Humanities',
    'Faculty of Business Administration', 'Faculty of Social Sciences', 'Faculty of Islamic Studies'
]
university_departments = {
    'Faculty of Engineering and Technology': [
        'Computer Science', 'Electrical Engineering', 'Mechanical Engineering', 'Civil Engineering'
    ],
    'Faculty of Sciences': [
        'Mathematics', 'Physics', 'Chemistry', 'Biology'
    ],
    'Faculty of Arts and Humanities': [
        'English', 'Urdu', 'History', 'Fine Arts'
    ],
    'Faculty of Business Administration': [
        'Management Sciences', 'Accounting and Finance', 'Marketing'
    ],
    'Faculty of Social Sciences': [
        'Sociology', 'Psychology', 'Economics', 'Political Science'
    ],
    'Faculty of Islamic Studies': [
        'Islamic Studies', 'Arabic'
    ]
}
university_programs = {
    'Computer Science': ['BS Computer Science', 'MS Computer Science', 'PhD Computer Science'],
    'Electrical Engineering': ['BS Electrical Engineering', 'MS Electrical Engineering'],
    'Mechanical Engineering': ['BS Mechanical Engineering'],
    'Civil Engineering': ['BS Civil Engineering'],
    'Mathematics': ['BS Mathematics', 'MPhil Mathematics'],
    'Physics': ['BS Physics', 'MPhil Physics'],
    'Chemistry': ['BS Chemistry'],
    'Biology': ['BS Biology'],
    'English': ['BS English', 'MA English'],
    'Urdu': ['BS Urdu'],
    'History': ['BS History'],
    'Fine Arts': ['BS Fine Arts'],
    'Management Sciences': ['BBA', 'MBA'],
    'Accounting and Finance': ['BS Accounting and Finance'],
    'Marketing': ['BS Marketing'],
    'Sociology': ['BS Sociology'],
    'Psychology': ['BS Psychology'],
    'Economics': ['BS Economics'],
    'Political Science': ['BS Political Science'],
    'Islamic Studies': ['BS Islamic Studies', 'MA Islamic Studies'],
    'Arabic': ['BS Arabic']
}
course_codes = [
    'CS101', 'CS201', 'CS301', 'EE101', 'EE202', 'ME101', 'CE101', 'MATH101', 'MATH201', 'PHY101',
    'CHEM101', 'BIO101', 'ENG101', 'URD101', 'HIST101', 'ART101', 'MGT101', 'ACC101', 'MKT101',
    'SOC101', 'PSY101', 'ECO101', 'POL101', 'ISL101', 'ARB101'
]
course_names = [
    'Introduction to Programming', 'Data Structures', 'Database Systems', 'Circuit Analysis',
    'Electronics', 'Thermodynamics', 'Structural Engineering', 'Calculus I', 'Linear Algebra',
    'Mechanics', 'Organic Chemistry', 'Cell Biology', 'English Composition', 'Urdu Literature',
    'Pakistan History', 'Painting Techniques', 'Principles of Management', 'Financial Accounting',
    'Marketing Principles', 'Introduction to Sociology', 'General Psychology', 'Microeconomics',
    'International Relations', 'Islamic Jurisprudence', 'Arabic Grammar'
]

def create_fake_image():
    from PIL import Image
    import io
    image = Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4()}.png")

def create_fake_users(count=1000):
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
                info=fake.text(max_nb_chars=200),
                profile_picture=create_fake_image() if random.choice([True, False]) else None
            )
            users.append(user)
        except Exception as e:
            print(f"Error creating user {email}: {e}")
    return users

def create_fake_faculties(count=3):
    faculties = []
    selected_faculties = random.sample(university_faculties, min(count, len(university_faculties)))
    for name in selected_faculties:
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

def create_fake_departments(faculties, count_per_faculty=2):
    departments = []
    for faculty in faculties:
        faculty_name = faculty.name
        available_depts = university_departments.get(faculty_name, [])
        selected_depts = random.sample(available_depts, min(count_per_faculty, len(available_depts)))
        for name in selected_depts:
            try:
                department = Department.objects.create(
                    faculty=faculty,
                    name=name,
                    slug=fake.slug(name),
                    code=fake.lexify(text="???").upper(),
                    image=create_fake_image() if random.choice([True, False]) else None,
                    introduction=fake.text(max_nb_chars=200),
                    details=fake.text(max_nb_chars=500)
                )
                departments.append(department)
            except Exception as e:
                print(f"Error creating department {name}: {e}")
    return departments

def create_fake_programs(departments, count_per_department=2):
    programs = []
    degree_types = ['BS', 'MS', 'PhD', 'MPhil', 'BBA', 'MBA', 'MA']
    for department in departments:
        dept_name = department.name
        available_programs = university_programs.get(dept_name, [])
        selected_programs = random.sample(available_programs, min(count_per_department, len(available_programs)))
        for name in selected_programs:
            try:
                degree_type = name.split()[0] if name.split()[0] in degree_types else random.choice(degree_types)
                program = Program.objects.create(
                    department=department,
                    name=name,
                    degree_type=degree_type,
                    duration_years=random.randint(2, 5),
                    total_semesters=random.randint(4, 10),
                    start_year=random.randint(2000, 2020),
                    end_year=None if random.choice([True, False]) else random.randint(2020, 2025),
                    is_active=True
                )
                programs.append(program)
            except Exception as e:
                print(f"Error creating program {name}: {e}")
    return programs

def create_fake_semesters(programs, semesters_per_program=8):
    semesters = []
    for program in programs:
        for i in range(1, semesters_per_program + 1):
            try:
                semester = Semester.objects.create(
                    program=program,
                    number=i,
                    name=f"Semester {i}",
                    description=fake.text(max_nb_chars=200),
                    start_time=fake.date_this_year(),
                    end_time=fake.date_this_year() + timedelta(days=120),
                    is_active=(i == 1 or i == semesters_per_program)
                )
                semesters.append(semester)
            except Exception as e:
                print(f"Error creating semester for program {program.name}: {e}")
    return semesters

def create_fake_academic_sessions(count=5):
    sessions = []
    session_names = ['Fall 2021', 'Spring 2022', 'Fall 2022', 'Spring 2023', 'Fall 2023', 'Spring 2024', 'Fall 2024', 'Spring 2025']
    selected_sessions = random.sample(session_names, min(count, len(session_names)))
    for name in selected_sessions:
        start_year = int(name.split()[-1])
        try:
            session = AcademicSession.objects.create(
                name=name,
                start_year=start_year,
                end_year=start_year + 1,
                is_active=(name == selected_sessions[-1]),
                description=fake.text(max_nb_chars=300)
            )
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {name}: {e}")
    return sessions

def create_fake_admission_cycles(programs, sessions, count_per_program=2):
    admission_cycles = []
    for program in programs:
        for _ in range(count_per_program):
            session = random.choice(sessions)
            try:
                admission_cycle = AdmissionCycle.objects.create(
                    program=program,
                    session=session,
                    application_start=fake.date_this_year(),
                    application_end=fake.date_this_year() + timedelta(days=30),
                    is_open=(session.is_active and random.choice([True, False]))
                )
                admission_cycles.append(admission_cycle)
            except Exception as e:
                print(f"Error creating admission cycle for program {program.name}: {e}")
    return admission_cycles

def create_fake_applicants(users, faculties, departments, programs, count=600):
    applicants = []
    available_users = users.copy()
    shifts = ['morning', 'evening']
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users for applicants")
            break
        user = random.choice(available_users)
        gender = random.choice(['male', 'female'])
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        full_name = f"{random.choice(first_names)} {random.choice(muslim_last_names)}"
        try:
            applicant = Applicant.objects.create(
                user=user,
                faculty=random.choice(faculties),
                department=random.choice(departments),
                program=random.choice(programs),
                status='accepted',
                applicant_photo=create_fake_image() if random.choice([True, False]) else None,
                full_name=full_name,
                religion='Islam',
                caste=fake.word() if random.choice([True, False]) else '',
                cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1000000,9999999)}",
                contact_no=f"+92{3000000000 + random.randint(0, 99999999):010d}",  # Fixed length
                identification_mark=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                father_occupation=fake.job(),
                father_cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1000000,9999999)}" if random.choice([True, False]) else '',
                monthly_income=random.randint(50000, 200000) if random.choice([True, False]) else None,
                relationship='father',
                permanent_address=fake.address().replace('\n', ', '),
                shift=random.choice(shifts),
                declaration=True
            )
            applicants.append(applicant)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating applicant {full_name}: {e}")
    return applicants

def create_fake_academic_qualifications(applicants, count_per_applicant=2):
    qualifications = []
    exams = ['Matriculation', 'Intermediate', 'Bachelor’s', 'Entry Test']
    boards = ['Lahore Board', 'FBISE', 'Punjab University', 'NTS']
    for applicant in applicants:
        for _ in range(count_per_applicant):
            exam = random.choice(exams)
            try:
                qualification = AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=exam,
                    passing_year=random.randint(2015, 2023),
                    marks_obtained=random.randint(600, 1100),
                    total_marks=1100 if exam != 'Entry Test' else 100,
                    division=random.choice(['1st', '2nd']) if exam != 'Entry Test' else None,
                    subjects=fake.text(max_nb_chars=100),
                    board=random.choice(boards),
                    certificate_file=create_fake_image() if random.choice([True, False]) else None
                )
                qualifications.append(qualification)
            except Exception as e:
                print(f"Error creating academic qualification for {applicant.full_name}: {e}")
    return qualifications

def create_fake_extra_curricular_activities(applicants, count_per_applicant=1):
    activities = []
    activity_types = ['Debate Competition', 'Sports Tournament', 'Qirat Competition', 'Volunteer Work', 'Art Exhibition']
    for applicant in applicants:
        for _ in range(count_per_applicant):
            try:
                activity = ExtraCurricularActivity.objects.create(
                    applicant=applicant,
                    activity=random.choice(activity_types),
                    position=fake.job() if random.choice([True, False]) else '',
                    achievement=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                    activity_year=random.randint(2015, 2023),
                    certificate_file=create_fake_image() if random.choice([True, False]) else None
                )
                activities.append(activity)
            except Exception as e:
                print(f"Error creating extra-curricular activity for {applicant.full_name}: {e}")
    return activities

def create_fake_teachers(users, departments, count=20):
    teachers = []
    available_users = users.copy()
    count = min(count, len(available_users))
    shifts = ['morning', 'evening', 'both']
    designations = ['Professor', 'Associate Professor', 'Assistant Professor', 'Head of Department']
    qualifications = ['PhD in Computer Science', 'MPhil in Mathematics', 'PhD in Physics', 'MA in English', 'MBA']
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users for teachers")
            break
        user = random.choice(available_users)
        gender = random.choice(['male', 'female'])
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        try:
            teacher = Teacher.objects.create(
                user=user,
                department=random.choice(departments),
                designation=random.choice(designations),
                contact_no=f"+92{3000000000 + random.randint(0, 99999999):010d}",  # Fixed length
                qualification=random.choice(qualifications),
                hire_date=fake.date_this_decade(),
                is_active=True,
                linkedin_url=fake.url() if random.choice([True, False]) else '',
                twitter_url=fake.url() if random.choice([True, False]) else '',
                personal_website=fake.url() if random.choice([True, False]) else '',
                experience=fake.text(max_nb_chars=300),
                shift_preference=random.choice(shifts)
            )
            teachers.append(teacher)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating teacher {user.first_name} {user.last_name}: {e}")
    return teachers

def create_fake_offices(count=3):
    offices = []
    office_names = ['Registrar Office', 'Examination Office', 'Admission Office']
    for name in office_names[:count]:
        try:
            office = Office.objects.create(
                name=name,
                description=fake.text(max_nb_chars=300),
                image=create_fake_image() if random.choice([True, False]) else None,
                location=fake.address().replace('\n', ', '),
                contact_email=fake.email(),
                contact_phone=f"+92{3000000000 + random.randint(0, 99999999):010d}",
                slug=fake.slug(name)
            )
            offices.append(office)
        except Exception as e:
            print(f"Error creating office {name}: {e}")
    return offices

def create_fake_office_staff(users, offices, count=10):
    staff = []
    available_users = users.copy()
    count = min(count, len(available_users))
    positions = ['Clerk', 'Assistant Registrar', 'Admission Officer']
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users for office staff")
            break
        user = random.choice(available_users)
        try:
            office_staff = OfficeStaff.objects.create(
                user=user,
                office=random.choice(offices),
                position=random.choice(positions),
                contact_no=f"+92{3000000000 + random.randint(0, 99999999):010d}" if random.choice([True, False]) else ''
            )
            staff.append(office_staff)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating office staff {user.first_name} {user.last_name}: {e}")
    return staff

def create_fake_courses(count=20):
    courses = []
    selected_courses = random.sample(list(zip(course_codes, course_names)), min(count, len(course_codes)))
    for code, name in selected_courses:
        try:
            course = Course.objects.create(
                code=code,
                name=name,
                credits=random.randint(2, 4),
                is_active=True,
                description=fake.text(max_nb_chars=300)
            )
            courses.append(course)
        except Exception as e:
            print(f"Error creating course {code}: {e}")
    for course in courses:
        prereqs = random.sample(courses, random.randint(0, min(2, len(courses) - 1)))
        course.prerequisites.set([c for c in prereqs if c != course])
    return courses

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, count_per_course=3):
    offerings = []
    if not teachers:
        print("Error: No teachers available for course offerings")
        return []
    offering_types = ['regular', 'elective', 'special', 'core']
    shifts = ['morning', 'evening', 'both']
    for course in courses:
        for _ in range(count_per_course):
            teacher = random.choice(teachers)
            shift = random.choice(shifts)
            if shift != 'both' and teacher.shift_preference != 'both' and teacher.shift_preference != shift:
                shift = teacher.shift_preference
            try:
                offering = CourseOffering.objects.create(
                    course=course,
                    teacher=teacher,
                    department=random.choice(departments),
                    program=random.choice(programs),
                    academic_session=random.choice(sessions),
                    semester=random.choice(semesters),
                    is_active=True,
                    current_enrollment=random.randint(10, 50),
                    offering_type=random.choice(offering_types),
                    shift=shift
                )
                offerings.append(offering)
            except Exception as e:
                print(f"Error creating course offering for course {course.code}: {e}")
    return offerings

def create_fake_study_materials(course_offerings, teachers, count_per_offering=3):
    materials = []
    titles = ['Lecture Notes', 'Tutorial Sheet', 'Reference Book Chapter', 'Lab Manual']
    for offering in course_offerings:
        for _ in range(count_per_offering):
            try:
                material = StudyMaterial.objects.create(
                    course_offering=offering,
                    title=random.choice(titles),
                    description=fake.text(max_nb_chars=200),
                    file=create_fake_image(),
                    uploaded_by=random.choice(teachers),
                    is_active=True
                )
                materials.append(material)
            except Exception as e:
                print(f"Error creating study material for offering {offering}: {e}")
    return materials

def create_fake_assignments(course_offerings, teachers, count_per_offering=3):
    assignments = []
    titles = ['Assignment 1', 'Project Proposal', 'Lab Report', 'Case Study']
    for offering in course_offerings:
        for _ in range(count_per_offering):
            try:
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    title=random.choice(titles),
                    description=fake.text(max_nb_chars=300),
                    file=create_fake_image() if random.choice([True, False]) else None,
                    created_by=random.choice(teachers),
                    due_date=timezone.make_aware(fake.date_time_this_year(after_now=True)) + timedelta(days=30),
                    total_marks=100,
                    is_active=True
                )
                assignments.append(assignment)
            except Exception as e:
                print(f"Error creating assignment for offering {offering}: {e}")
    return assignments

def create_fake_payments(applicants, count=100):
    payments = []
    for _ in range(count):
        try:
            payment = Payment.objects.create(
                user=random.choice(applicants),
                stripe_session_id=str(uuid.uuid4()),
                stripe_payment_intent=str(uuid.uuid4()) if random.choice([True, False]) else None,
                amount=random.uniform(5000, 50000),
                status=random.choice(['pending', 'paid', 'failed'])
            )
            payments.append(payment)
        except Exception as e:
            print(f"Error creating payment: {e}")
    return payments

def create_fake_students(applicants, programs, semesters, students_per_shift=50):
    students = []
    shifts = ['morning', 'evening']
    available_applicants = applicants.copy()
    for program in programs:
        for shift in shifts:
            print(f"Creating {students_per_shift} students for {program.name} ({shift} shift)")
            program_shift_applicants = [a for a in available_applicants if a.program == program and a.shift == shift]
            if len(program_shift_applicants) < students_per_shift:
                print(f"Warning: Only {len(program_shift_applicants)} applicants available for {program.name} ({shift} shift). Creating additional applicants.")
                needed = students_per_shift - len(program_shift_applicants)
                new_users = create_fake_users(needed)
                new_applicants = []
                for user in new_users:
                    gender = random.choice(['male', 'female'])
                    first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
                    full_name = f"{random.choice(first_names)} {random.choice(muslim_last_names)}"
                    try:
                        applicant = Applicant.objects.create(
                            user=user,
                            faculty=program.department.faculty,
                            department=program.department,
                            program=program,
                            status='accepted',
                            applicant_photo=create_fake_image() if random.choice([True, False]) else None,
                            full_name=full_name,
                            religion='Islam',
                            caste=fake.word() if random.choice([True, False]) else '',
                            cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1000000,9999999)}",
                            contact_no=f"+92{3000000000 + random.randint(0, 99999999):010d}",
                            identification_mark=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                            father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                            father_occupation=fake.job(),
                            father_cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1000000,9999999)}" if random.choice([True, False]) else '',
                            monthly_income=random.randint(50000, 200000) if random.choice([True, False]) else None,
                            relationship='father',
                            permanent_address=fake.address().replace('\n', ', '),
                            shift=shift,
                            declaration=True
                        )
                        new_applicants.append(applicant)
                    except Exception as e:
                        print(f"Error creating additional applicant for {program.name} ({shift}): {e}")
                available_applicants.extend(new_applicants)
                program_shift_applicants.extend(new_applicants)
            selected_applicants = random.sample(program_shift_applicants, min(students_per_shift, len(program_shift_applicants)))
            for applicant in selected_applicants:
                if not hasattr(applicant, 'student_profile'):
                    try:
                        program_semesters = [s for s in semesters if s.program == program]
                        if not program_semesters:
                            print(f"Warning: No semesters available for program {program.name}")
                            continue
                        student = Student.objects.create(
                            applicant=applicant,
                            user=applicant.user,
                            university_roll_no=f"2023-{random.randint(1000,9999)}",
                            college_roll_no=f"{random.randint(100,999)}" if random.choice([True, False]) else None,
                            enrollment_date=fake.date_this_decade(),
                            graduation_date=None,
                            program=program,
                            current_semester=random.choice(program_semesters),
                            current_status='active',
                            emergency_contact=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                            emergency_phone=f"+92{3000000000 + random.randint(0, 99999999):010d}"
                        )
                        students.append(student)
                        available_applicants.remove(applicant)
                    except Exception as e:
                        print(f"Error creating student for {applicant.full_name}: {e}")
    return students

def create_fake_student_semester_enrollments(students, semesters, count_per_student=2):
    enrollments = []
    for student in students:
        available_semesters = [s for s in semesters if s.program == student.program]
        for _ in range(min(count_per_student, len(available_semesters))):
            semester = random.choice(available_semesters)
            if not StudentSemesterEnrollment.objects.filter(student=student, semester=semester).exists():
                try:
                    enrollment = StudentSemesterEnrollment.objects.create(
                        student=student,
                        semester=semester,
                        status=random.choice(['enrolled', 'completed', 'dropped'])
                    )
                    enrollments.append(enrollment)
                    available_semesters.remove(semester)
                except Exception as e:
                    print(f"Error creating semester enrollment for {student.applicant.full_name}: {e}")
    return enrollments

def create_fake_course_enrollments(semester_enrollments, course_offerings, count_per_enrollment=3):
    enrollments = []
    for se in semester_enrollments:
        available_offerings = [
            co for co in course_offerings
            if co.semester == se.semester and
            (co.shift == 'both' or co.shift == se.student.applicant.shift)
        ]
        for _ in range(min(count_per_enrollment, len(available_offerings))):
            course_offering = random.choice(available_offerings)
            if not CourseEnrollment.objects.filter(student_semester_enrollment=se, course_offering=course_offering).exists():
                try:
                    enrollment = CourseEnrollment.objects.create(
                        student_semester_enrollment=se,
                        course_offering=course_offering,
                        status=random.choice(['enrolled', 'completed', 'dropped'])
                    )
                    enrollments.append(enrollment)
                    available_offerings.remove(course_offering)
                except Exception as e:
                    print(f"Error creating course enrollment for {se.student.applicant.full_name}: {e}")
    return enrollments

def create_fake_assignment_submissions(assignments, students, teachers, count_per_assignment=10):
    submissions = []
    for assignment in assignments:
        course_offering = assignment.course_offering
        enrolled_students = [
            s for s in students
            if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s,
                course_offering=course_offering
            ).exists()
        ]
        available_students = random.sample(enrolled_students, min(count_per_assignment, len(enrolled_students)))
        for student in available_students:
            if not AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
                try:
                    submission = AssignmentSubmission.objects.create(
                        assignment=assignment,
                        student=student,
                        file=create_fake_image(),
                        marks_obtained=random.randint(50, 100) if random.choice([True, False]) else None,
                        feedback=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                        graded_by=random.choice(teachers) if random.choice([True, False]) else None,
                        graded_at=timezone.make_aware(fake.date_time_this_year()) if random.choice([True, False]) else None
                    )
                    submissions.append(submission)
                except Exception as e:
                    print(f"Error creating assignment submission for {student.applicant.full_name}: {e}")
    return submissions

def create_fake_exam_results(course_offerings, students, teachers, count_per_offering=10):
    results = []
    exam_types = ['midterm', 'final', 'quiz']
    for offering in course_offerings:
        enrolled_students = [
            s for s in students
            if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s,
                course_offering=offering
            ).exists()
        ]
        available_students = random.sample(enrolled_students, min(count_per_offering, len(enrolled_students)))
        for student in available_students:
            exam_type = random.choice(exam_types)
            if not ExamResult.objects.filter(course_offering=offering, student=student, exam_type=exam_type).exists():
                try:
                    result = ExamResult.objects.create(
                        course_offering=offering,
                        student=student,
                        exam_type=exam_type,
                        total_marks=100,
                        marks_obtained=random.randint(50, 100),
                        graded_by=random.choice(teachers),
                        remarks=fake.text(max_nb_chars=200) if random.choice([True, False]) else ''
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error creating exam result for {student.applicant.full_name}: {e}")
    return results

def clear_existing_data():
    models_to_clear = [
        CustomUser, Faculty, Department, Program, Semester, AcademicSession,
        AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity,
        Teacher, Office, OfficeStaff, Course, CourseOffering, StudyMaterial,
        Assignment, AssignmentSubmission, ExamResult, Payment, Student,
        StudentSemesterEnrollment, CourseEnrollment
    ]
    for model in models_to_clear:
        try:
            model.objects.all().delete()
            print(f"Cleared data for {model.__name__}")
        except Exception as e:
            print(f"Error clearing data for {model.__name__}: {e}")

def main():
    print("Creating fake data...")
    if input("Clear existing data? (y/n): ").lower() == 'y':
        clear_existing_data()

    users = create_fake_users(1000)
    print(f"Created {len(users)} users")

    faculties = create_fake_faculties(3)
    print(f"Created {len(faculties)} faculties")

    departments = create_fake_departments(faculties, 2)
    print(f"Created {len(departments)} departments")

    programs = create_fake_programs(departments, 2)
    print(f"Created {len(programs)} programs")

    semesters = create_fake_semesters(programs, 8)
    print(f"Created {len(semesters)} semesters")

    sessions = create_fake_academic_sessions(5)
    print(f"Created {len(sessions)} academic sessions")

    admission_cycles = create_fake_admission_cycles(programs, sessions, 2)
    print(f"Created {len(admission_cycles)} admission cycles")

    applicants = create_fake_applicants(users, faculties, departments, programs, 600)
    print(f"Created {len(applicants)} applicants")

    qualifications = create_fake_academic_qualifications(applicants, 2)
    print(f"Created {len(qualifications)} academic qualifications")

    activities = create_fake_extra_curricular_activities(applicants, 1)
    print(f"Created {len(activities)} extra-curricular activities")

    teachers = create_fake_teachers(users, departments, 20)
    print(f"Created {len(teachers)} teachers")

    offices = create_fake_offices(3)
    print(f"Created {len(offices)} offices")

    office_staff = create_fake_office_staff(users, offices, 10)
    print(f"Created {len(office_staff)} office staff")

    courses = create_fake_courses(20)
    print(f"Created {len(courses)} courses")

    course_offerings = create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, 3)
    print(f"Created {len(course_offerings)} course offerings")

    study_materials = create_fake_study_materials(course_offerings, teachers, 3)
    print(f"Created {len(study_materials)} study materials")

    assignments = create_fake_assignments(course_offerings, teachers, 3)
    print(f"Created {len(assignments)} assignments")

    payments = create_fake_payments(applicants, 100)
    print(f"Created {len(payments)} payments")

    students = create_fake_students(applicants, programs, semesters, students_per_shift=50)
    print(f"Created {len(students)} students")

    semester_enrollments = create_fake_student_semester_enrollments(students, semesters, 2)
    print(f"Created {len(semester_enrollments)} semester enrollments")

    course_enrollments = create_fake_course_enrollments(semester_enrollments, course_offerings, 3)
    print(f"Created {len(course_enrollments)} course enrollments")

    assignment_submissions = create_fake_assignment_submissions(assignments, students, teachers, 10)
    print(f"Created {len(assignment_submissions)} assignment submissions")

    exam_results = create_fake_exam_results(course_offerings, students, teachers, 10)
    print(f"Created {len(exam_results)} exam results")

    print("Fake data creation completed!")

if __name__ == "__main__":
    main()