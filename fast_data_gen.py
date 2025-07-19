import os
import django
import random
from datetime import datetime, timedelta
from faker import Faker
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.db import transaction

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

# Import models
from users.models import CustomUser
from academics.models import Faculty, Department, Program, Semester
from admissions.models import Applicant, AdmissionCycle, AcademicSession
from faculty_staff.models import Teacher, TeacherDetails
from courses.models import Course, CourseOffering, Venue, TimetableSlot, Attendance, Assignment, AssignmentSubmission, ExamResult
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment

# Initialize Faker
fake = Faker()

# Constants
NUM_FACULTIES = 2
NUM_DEPARTMENTS_PER_FACULTY = 2
NUM_PROGRAMS_PER_DEPARTMENT = 2
NUM_COURSES_PER_DEPARTMENT = 5
NUM_TEACHERS_PER_DEPARTMENT = 3
NUM_STUDENTS_PER_PROGRAM = 5
NUM_OFFICES = 1
NUM_OFFICE_STAFF = 2

def create_fake_image():
    """Create a dummy image file for testing."""
    return SimpleUploadedFile(
        name=f"fake_image_{uuid.uuid4()}.jpg",
        content=b'fake_image_content',
        content_type='image/jpeg'
    )

def create_fake_file():
    """Create a dummy file for testing."""
    return SimpleUploadedFile(
        name=f"fake_file_{uuid.uuid4()}.pdf",
        content=b'fake_file_content',
        content_type='application/pdf'
    )

def delete_existing_data():
    """Delete all existing data from the database."""
    models = [
        CourseEnrollment, StudentSemesterEnrollment, Student, 
        Attendance, ExamResult, AssignmentSubmission, Assignment, 
        TimetableSlot, CourseOffering, Course, 
        TeacherDetails, Teacher, AdmissionCycle, 
        Applicant, Semester, AcademicSession, Program, 
        Department, Faculty, CustomUser
    ]
    
    for model in models:
        count = model.objects.count()
        model.objects.all().delete()
        print(f"Deleted {count} {model.__name__} records")

def create_users():
    """Create admin, teacher, and student users."""
    users = []
    
    # Create admin user
    admin = CustomUser.objects.create_superuser(
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        password='admin123'
    )
    users.append(admin)
    print("Created admin user")
    
    # Create teacher users
    for i in range(1, NUM_TEACHERS_PER_DEPARTMENT * NUM_DEPARTMENTS_PER_FACULTY * NUM_FACULTIES + 1):
        user = CustomUser.objects.create_user(
            email=f'teacher{i}@example.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            password='teacher123',
            is_staff=True
        )
        users.append(user)
    print(f"Created {len(users) - 1} teacher users")
    
    # Create student users
    num_students = NUM_STUDENTS_PER_PROGRAM * NUM_PROGRAMS_PER_DEPARTMENT * NUM_DEPARTMENTS_PER_FACULTY * NUM_FACULTIES
    for i in range(1, num_students + 1):
        user = CustomUser.objects.create_user(
            email=f'student{i}@example.com',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            password='student123'
        )
        users.append(user)
    print(f"Created {num_students} student users")
    
    return users

def create_academic_structures():
    """Create faculties, departments, and programs."""
    faculties = []
    departments = []
    programs = []
    
    # Create faculties
    for i in range(1, NUM_FACULTIES + 1):
        faculty = Faculty.objects.create(
            name=f'Faculty of {fake.word().capitalize()} Sciences',
            slug=f'faculty-{i}',
            description=fake.text()
        )
        faculties.append(faculty)
        
        # Create departments
        for j in range(1, NUM_DEPARTMENTS_PER_FACULTY + 1):
            dept_name = f'Department of {fake.word().capitalize()}'
            department = Department.objects.create(
                faculty=faculty,
                name=dept_name,
                slug=f'dept-{i}-{j}',
                code=f'DEPT{i}{j}'
            )
            departments.append(department)
            
            # Create programs
            for k in range(1, NUM_PROGRAMS_PER_DEPARTMENT + 1):
                program_type = 'BS' if k % 2 == 0 else 'MS'
                program = Program.objects.create(
                    department=department,
                    name=f'{program_type} in {dept_name.split()[-1]}',
                    degree_type=program_type,
                    duration_years=4 if program_type == 'BS' else 2,
                    total_semesters=8 if program_type == 'BS' else 4,
                    start_year=2020,
                    is_active=True
                )
                programs.append(program)
    
    print(f"Created {len(faculties)} faculties, {len(departments)} departments, {len(programs)} programs")
    return faculties, departments, programs

