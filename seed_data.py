import os
import django
from django.utils.text import slugify
from faker import Faker
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import your models
from users.models import CustomUser
from academics.models import Faculty, Department, Program, Semester
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from faculty_staff.models import Teacher
from courses.models import Course, CourseOffering
from students.models import Student, StudentEnrollment

# Initialize Faker
fake = Faker()

# Utility function to create a fixed date in a given year
def fixed_date_in_year(year):
    # Set a fixed date, e.g., July 1st of the given year
    return datetime(year, 7, 1)

# Current date for semester calculation
current_year = 2025  # As of May 25, 2025
semesters_per_year = 2

# Delete all existing data
def delete_old_data():
    print("Deleting old data...")
    StudentEnrollment.objects.all().delete()
    Student.objects.all().delete()
    ExtraCurricularActivity.objects.all().delete()
    AcademicQualification.objects.all().delete()
    Applicant.objects.all().delete()
    CourseOffering.objects.all().delete()
    Course.objects.all().delete()
    Teacher.objects.all().delete()
    CustomUser.objects.filter(is_superuser=False).delete()
    AdmissionCycle.objects.all().delete()
    AcademicSession.objects.all().delete()
    Semester.objects.all().delete()
    Program.objects.all().delete()
    Department.objects.all().delete()
    Faculty.objects.all().delete()
    print("Old data deleted successfully.")

# 1. Create Faculty records
def create_faculties():
    faculties_data = [
        {"name": "Faculty of Engineering", "description": "Faculty offering engineering programs."},
        {"name": "Faculty of Sciences", "description": "Faculty offering science programs."},
        {"name": "Faculty of Arts", "description": "Faculty offering arts and humanities programs."},
    ]
    faculties = []
    for data in faculties_data:
        faculty, created = Faculty.objects.get_or_create(
            name=data["name"],
            defaults={
                "slug": slugify(data["name"]),
                "description": data["description"],
            }
        )
        faculties.append(faculty)
    print(f"Created {len(faculties)} faculties.")
    return faculties

# 2. Create Department records
def create_departments(faculties):
    departments_data = [
        {"name": "Department of Computer Science", "code": "CS", "faculty": 0},
        {"name": "Department of Electrical Engineering", "code": "EE", "faculty": 0},
        {"name": "Department of Physics", "code": "PHY", "faculty": 1},
        {"name": "Department of Chemistry", "code": "CHEM", "faculty": 1},
        {"name": "Department of Literature", "code": "LIT", "faculty": 2},
    ]
    departments = []
    for data in departments_data:
        department, created = Department.objects.get_or_create(
            name=data["name"],
            faculty=faculties[data["faculty"]],
            defaults={
                "slug": slugify(data["name"]),
                "code": data["code"],
                "introduction": fake.paragraph(),
                "details": fake.text(),
            }
        )
        departments.append(department)
    print(f"Created {len(departments)} departments.")
    return departments

# 3. Create Program records
def create_programs(departments):
    programs_data = [
        {"name": "Bachelor of Science in Computer Science", "degree_type": "BS", "department": 0, "duration_years": 4, "total_semesters": 8, "start_year": 2010},
        {"name": "Bachelor of Science in Electrical Engineering", "degree_type": "BS", "department": 1, "duration_years": 4, "total_semesters": 8, "start_year": 2012},
        {"name": "Bachelor of Science in Physics", "degree_type": "BS", "department": 2, "duration_years": 4, "total_semesters": 8, "start_year": 2015},
        {"name": "Bachelor of Science in Chemistry", "degree_type": "BS", "department": 3, "duration_years": 4, "total_semesters": 8, "start_year": 2015},
        {"name": "Bachelor of Arts in Literature", "degree_type": "BA", "department": 4, "duration_years": 4, "total_semesters": 8, "start_year": 2018},
    ]
    programs = []
    for data in programs_data:
        program, created = Program.objects.get_or_create(
            name=data["name"],
            department=departments[data["department"]],
            defaults={
                "degree_type": data["degree_type"],
                "duration_years": data["duration_years"],
                "total_semesters": data["total_semesters"],
                "start_year": data["start_year"],
                "is_active": True,
            }
        )
        programs.append(program)
    print(f"Created {len(programs)} programs.")
    return programs

