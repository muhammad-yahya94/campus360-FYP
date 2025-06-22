import os
import django
import random
import sys
from datetime import timedelta, date
from faker import Faker
from django.utils import timezone
from django.core.files.base import ContentFile
import uuid

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
try:
    django.setup()
    from users.models import CustomUser
    from admissions.models import Applicant, AcademicSession, AdmissionCycle
    from students.models import Student
    from academics.models import Faculty, Department, Program, Semester
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
    'Faculty of Sciences',
    'Faculty of Business Administration'
]
university_departments = {
    'Faculty of Engineering and Technology': ['Computer Science'],
    'Faculty of Sciences': ['Mathematics'],
    'Faculty of Business Administration': ['Management Sciences']
}
university_programs = {
    'Computer Science': ['BS Computer Science', 'BS Software Engineering', 'MS Computer Science'],
    'Mathematics': ['BS Mathematics'],
    'Management Sciences': ['BBA', 'MBA', 'B.Com']
}

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
    program_names = [prog for progs in university_programs.values() for prog in progs]
    for i in range(1, count + 1):
        gender = random.choice(['male', 'female'])
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        first_name = random.choice(first_names)
        last_name = random.choice(muslim_last_names)
        program_index = (i - 1) % len(program_names)
        program = program_names[program_index]
        domain = {
            'BS Computer Science': 'bsit.com',
            'BS Software Engineering': 'bsse.com',
            'MS Computer Science': 'mscs.com',
            'BS Mathematics': 'bsmath.com',
            'BBA': 'bba.com',
            'MBA': 'mba.com',
            'B.Com': 'bcom.com'
        }.get(program, 'example.com')
        email = f"stu{i}@{domain}"
        while email in existing_emails:
            email = f"stu{i}_{random.randint(1,999)}@{domain}"
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
        slug = fake.slug(name)
        try:
            faculty, created = Faculty.objects.get_or_create(
                name=name,
                defaults={'slug': slug, 'description': fake.text(max_nb_chars=300)}
            )
            if created:
                print(f"Created faculty {name}")
            else:
                print(f"Faculty {name} already exists, using existing record")
            faculties.append(faculty)
        except Exception as e:
            print(f"Error processing faculty {name}: {e}")
    return faculties

def create_fake_departments(faculties):
    departments = []
    for faculty in faculties:
        available_depts = university_departments.get(faculty.name, [])
        for name in available_depts:
            slug = fake.slug(name)
            try:
                department, created = Department.objects.get_or_create(
                    faculty=faculty,
                    name=name,
                    defaults={'slug': slug, 'code': fake.lexify(text="???").upper(), 'introduction': fake.text(max_nb_chars=200)}
                )
                if created:
                    print(f"Created department {name}")
                else:
                    print(f"Department {name} already exists, using existing record")
                departments.append(department)
            except Exception as e:
                print(f"Error processing department {name}: {e}")
    return departments

def create_fake_programs(departments):
    programs = []
    program_mapping = {
        'BS Computer Science': 'Computer Science',
        'BS Software Engineering': 'Computer Science',
        'MS Computer Science': 'Computer Science',
        'BS Mathematics': 'Mathematics',
        'BBA': 'Management Sciences',
        'MBA': 'Management Sciences',
        'B.Com': 'Management Sciences'
    }
    all_programs = [prog for progs in university_programs.values() for prog in progs]
    for program_name in all_programs:
        department_name = program_mapping[program_name]
        department = next((d for d in departments if d.name == department_name), None)
        if department:
            try:
                program, created = Program.objects.get_or_create(
                    department=department,
                    name=program_name,
                    defaults={'degree_type': program_name.split()[0], 'duration_years': 4, 'total_semesters': 8, 'start_year': 2020, 'is_active': True}
                )
                if created:
                    print(f"Created program {program_name}")
                else:
                    print(f"Program {program_name} already exists, using existing record")
                programs.append(program)
            except Exception as e:
                print(f"Error processing program {program_name}: {e}")
    return programs

def create_fake_semesters(programs):
    semesters = []
    for program in programs:
        for semester_num in range(1, program.total_semesters + 1):
            try:
                semester, created = Semester.objects.get_or_create(
                    program=program,
                    number=semester_num,
                    defaults={
                        'name': f'Semester {semester_num}',
                        'description': fake.text(max_nb_chars=200),
                        'start_time': timezone.now().date() - timedelta(days=30 * (program.total_semesters - semester_num)),
                        'end_time': timezone.now().date() + timedelta(days=30 * (program.total_semesters - semester_num + 1)),
                        'is_active': semester_num == 1  # Only the first semester is active initially
                    }
                )
                if created:
                    print(f"Created semester {semester} for {program.name}")
                else:
                    print(f"Semester {semester_num} for {program.name} already exists, using existing record")
                semesters.append(semester)
            except Exception as e:
                print(f"Error processing semester {semester_num} for {program.name}: {e}")
    return semesters