def create_academic_sessions():
    """Create academic sessions."""
    sessions = []
    current_year = datetime.now().year
    
    for year in range(current_year - 1, current_year + 1):
        session = AcademicSession.objects.create(
            name=f"{year}-{year+1}",
            start_year=year,
            end_year=year+1,
            is_active=(year == current_year),
            description=f"Academic year {year}-{year+1}"
        )
        sessions.append(session)
    
    print(f"Created {len(sessions)} academic sessions")
    return sessions

def create_semesters(programs, sessions):
    """Create semesters for programs and sessions."""
    semesters = []
    
    for program in programs:
        for session in sessions:
            for sem_num in range(1, program.total_semesters + 1):
                semester = Semester.objects.create(
                    program=program,
                    session=session,
                    number=sem_num,
                    name=f"Semester {sem_num}",
                    start_time=datetime(session.start_year, 1 if sem_num % 2 == 1 else 7, 1),
                    end_time=datetime(session.start_year, 6 if sem_num % 2 == 1 else 12, 30),
                    is_active=(sem_num == program.total_semesters and session.is_active)
                )
                semesters.append(semester)
    
    print(f"Created {len(semesters)} semesters")
    return semesters

def create_teachers(users, departments):
    """Create teacher profiles."""
    teachers = []
    teacher_users = [u for u in users if u.is_staff and u.email != 'admin@example.com']
    
    for i, user in enumerate(teacher_users):
        dept = departments[i % len(departments)]
        teacher = Teacher.objects.create(
            user=user,
            department=dept,
            designation='Professor' if i % 3 == 0 else 'Assistant Professor',
            contact_no=fake.phone_number()[:15],
            qualification='PhD' if i % 2 == 0 else 'MS',
            hire_date=fake.date_this_decade(),
            is_active=True
        )
        
        # Create teacher details
        TeacherDetails.objects.create(
            teacher=teacher,
            employment_type=random.choice(['permanent', 'visitor', 'contract']),
            status='available',
            salary_per_lecture=random.randint(2000, 5000),
            fixed_salary=random.randint(50000, 150000)
        )
        
        teachers.append(teacher)
    
    print(f"Created {len(teachers)} teacher profiles")
    return teachers

def create_courses(departments):
    """Create courses."""
    courses = []
    
    for dept in departments:
        for i in range(1, NUM_COURSES_PER_DEPARTMENT + 1):
            course = Course.objects.create(
                code=f"{dept.code}{100 + i}",
                name=f"Course {i} - {fake.word().capitalize()}",
                credits=random.choice([2, 3, 4]),
                lab_work=random.choice([0, 1]),
                is_active=True,
                description=fake.text()
            )
            courses.append(course)
    
    print(f"Created {len(courses)} courses")
    return courses

def create_course_offerings(courses, semesters, teachers):
    """Create course offerings."""
    offerings = []
    
    for semester in semesters:
        # Get courses from the same department as the program
        dept_courses = [c for c in courses if c.code.startswith(semester.program.department.code)]
        
        # Offer 3-5 courses per semester
        for course in random.sample(dept_courses, min(5, len(dept_courses))):
            # Find a teacher from the same department
            dept_teachers = [t for t in teachers if t.department == semester.program.department]
            
            if not dept_teachers:
                continue
                
            offering = CourseOffering.objects.create(
                course=course,
                teacher=random.choice(dept_teachers),
                department=semester.program.department,
                program=semester.program,
                academic_session=semester.session,
                semester=semester,
                is_active=True,
                current_enrollment=0,
                shift=random.choice(['morning', 'evening']),
                offering_type='core' if random.random() > 0.5 else 'elective'
            )
            offerings.append(offering)
    
    print(f"Created {len(offerings)} course offerings")
    return offerings

