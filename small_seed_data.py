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
    from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
    from users.models import CustomUser
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

fake = Faker()  # No locale to avoid user_agent warning

# Muslim names
muslim_first_names_male = ['Ahmed', 'Ali', 'Hassan', 'Omar', 'Ibrahim', 'Yousuf', 'Abdullah', 'Hamza', 'Bilal', 'Khalid']
muslim_first_names_female = ['Aisha', 'Fatima', 'Maryam', 'Zainab', 'Khadija', 'Amna', 'Hafsa', 'Sana', 'Noor', 'Sara']
muslim_last_names = ['Khan', 'Ahmed', 'Malik', 'Hussain', 'Shah', 'Iqbal', 'Chaudhry', 'Mahmood', 'Siddiqui', 'Zafar']

# University data
university_faculties = [
    'Faculty of Engineering and Technology',
    'Faculty of Sciences',
    'Faculty of Business Administration'
]
university_departments = {
    'Faculty of Engineering and Technology': ['Computer Science', 'Electrical Engineering'],
    'Faculty of Sciences': ['Mathematics'],
    'Faculty of Business Administration': ['Management Sciences']
}
university_programs = {
    'Computer Science': ['BS Computer Science'],
    'Electrical Engineering': ['BS Electrical Engineering'],
    'Mathematics': ['BS Mathematics'],
    'Management Sciences': ['BBA']
}
course_codes = ['CS101', 'EE101', 'MATH101', 'MGT101']
course_names = ['Introduction to Programming', 'Circuit Analysis', 'Calculus I', 'Principles of Management']

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
                program = Program.objects.create(
                    department=department,
                    name=name,
                    degree_type=name.split()[0],
                    duration_years=4,
                    total_semesters=8,
                    start_year=2020,
                    is_active=True
                )
                programs.append(program)
            except Exception as e:
                print(f"Error creating program {name}: {e}")
    return programs

def create_fake_semesters(programs):
    semesters = []
    for program in programs:
        for i in range(1, 4):  # 3 semesters per program
            try:
                semester = Semester.objects.create(
                    program=program,
                    number=i,
                    name=f"Semester {i}",
                    start_time=fake.date_this_year(),
                    end_time=fake.date_this_year() + timedelta(days=120),
                    is_active=(i == 1)
                )
                semesters.append(semester)
            except Exception as e:
                print(f"Error creating semester for program {program.name}: {e}")
    return semesters

def create_fake_academic_sessions():
    sessions = []
    session_names = ['Fall 2024', 'Spring 2025']
    for name in session_names:
        start_year = int(name.split()[-1])
        try:
            session = AcademicSession.objects.create(
                name=name,
                start_year=start_year,
                end_year=start_year + 1,
                is_active=(name == 'Spring 2025'),
                description=fake.text(max_nb_chars=300)
            )
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {name}: {e}")
    return sessions

def create_fake_admission_cycles(programs, sessions):
    admission_cycles = []
    for program in programs[:2]:  # Only 2 programs for students
        for session in sessions:
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

def create_fake_applicants(users, faculties, departments, programs):
    applicants = []
    available_users = users.copy()
    shifts = ['morning', 'evening']
    selected_programs = programs[:2]  # Only 2 programs for 10 students
    for program in selected_programs:
        # Balance shifts: 3 morning, 2 evening
        program_shifts = [shifts[0]] * 3 + [shifts[1]] * 2
        random.shuffle(program_shifts)  # Shuffle to randomize order
        for i in range(5):  # 5 applicants per program
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
                    faculty=program.department.faculty,
                    department=program.department,
                    program=program,
                    status='accepted',
                    full_name=full_name,
                    religion='Islam',
                    cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}",
                    dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                    contact_no=f"0{random.randint(3000000000,9999999999):010d}",  # 11 chars
                    father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                    father_occupation=fake.job(),
                    permanent_address=fake.address().replace('\n', ', '),
                    shift=program_shifts[i],  # Use balanced shift
                    declaration=True
                )
                applicants.append(applicant)
                available_users.remove(user)
            except Exception as e:
                print(f"Error creating applicant {full_name}: {e}")
    return applicants

def create_fake_teachers(users, departments):
    teachers = []
    available_users = users.copy()
    designations = ['Professor', 'Associate Professor', 'Assistant Professor']
    qualifications = ['PhD in Computer Science', 'MPhil in Mathematics', 'MBA']
    for department in departments:
        # Create 1 HOD
        if not available_users:
            print("Warning: Not enough users for HOD")
            break
        user = random.choice(available_users)
        try:
            teacher = Teacher.objects.create(
                user=user,
                department=department,
                designation='Head of Department',
                contact_no=f"0{random.randint(3000000000,9999999999):010d}",  # 11 chars
                qualification=random.choice(qualifications),
                hire_date=fake.date_this_decade(),
                is_active=True,
                experience=fake.text(max_nb_chars=300)
            )
            teachers.append(teacher)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating HOD for {department.name}: {e}")
        # Create 5 teachers
        for _ in range(5):
            if not available_users:
                print("Warning: Not enough users for teachers")
                break
            user = random.choice(available_users)
            try:
                teacher = Teacher.objects.create(
                    user=user,
                    department=department,
                    designation=random.choice(designations),
                    contact_no=f"0{random.randint(3000000000,9999999999):010d}",  # 11 chars
                    qualification=random.choice(qualifications),
                    hire_date=fake.date_this_decade(),
                    is_active=True,
                    experience=fake.text(max_nb_chars=300)
                )
                teachers.append(teacher)
                available_users.remove(user)
            except Exception as e:
                print(f"Error creating teacher for {department.name}: {e}")
    return teachers