# 4. Create Semester records for each program
def create_semesters(programs):
    semesters = []
    for program in programs:
        for number in range(1, program.total_semesters + 1):
            semester, created = Semester.objects.get_or_create(
                program=program,
                number=number,
                defaults={
                    "name": f"Semester {number}",
                    "description": fake.paragraph(),
                    "start_time": fixed_date_in_year(2020),  # Fixed for consistency
                    "end_time": fixed_date_in_year(2020),
                    "is_active": number == 1,  # Make first semester active for simplicity
                }
            )
            semesters.append(semester)
    print(f"Created {len(semesters)} semesters.")
    return semesters

# 5. Create AcademicSession records (4 sessions as requested)
def create_academic_sessions():
    sessions_data = [
        {"name": "2021-2025", "start_year": 2021, "end_year": 2025},
        {"name": "2022-2026", "start_year": 2022, "end_year": 2026},
        {"name": "2023-2027", "start_year": 2023, "end_year": 2027},
        {"name": "2024-2029", "start_year": 2024, "end_year": 2029},
    ]
    sessions = []
    for data in sessions_data:
        session, created = AcademicSession.objects.get_or_create(
            name=data["name"],
            defaults={
                "start_year": data["start_year"],
                "end_year": data["end_year"],
                "is_active": True,  # All sessions are current
                "description": fake.paragraph(),
            }
        )
        sessions.append(session)
    print(f"Created {len(sessions)} academic sessions.")
    return sessions

# 6. Create CustomUser and Teacher records (1 HOD + 6 Professors per department)
def create_teachers(departments):
    teachers = []
    for department in departments:
        # Create an HOD for each department
        hod_user = CustomUser.objects.create(
            email=f"hod_{department.code.lower()}@university.com",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_staff=True,
            is_active=True,
        )
        hod_user.set_password("password123")
        hod_user.save()

        hod, created = Teacher.objects.get_or_create(
            user=hod_user,
            department=department,
            defaults={
                "designation": "head_of_department",
                "contact_no": fake.phone_number(),
                "qualification": "PhD in " + department.name.split()[-1],
                "hire_date": fixed_date_in_year(2015),
                "is_active": True,
                "linkedin_url": fake.url(),
                "twitter_url": fake.url(),
                "personal_website": fake.url(),
                "experience": fake.paragraph(),
            }
        )
        teachers.append(hod)

        # Create 6 additional professors per department
        for _ in range(6):
            professor_user = CustomUser.objects.create(
                email=f"prof_{fake.user_name()}@university.com",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_staff=True,
                is_active=True,
            )
            professor_user.set_password("password123")
            professor_user.save()

            professor, created = Teacher.objects.get_or_create(
                user=professor_user,
                department=department,
                defaults={
                    "designation": "professor",
                    "contact_no": fake.phone_number(),
                    "qualification": "PhD in " + department.name.split()[-1],
                    "hire_date": fixed_date_in_year(2015),
                    "is_active": True,
                    "linkedin_url": fake.url(),
                    "twitter_url": fake.url(),
                    "personal_website": fake.url(),
                    "experience": fake.paragraph(),
                }
            )
            teachers.append(professor)
    print(f"Created {len(teachers)} teachers (including HODs).")
    return teachers