def create_students(users, programs, sessions):
    """Create student profiles."""
    students = []
    student_users = [u for u in users if not u.is_staff]
    user_index = 0
    
    for program in programs:
        # Get active session
        active_session = next((s for s in sessions if s.is_active), None)
        if not active_session:
            continue
            
        # Create students for this program
        for _ in range(NUM_STUDENTS_PER_PROGRAM):
            if user_index >= len(student_users):
                break
                
            user = student_users[user_index]
            user_index += 1
            
            # Create applicant
            applicant = Applicant.objects.create(
                user=user,
                session=active_session,
                faculty=program.department.faculty,
                department=program.department,
                program=program,
                status='accepted',
                full_name=f"{user.first_name} {user.last_name}",
                cnic=fake.unique.random_number(digits=13, fix_len=True),
                dob=fake.date_of_birth(minimum_age=18, maximum_age=25),
                contact_no=fake.phone_number()[:15],
                father_name=fake.name_male(),
                father_occupation=fake.job(),
                permanent_address=fake.address(),
                shift=random.choice(['morning', 'evening']),
                declaration=True
            )
            
            # Create student with enrollment date as January 1st of the session start year
            enrollment_date = datetime(active_session.start_year, 1, 1).strftime('%Y-%m-%d')
            student = Student.objects.create(
                applicant=applicant,
                user=user,
                program=program,
                university_roll_no=fake.unique.random_number(digits=8, fix_len=True),
                college_roll_no=fake.unique.random_number(digits=6, fix_len=True),
                enrollment_date=enrollment_date,
                current_status='active'
            )
            students.append(student)
    
    print(f"Created {len(students)} student profiles")
    return students

def create_enrollments(students, semesters, course_offerings):
    """Create semester and course enrollments."""
    semester_enrollments = []
    course_enrollments = []
    
    for student in students:
        # Get active semester for student's program
        program_semesters = [s for s in semesters 
                           if s.program == student.program and s.session.is_active]
        
        if not program_semesters:
            continue
            
        # Enroll in the latest semester
        semester = max(program_semesters, key=lambda x: x.number)
        
        # Create semester enrollment
        sem_enrollment = StudentSemesterEnrollment.objects.create(
            student=student,
            semester=semester,
            status='enrolled'
        )
        semester_enrollments.append(sem_enrollment)
        
        # Enroll in courses for this semester
        semester_offerings = [o for o in course_offerings 
                            if o.semester == semester]
        
        for offering in semester_offerings[:4]:  # Enroll in up to 4 courses
            enrollment = CourseEnrollment.objects.create(
                student_semester_enrollment=sem_enrollment,
                course_offering=offering,
                status='enrolled'
            )
            course_enrollments.append(enrollment)
            
            # Update current enrollment count
            offering.current_enrollment += 1
            offering.save()
            
            # Create attendance
            for _ in range(5):  # 5 attendance records per course
                Attendance.objects.create(
                    student=student,
                    course_offering=offering,
                    date=fake.date_between(
                        start_date=semester.start_time.date() if hasattr(semester.start_time, 'date') else semester.start_time,
                        end_date=min(semester.end_time.date() if hasattr(semester.end_time, 'date') else semester.end_time, 
                                  timezone.now().date())
                    ),
                    status=random.choice(['present', 'absent', 'late']),
                    recorded_by=offering.teacher
                )
            
            # Create assignment with submission
            assignment = Assignment.objects.create(
                course_offering=offering,
                teacher=offering.teacher,
                title=f"Assignment {fake.word().capitalize()}",
                description=fake.text(),
                due_date=timezone.now() + timedelta(days=7),
                max_points=100
            )
            
            # Create submission
            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=student,
                content=fake.text(),
                submitted_at=timezone.now(),
                marks_obtained=random.randint(50, 100),
                feedback=fake.sentence(),
                graded_by=offering.teacher
            )
            
            # Create exam result
            ExamResult.objects.create(
                course_offering=offering,
                student=student,
                midterm_obtained=random.randint(15, 25),
                midterm_total=25,
                final_obtained=random.randint(30, 50),
                final_total=50,
                sessional_obtained=random.randint(10, 25),
                sessional_total=25,
                project_obtained=random.randint(0, 10),
                project_total=10,
                practical_obtained=random.randint(0, 15),
                practical_total=15,
                graded_by=offering.teacher
            )
    
    print(f"Created {len(semester_enrollments)} semester enrollments and {len(course_enrollments)} course enrollments")
    return semester_enrollments, course_enrollments

def create_venues(departments):
    """Create venues."""
    venues = []
    
    for dept in departments:
        for i in range(1, 4):  # 3 venues per department
            venue = Venue.objects.create(
                name=f"{dept.code}-{i}",
                department=dept,
                capacity=random.randint(30, 100),
                is_active=True
            )
            venues.append(venue)
    
    print(f"Created {len(venues)} venues")
    return venues