def create_fake_academic_sessions():
    sessions = []
    new_sessions = [
        ('Spring 2024-2028', 2024, 2028),
        ('Spring 2023-2027', 2023, 2027),
        ('Spring 2022-2026', 2022, 2026)
    ]
    for name, start_year, end_year in new_sessions:
        try:
            session, created = AcademicSession.objects.get_or_create(
                name=name,
                defaults={
                    'start_year': start_year,
                    'end_year': end_year,
                    'is_active': True,
                    'description': fake.text(max_nb_chars=200)
                }
            )
            if created:
                print(f"Created academic session {name}")
            else:
                print(f"Academic session {name} already exists, setting as active")
                session.is_active = True
                session.save()
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {name}: {e}")
    # Include existing active sessions
    existing_active_sessions = AcademicSession.objects.filter(is_active=True).exclude(name__in=[s.name for s in sessions])
    sessions.extend(existing_active_sessions)
    print(f"Total sessions retrieved: {len(sessions)}")
    return sessions

def create_fake_admission_cycles(programs, sessions):
    cycles = []
    if not programs or not sessions:
        print("Warning: No programs or sessions available, skipping admission cycle creation")
        return cycles
    for program in programs:
        for session in sessions:
            try:
                cycle, created = AdmissionCycle.objects.get_or_create(
                    program=program,
                    session=session,
                    defaults={
                        'application_start': timezone.now().date() - timedelta(days=60 * (2025 - session.start_year)),
                        'application_end': timezone.now().date() - timedelta(days=30 * (2025 - session.start_year)),
                        'is_open': False
                    }
                )
                if created:
                    print(f"Created admission cycle for {program} - {session}")
                else:
                    print(f"Admission cycle for {program} - {session} already exists, using existing record")
                cycles.append(cycle)
            except Exception as e:
                print(f"Error creating admission cycle for {program} - {session}: {e}")
    return cycles

def create_fake_applicants(users, programs, sessions):
    applicants = []
    shifts = ['morning', 'evening']
    program_names = [prog for progs in university_programs.values() for prog in progs]
    if not programs or not sessions:
        print("Warning: No programs or sessions available, creation of applicants skipped")
        return applicants
    
    # Distribute users across sessions (approx. 12-13 per session for 50 users)
    session_indices = [i % len(sessions) for i in range(len(users))]
    for i, user in enumerate(users):
        session = sessions[session_indices[i]]
        program_index = (i - 1) % len(program_names)
        program_name = program_names[program_index]
        program = next((p for p in programs if p.name == program_name), programs[0])  # Fallback to first program
        department = program.department
        gender = random.choice(['male', 'female'])
        first_names = muslim_first_names_male if gender == 'male' else muslim_first_names_female
        full_name = f"{random.choice(first_names)} {random.choice(muslim_last_names)}"
        try:
            applicant = Applicant.objects.create(
                user=user,
                faculty=department.faculty,
                department=department,
                program=program,
                status='accepted',
                full_name=full_name,
                religion='Islam',
                cnic=f"3520{random.randint(1000000,9999999)}-{random.randint(1,9)}",
                dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                contact_no=f"0{random.randint(3000000000,9999999999):010d}",
                father_name=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                father_occupation=fake.job(),
                permanent_address=fake.address().replace('\n', ', '),
                shift=random.choice(shifts),
                declaration=True
            )
            applicants.append(applicant)
        except Exception as e:
            print(f"Error creating applicant {full_name}: {e}")
    return applicants

def create_fake_students(applicants):
    students = []
    for applicant in applicants:
        try:
            # Get the first semester of the applicant's program
            first_semester = Semester.objects.filter(program=applicant.program, number=1).first()
            if not first_semester:
                print(f"Warning: No first semester found for {applicant.program.name}, skipping student creation for {applicant.full_name}")
                continue
            # Set enrollment date based on the session start year
            session = AdmissionCycle.objects.filter(program=applicant.program).first().session
            enrollment_year = session.start_year
            enrollment_date = fake.date_between(start_date=date(enrollment_year, 1, 1), end_date=date(enrollment_year, 12, 31))
            student = Student.objects.create(
                applicant=applicant,
                user=applicant.user,
                university_roll_no=20240000 + random.randint(1, 9999),
                enrollment_date=enrollment_date,
                program=applicant.program,
                current_semester=first_semester,
                current_status='active',
                emergency_contact=f"{random.choice(muslim_first_names_male)} {random.choice(muslim_last_names)}",
                emergency_phone=f"0{random.randint(3000000000,9999999999):010d}"
            )
            students.append(student)
        except Exception as e:
            print(f"Error creating student for {applicant.full_name}: {e}")
    return students

def clear_existing_data():
    models_to_clear = [CustomUser, Applicant, Student, Faculty, Department, Program, Semester, AcademicSession, AdmissionCycle]
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

    users = create_fake_users(50)
    print(f"Created {len(users)} users")

    faculties = create_fake_faculties()
    print(f"Created or used {len(faculties)} faculties")

    departments = create_fake_departments(faculties)
    print(f"Created or used {len(departments)} departments")

    programs = create_fake_programs(departments)
    print(f"Created or used {len(programs)} programs")

    semesters = create_fake_semesters(programs)
    print(f"Created or used {len(semesters)} semesters")

    sessions = create_fake_academic_sessions()
    print(f"Created or used {len(sessions)} academic sessions")

    admission_cycles = create_fake_admission_cycles(programs, sessions)
    print(f"Created or used {len(admission_cycles)} admission cycles")

    applicants = create_fake_applicants(users, programs, sessions)
    print(f"Created {len(applicants)} applicants")

    students = create_fake_students(applicants)
    print(f"Created {len(students)} students")

    print("Fake data creation completed!")

if __name__ == "__main__":
    main()