# 7. Create Course and CourseOffering records
def create_courses_and_offerings(programs, teachers, semesters, academic_sessions):
    courses_data = [
        {"code": "CS101", "name": "Introduction to Programming", "credits": 3},
        {"code": "CS102", "name": "Data Structures", "credits": 3},
        {"code": "EE101", "name": "Circuit Analysis", "credits": 3},
        {"code": "PHY101", "name": "Mechanics", "credits": 3},
        {"code": "CHEM101", "name": "Organic Chemistry", "credits": 3},
        {"code": "LIT101", "name": "Introduction to Literature", "credits": 3},
    ]
    courses = []
    for data in courses_data:
        course, created = Course.objects.get_or_create(
            code=data["code"],
            defaults={
                "name": data["name"],
                "credits": data["credits"],
                "is_active": True,
                "description": fake.paragraph(),
            }
        )
        courses.append(course)

    # Create CourseOfferings
    course_offerings = []
    offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
    for program in programs:
        dept_teachers = [t for t in teachers if t.department == program.department]
        if not dept_teachers:
            continue
        for semester in semesters:  # Create offerings for all semesters
            if semester.program != program:
                continue
            for course in courses:
                if not course.code.startswith(program.department.code):
                    continue  # Only assign courses that match the department code
                teacher = random.choice(dept_teachers)
                for session in academic_sessions:
                    offering, created = CourseOffering.objects.get_or_create(
                        course=course,
                        teacher=teacher,
                        department=program.department,
                        program=program,
                        academic_session=session,
                        semester=semester,
                        defaults={
                            "is_active": True,
                            "max_capacity": 50,
                            "current_enrollment": 0,
                            "offering_type": random.choice(offering_types),
                        }
                    )
                    course_offerings.append(offering)
    print(f"Created {len(courses)} courses and {len(course_offerings)} course offerings.")
    return courses, course_offerings

# 8. Create Applicant, AcademicQualification, and ExtraCurricularActivity records
def create_applicants_and_related(programs, academic_sessions):
    applicants = []
    students_per_session = 30  # Target ~30 students per session
    total_sessions = len(academic_sessions)  # 4 sessions
    total_applicants = students_per_session * total_sessions  # ~120 applicants
    applicants_per_session = students_per_session  # ~30 applicants per session

    for session in academic_sessions:
        for _ in range(applicants_per_session):
            user = CustomUser.objects.create(
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_active=True,
            )
            user.set_password("password123")
            user.save()

            program = random.choice(programs)
            applicant, created = Applicant.objects.get_or_create(
                user=user,
                faculty=program.department.faculty,
                department=program.department,
                program=program,
                defaults={
                    "status": random.choice(['pending', 'accepted', 'rejected']),
                    "full_name": user.get_full_name(),
                    "religion": fake.word(),
                    "cnic": fake.ssn(),
                    "dob": fixed_date_in_year(2000),  # Fixed for consistency
                    "contact_no": fake.phone_number(),
                    "identification_mark": fake.sentence(),
                    "father_name": fake.name(),
                    "father_occupation": fake.job(),
                    "father_cnic": fake.ssn(),
                    "monthly_income": random.randint(30000, 100000),
                    "relationship": random.choice(['father', 'guardian']),
                    "permanent_address": fake.address(),
                    "declaration": True,
                }
            )
            applicants.append(applicant)

            # Create AcademicQualifications for the applicant
            for _ in range(random.randint(1, 3)):
                AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=random.choice(["Matriculation", "FSc", "Bachelor's"]),
                    passing_year=random.randint(2015, 2023),
                    marks_obtained=random.randint(600, 1000),
                    total_marks=1100,
                    division=random.choice(["1st Division", "2nd Division", "A+"]),
                    subjects=", ".join([fake.word() for _ in range(3)]),
                    board=fake.company(),
                )

            # Create ExtraCurricularActivities for the applicant
            for _ in range(random.randint(0, 2)):
                ExtraCurricularActivity.objects.create(
                    applicant=applicant,
                    activity=fake.sentence(nb_words=3),
                    position=random.choice(["Member", "Captain", "Secretary"]),
                    achievement=fake.sentence(nb_words=5),
                    activity_year=random.randint(2015, 2023),
                )
    print(f"Created {len(applicants)} applicants with related qualifications and activities.")
    return applicants

# 9. Create AdmissionCycle records
def create_admission_cycles(programs, academic_sessions, applicants):
    admission_cycles = []
    for program in programs:
        for session in academic_sessions:
            cycle, created = AdmissionCycle.objects.get_or_create(
                program=program,
                session=session,
                defaults={
                    "application_start": fixed_date_in_year(session.start_year),
                    "application_end": fixed_date_in_year(session.start_year),
                    "is_open": False,  # Set to False since these are past/current sessions
                }
            )
            admission_cycles.append(cycle)
    print(f"Created {len(admission_cycles)} admission cycles.")
    return admission_cycles