def create_fake_courses():
    courses = []
    for code, name in zip(course_codes, course_names):
        try:
            course = Course.objects.create(
                code=code,
                name=name,
                credits=3,
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
    for course in courses:
        try:
            offering = CourseOffering.objects.create(
                course=course,
                teacher=random.choice(teachers),
                department=random.choice(departments),
                program=random.choice(programs[:2]),  # Only 2 programs
                academic_session=random.choice(sessions),
                semester=random.choice(semesters),
                is_active=True,
                current_enrollment=5,
                offering_type=random.choice(offering_types),
                shift=random.choice(shifts)  # Set shift
            )
            offerings.append(offering)
        except Exception as e:
            print(f"Error creating course offering for course {course.code}: {e}")
    return offerings

def create_fake_students(applicants, programs, semesters):
    students = []
    for applicant in applicants:
        try:
            # Get Semester 1 for the applicant's program
            program_semesters = [s for s in semesters if s.program == applicant.program and s.number == 1]
            if not program_semesters:
                print(f"Warning: No Semester 1 for program {applicant.program.name}")
                continue
            student = Student.objects.create(
                applicant=applicant,
                user=applicant.user,
                university_roll_no=20240000 + random.randint(1, 9999),  # Numeric
                enrollment_date=fake.date_this_year(),
                program=applicant.program,
                current_semester=program_semesters[0],  # Use Semester 1
                current_status='active',
                emergency_contact=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                emergency_phone=f"0{random.randint(3000000000,9999999999):010d}"  # 11 chars
            )
            students.append(student)
        except Exception as e:
            print(f"Error creating student for {applicant.full_name}: {e}")
    return students

def create_fake_student_semester_enrollments(students, semesters):
    enrollments = []
    for student in students:
        semester = student.current_semester
        try:
            enrollment = StudentSemesterEnrollment.objects.create(
                student=student,
                semester=semester,
                status='enrolled'
            )
            enrollments.append(enrollment)
        except Exception as e:
            print(f"Error creating semester enrollment for {student.applicant.full_name}: {e}")
    return enrollments

def create_fake_course_enrollments(semester_enrollments, course_offerings):
    enrollments = []
    for se in semester_enrollments:
        available_offerings = [
            co for co in course_offerings
            if co.semester == se.semester and
            (co.shift == 'both' or co.shift == se.student.applicant.shift)
        ]
        for co in available_offerings[:2]:  # 2 courses per student
            try:
                enrollment = CourseEnrollment.objects.create(
                    student_semester_enrollment=se,
                    course_offering=co,
                    status='enrolled'
                )
                enrollments.append(enrollment)
            except Exception as e:
                print(f"Error creating course enrollment for {se.student.applicant.full_name}: {e}")
    return enrollments

def clear_existing_data():
    models_to_clear = [
        CustomUser, Faculty, Department, Program, Semester, AcademicSession,
        AdmissionCycle, Applicant, Teacher, Course, CourseOffering, Student,
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
    if input("Clear existing data? (yes/no): ").lower() == 'yes':
        clear_existing_data()

    users = create_fake_users(100)  # Increased to 100
    print(f"Created {len(users)} users")

    faculties = create_fake_faculties()
    print(f"Created {len(faculties)} faculties")

    departments = create_fake_departments(faculties)
    print(f"Created {len(departments)} departments")

    programs = create_fake_programs(departments)
    print(f"Created {len(programs)} programs")

    semesters = create_fake_semesters(programs)
    print(f"Created {len(semesters)} semesters")

    sessions = create_fake_academic_sessions()
    print(f"Created {len(sessions)} sessions")

    admission_cycles = create_fake_admission_cycles(programs, sessions)
    print(f"Created {len(admission_cycles)} admission cycles")

    applicants = create_fake_applicants(users, faculties, departments, programs)
    print(f"Created {len(applicants)} applicants")

    teachers = create_fake_teachers(users, departments)
    print(f"Created {len(teachers)} teachers")

    courses = create_fake_courses()
    print(f"Created {len(courses)} courses")

    course_offerings = create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters)
    print(f"Created {len(course_offerings)} course offerings")

    students = create_fake_students(applicants, programs, semesters)
    print(f"Created {len(students)} students")

    semester_enrollments = create_fake_student_semester_enrollments(students, semesters)
    print(f"Created {len(semester_enrollments)} semester enrollments")

    course_enrollments = create_fake_course_enrollments(semester_enrollments, course_offerings)
    print(f"Created {len(course_enrollments)} course enrollments")

    print("Fake data creation completed!")

if __name__ == "__main__":
    main()