def create_timetable_slots(course_offerings, venues):
    """Create timetable slots, skipping any that already exist."""
    slots = []
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    created_count = 0
    skipped_count = 0
    
    for offering in course_offerings:
        # Create 1-2 slots per offering
        for _ in range(random.randint(1, 2)):
            # Find a venue in the same department
            dept_venues = [v for v in venues if v.department == offering.department]
            if not dept_venues:
                continue
                
            day = random.choice(days)
            venue = random.choice(dept_venues)
            start_hour = random.randint(8, 16)
            start_time = f"{start_hour:02d}:00:00"
            end_time = f"{start_hour + 1:02d}:00:00"  # 1-hour slots
            
            try:
                # Check if slot already exists
                if TimetableSlot.objects.filter(
                    course_offering=offering,
                    day=day,
                    start_time=start_time,
                    venue=venue
                ).exists():
                    skipped_count += 1
                    continue
                    
                slot = TimetableSlot.objects.create(
                    course_offering=offering,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    venue=venue
                )
                slots.append(slot)
                created_count += 1
                
            except IntegrityError as e:
                skipped_count += 1
                continue
    
    print(f"Created {created_count} timetable slots, skipped {skipped_count} existing slots")
    
    print(f"Created {len(slots)} timetable slots")
    return slots

def create_admission_cycles(programs, sessions):
    """Create admission cycles."""
    cycles = []
    
    for program in programs:
        for session in sessions:
            # Only create cycles for current and future years
            if session.end_year < datetime.now().year:
                continue
                
            cycle = AdmissionCycle.objects.create(
                program=program,
                session=session,
                application_start=datetime(session.start_year - 1, 11, 1),
                application_end=datetime(session.start_year, 2, 28),
                is_open=(session.is_active and datetime.now().month in [11, 12, 1, 2])
            )
            cycles.append(cycle)
    
    print(f"Created {len(cycles)} admission cycles")
    return cycles

def main():
    """Main function to generate all data."""
    print("Starting data generation...")
    start_time = timezone.now()
    
    try:
        # Delete existing data
        delete_existing_data()
        
        # Create users
        users = create_users()
        
        # Create academic structures
        faculties, departments, programs = create_academic_structures()
        
        # Create academic sessions
        sessions = create_academic_sessions()
        
        # Create semesters
        semesters = create_semesters(programs, sessions)
        
        # Create teachers
        teachers = create_teachers(users, departments)
        
        # Create courses
        courses = create_courses(departments)
        
        # Create course offerings
        course_offerings = create_course_offerings(courses, semesters, teachers)
        
        # Create students
        students = create_students(users, programs, sessions)
        
        # Create enrollments and academic records
        semester_enrollments, course_enrollments = create_enrollments(
            students, semesters, course_offerings
        )
        
        # Create venues
        venues = create_venues(departments)
        
        # Create timetable slots
        timetable_slots = create_timetable_slots(course_offerings, venues)
        
        # Create admission cycles
        admission_cycles = create_admission_cycles(programs, sessions)
        
        print("\nData generation completed successfully!")
        print(f"Total time: {(timezone.now() - start_time).total_seconds():.2f} seconds")
        
        # Print summary
        print("\nSummary:")
        print(f"- {CustomUser.objects.count()} users")
        print(f"- {Faculty.objects.count()} faculties")
        print(f"- {Department.objects.count()} departments")
        print(f"- {Program.objects.count()} programs")
        print(f"- {AcademicSession.objects.count()} sessions")
        print(f"- {Semester.objects.count()} semesters")
        print(f"- {Teacher.objects.count()} teachers")
        print(f"- {Course.objects.count()} courses")
        print(f"- {CourseOffering.objects.count()} course offerings")
        print(f"- {Student.objects.count()} students")
        print(f"- {StudentSemesterEnrollment.objects.count()} semester enrollments")
        print(f"- {CourseEnrollment.objects.count()} course enrollments")
        print(f"- {Attendance.objects.count()} attendance records")
        print(f"- {Assignment.objects.count()} assignments")
        print(f"- {ExamResult.objects.count()} exam results")
        print(f"- {Venue.objects.count()} venues")
        print(f"- {TimetableSlot.objects.count()} timetable slots")
        print(f"- {AdmissionCycle.objects.count()} admission cycles")
        
    except Exception as e:
        print(f"Error during data generation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