# 10. Create Student and StudentEnrollment records
def create_students_and_enrollments(applicants, course_offerings, semesters, academic_sessions):
    students = []
    students_per_session = 30  # Target ~30 students per session
    total_sessions = len(academic_sessions)  # 4 sessions
    applicants_per_session = students_per_session  # ~30 applicants per session

    # Distribute applicants into sessions
    session_applicants = [[] for _ in range(total_sessions)]
    applicant_idx = 0
    for session_idx in range(total_sessions):
        for _ in range(applicants_per_session):
            if applicant_idx < len(applicants):
                session_applicants[session_idx].append(applicants[applicant_idx])
                applicant_idx += 1

    # Create students for each session
    for session_idx, session in enumerate(academic_sessions):
        session_applicant_list = session_applicants[session_idx]
        for applicant in session_applicant_list:
            if applicant.status != 'accepted':
                applicant.status = 'accepted'  # Force accepted to meet student count
                applicant.save()

            # Calculate current semester based on enrollment year and current year
            enrollment_year = session.start_year
            years_elapsed = current_year - enrollment_year
            total_semesters = min(years_elapsed * semesters_per_year, 8)  # Cap at 8 semesters
            current_semester = [s for s in semesters if s.program == applicant.program and s.number == total_semesters][0] if total_semesters > 0 and total_semesters <= 8 else [s for s in semesters if s.program == applicant.program and s.number == 1][0]

            student, created = Student.objects.get_or_create(
                applicant=applicant,
                defaults={
                    "user": applicant.user,
                    "university_roll_no": random.randint(10000, 99999),
                    "college_roll_no": random.randint(1000, 9999),
                    "enrollment_date": fixed_date_in_year(session.start_year),
                    "program": applicant.program,
                    "current_semester": current_semester,
                    "current_status": "active",  # All students are active
                    "emergency_contact": fake.name(),
                    "emergency_phone": fake.phone_number(),
                }
            )
            students.append(student)

            # Create StudentEnrollments
            relevant_offerings = [co for co in course_offerings if co.program == student.program and co.semester == student.current_semester and co.academic_session == session]
            if not relevant_offerings:
                continue
            for _ in range(min(3, len(relevant_offerings))):  # Enroll in up to 3 courses
                course_offering = random.choice(relevant_offerings)
                if course_offering.current_enrollment >= course_offering.max_capacity:
                    continue
                StudentEnrollment.objects.get_or_create(
                    student=student,
                    course_offering=course_offering,
                    defaults={
                        "status": "enrolled",
                    }
                )
                course_offering.current_enrollment += 1
                course_offering.save()
    print(f"Created {len(students)} students with enrollments.")
    return students

# Main function to run the data generation
def main():
    print("Starting fake data generation...")
    
    # Delete old data
    delete_old_data()
    
    # Create Faculties
    faculties = create_faculties()
    
    # Create Departments
    departments = create_departments(faculties)
    
    # Create Programs
    programs = create_programs(departments)
    
    # Create Semesters
    semesters = create_semesters(programs)
    
    # Create Academic Sessions
    academic_sessions = create_academic_sessions()
    
    # Create Teachers
    teachers = create_teachers(departments)
    
    # Create Courses and Course Offerings
    courses, course_offerings = create_courses_and_offerings(programs, teachers, semesters, academic_sessions)
    
    # Create Applicants and related data
    applicants = create_applicants_and_related(programs, academic_sessions)
    
    # Create Admission Cycles
    admission_cycles = create_admission_cycles(programs, academic_sessions, applicants)
    
    # Create Students and Enrollments
    students = create_students_and_enrollments(applicants, course_offerings, semesters, academic_sessions)
    
    print("Fake data generation completed successfully!")

if __name__ == "__main__":
    main()