import os
import django
from faker import Faker
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime, timedelta
import random

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

from academics.models import Faculty, Department, Program, Semester
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from faculty_staff.models import Teacher, Office, OfficeStaff
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
from courses.models import Course, CourseOffering, StudyMaterial, Assignment, AssignmentSubmission, ExamResult
from users.models import CustomUser

fake = Faker()

# Current year for semester calculation
CURRENT_YEAR = 2025

def create_users(num_users=700):
    users = CustomUser.objects.all() or []
    if not users:
        for _ in range(num_users):
            email = fake.email()
            while CustomUser.objects.filter(email=email).exists():
                email = fake.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    profile_picture='',
                    info=fake.text(max_nb_chars=200)
                )
                users.append(user)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create user with email {email}: {e}")
                continue
    print(f"Using {len(users)} existing or newly created users.")
    return users

def create_faculties(num_faculties=3):
    faculties = Faculty.objects.all() or []
    if not faculties:
        faculty_names = ['Faculty of Engineering', 'Faculty of Sciences', 'Faculty of Humanities']
        for i in range(min(num_faculties, len(faculty_names))):
            try:
                faculty = Faculty.objects.create(
                    name=faculty_names[i],
                    slug=slugify(faculty_names[i]),
                    description=fake.text(max_nb_chars=300)
                )
                faculties.append(faculty)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create faculty '{faculty_names[i]}': {e}")
                continue
    print(f"Using {len(faculties)} existing or newly created faculties.")
    return faculties

def create_departments(faculties, num_depts_per_faculty=2):
    departments = Department.objects.all() or []
    if not departments:
        dept_names = [
            ('Computer Science', 'CS'), ('Electrical Engineering', 'EE'),
            ('Physics', 'PHY'), ('Mathematics', 'MATH'),
            ('Literature', 'LIT'), ('History', 'HIST')
        ]
        for faculty in faculties:
            for i in range(min(num_depts_per_faculty, len(dept_names))):
                name, code = dept_names[i]
                base_slug = slugify(name)
                slug = f"{slugify(faculty.name)}-{base_slug}"
                counter = 1
                while Department.objects.filter(slug=slug).exists():
                    slug = f"{slugify(faculty.name)}-{base_slug}-{counter}"
                    counter += 1
                try:
                    department = Department.objects.create(
                        faculty=faculty,
                        name=name,
                        slug=slug,
                        code=code,
                        image='',
                        introduction=fake.text(max_nb_chars=200),
                        details=fake.text(max_nb_chars=500)
                    )
                    departments.append(department)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create department '{name}' for faculty '{faculty.name}': {e}")
                    continue
    print(f"Using {len(departments)} existing or newly created departments.")
    return departments

def create_programs(departments, num_programs_per_dept=2):
    programs = Program.objects.all() or []
    if not programs:
        program_names = [
            'Bachelor of Science', 'Master of Science',
            'PhD', 'Bachelor of Arts'
        ]
        for dept in departments:
            for _ in range(num_programs_per_dept):
                name = f"{random.choice(program_names)} in {dept.name}"
                try:
                    program = Program.objects.create(
                        department=dept,
                        name=name,
                        degree_type=random.choice(['BS', 'MS', 'PhD', 'BA']),
                        duration_years=4,
                        total_semesters=8,
                        start_year=fake.year(),
                        is_active=True
                    )
                    programs.append(program)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create program '{name}' for department '{dept.name}': {e}")
                    continue
    print(f"Using {len(programs)} existing or newly created programs.")
    return programs

def create_semesters(programs, num_semesters_per_program=8):
    semesters = Semester.objects.all() or []
    if not semesters:
        for program in programs:
            for i in range(1, min(num_semesters_per_program + 1, program.total_semesters + 1)):
                try:
                    semester = Semester.objects.create(
                        program=program,
                        number=i,
                        name=f"Semester {i}",
                        description=fake.text(max_nb_chars=200),
                        start_time=fake.date_this_year(),
                        end_time=fake.date_this_year(after_today=True),
                        is_active=True
                    )
                    semesters.append(semester)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create semester {i} for program '{program.name}': {e}")
                    continue
    print(f"Using {len(semesters)} existing or newly created semesters.")
    return semesters

def create_academic_sessions(num_sessions=3):
    sessions = AcademicSession.objects.all() or []
    if not sessions:
        for i in range(num_sessions):
            start_year = 2020 + i
            try:
                session = AcademicSession.objects.create(
                    name=f"{start_year}-{start_year + 4}",
                    start_year=start_year,
                    end_year=start_year + 4,
                    is_active=(i == num_sessions - 1),
                    description=fake.text(max_nb_chars=300)
                )
                sessions.append(session)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create academic session '{start_year}-{start_year + 4}': {e}")
                continue
    print(f"Using {len(sessions)} existing or newly created academic sessions.")
    return sessions

def create_admission_cycles(programs, sessions):
    cycles = AdmissionCycle.objects.all() or []
    if not cycles:
        for program in programs:
            for session in sessions:
                try:
                    cycle = AdmissionCycle.objects.create(
                        program=program,
                        session=session,
                        application_start=fake.date_this_year(),
                        application_end=fake.date_this_year(after_today=True),
                        is_open=fake.boolean()
                    )
                    cycles.append(cycle)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create admission cycle for program '{program.name}' and session '{session.name}': {e}")
                    continue
    print(f"Using {len(cycles)} existing or newly created admission cycles.")
    return cycles

def create_applicants(users, faculties, departments, programs, num_applicants_per_program=55):
    applicants = Applicant.objects.all() or []
    if not applicants:
        available_users = [user for user in users if not Applicant.objects.filter(user=user).exists() and not hasattr(user, 'teacher_profile') and not hasattr(user, 'student_profile') and not hasattr(user, 'officestaff_profile')]
        for program in programs:
            for _ in range(num_applicants_per_program):
                if not available_users:
                    print(f"No more available users for applicants in program '{program.name}'.")
                    break
                user = random.choice(available_users)
                try:
                    applicant = Applicant.objects.create(
                        user=user,
                        faculty=program.department.faculty,
                        department=program.department,
                        program=program,
                        status=random.choices(
                            ['pending', 'accepted', 'rejected'],
                            weights=[20, 70, 10],
                            k=1
                        )[0],
                        applicant_photo='',
                        full_name=fake.name(),
                        religion=fake.word(),
                        caste=fake.word(),
                        cnic=fake.numerify('#####-#######-#'),
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=30),
                        contact_no=fake.phone_number()[:15],
                        identification_mark=fake.text(max_nb_chars=100),
                        father_name=fake.name(),
                        father_occupation=fake.job(),
                        father_cnic=fake.numerify('#####-#######-#'),
                        monthly_income=random.randint(20000, 100000),
                        relationship=random.choice(['father', 'guardian']),
                        permanent_address=fake.address(),
                        declaration=True
                    )
                    applicants.append(applicant)
                    available_users.remove(user)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create applicant for user {user.email}: {e}")
                    available_users.remove(user)
                    continue
    print(f"Using {len(applicants)} existing or newly created applicants.")
    return applicants

def create_academic_qualifications(applicants):
    qualifications = AcademicQualification.objects.all() or []
    if not qualifications:
        for applicant in applicants:
            for _ in range(random.randint(1, 3)):
                try:
                    qualification = AcademicQualification.objects.create(
                        applicant=applicant,
                        exam_passed=random.choice(['Matriculation', 'FSc', 'Bachelor']),
                        passing_year=fake.year(),
                        marks_obtained=random.randint(500, 1000),
                        total_marks=1100,
                        division=random.choice(['1st Division', '2nd Division', 'A+']),
                        subjects=fake.text(max_nb_chars=100),
                        board=fake.company(),
                        certificate_file=''
                    )
                    qualifications.append(qualification)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create academic qualification for applicant {applicant.full_name}: {e}")
                    continue
    print(f"Using {len(qualifications)} existing or newly created academic qualifications.")
    return qualifications

def create_extra_curricular_activities(applicants):
    activities = ExtraCurricularActivity.objects.all() or []
    if not activities:
        for applicant in applicants:
            for _ in range(random.randint(0, 2)):
                try:
                    activity = ExtraCurricularActivity.objects.create(
                        applicant=applicant,
                        activity=fake.catch_phrase(),
                        position=random.choice(['Captain', 'Member', 'Secretary', '']),
                        achievement=fake.sentence(),
                        activity_year=fake.year(),
                        certificate_file=''
                    )
                    activities.append(activity)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create extra-curricular activity for applicant {applicant.full_name}: {e}")
                    continue
    print(f"Using {len(activities)} existing or newly created extra-curricular activities.")
    return activities

def create_teachers(users, departments, num_teachers_per_dept=7):
    teachers = Teacher.objects.all() or []
    if not teachers:
        available_users = [user for user in users if not hasattr(user, 'teacher_profile') and not hasattr(user, 'student_profile') and not hasattr(user, 'officestaff_profile')]
        for dept in departments:
            if len(available_users) < num_teachers_per_dept:
                print(f"Warning: Only {len(available_users)} users available for {num_teachers_per_dept} teachers in department '{dept.name}'.")
                num_teachers_per_dept = len(available_users)
            
            if available_users:
                user = random.choice(available_users)
                try:
                    teacher = Teacher.objects.create(
                        user=user,
                        department=dept,
                        designation='head_of_department',
                        contact_no=fake.phone_number()[:15],
                        qualification=fake.text(max_nb_chars=100),
                        hire_date=fake.date_this_decade(),
                        is_active=True,
                        linkedin_url=fake.url(),
                        twitter_url=fake.url(),
                        personal_website=fake.url(),
                        experience=fake.text(max_nb_chars=300)
                    )
                    teachers.append(teacher)
                    available_users.remove(user)
                    print(f"Created head_of_department for {dept.name}")
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create head_of_department for {dept.name} with user {user.email}: {e}")
                    available_users.remove(user)
                    continue
            
            for _ in range(min(6, len(available_users))):
                if not available_users:
                    print(f"No more available users for professors in department '{dept.name}'.")
                    break
                user = random.choice(available_users)
                try:
                    teacher = Teacher.objects.create(
                        user=user,
                        department=dept,
                        designation='professor',
                        contact_no=fake.phone_number()[:15],
                        qualification=fake.text(max_nb_chars=100),
                        hire_date=fake.date_this_decade(),
                        is_active=True,
                        linkedin_url=fake.url(),
                        twitter_url=fake.url(),
                        personal_website=fake.url(),
                        experience=fake.text(max_nb_chars=300)
                    )
                    teachers.append(teacher)
                    available_users.remove(user)
                    print(f"Created professor for {dept.name}")
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create professor for {dept.name} with user {user.email}: {e}")
                    available_users.remove(user)
                    continue
    print(f"Using {len(teachers)} existing or newly created teachers.")
    return teachers

def create_offices(num_offices=3):
    offices = Office.objects.all() or []
    if not offices:
        office_names = ['Registrar Office', 'Admissions Office', 'Finance Office']
        for i in range(min(num_offices, len(office_names))):
            try:
                office = Office.objects.create(
                    name=office_names[i],
                    description=fake.text(max_nb_chars=300),
                    image='',
                    location=fake.address(),
                    contact_email=fake.email(),
                    contact_phone=fake.phone_number()[:20],
                    slug=slugify(office_names[i])
                )
                offices.append(office)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create office '{office_names[i]}': {e}")
                continue
    print(f"Using {len(offices)} existing or newly created offices.")
    return offices

def create_office_staff(users, offices):
    staff = OfficeStaff.objects.all() or []
    if not staff:
        available_users = [user for user in users if not hasattr(user, 'officestaff_profile') and not hasattr(user, 'teacher_profile') and not hasattr(user, 'student_profile')]
        for office in offices:
            for _ in range(random.randint(1, 3)):
                if not available_users:
                    print(f"No more available users for office staff in office '{office.name}'.")
                    break
                user = random.choice(available_users)
                try:
                    office_staff = OfficeStaff.objects.create(
                        user=user,
                        office=office,
                        position=fake.job(),
                        contact_no=fake.phone_number()[:15]
                    )
                    staff.append(office_staff)
                    available_users.remove(user)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create office staff for user {user.email} in office '{office.name}': {e}")
                    available_users.remove(user)
                    continue
    print(f"Using {len(staff)} existing or newly created office staff.")
    return staff

def create_students(applicants, programs, semesters, sessions, min_students_per_program=50):
    students = Student.objects.all() or []
    if not students:
        program_applicants = {program.id: [] for program in programs}
        for applicant in applicants:
            if applicant.status == 'accepted':
                program_applicants[applicant.program.id].append(applicant)
        
        available_users = [user for user in users if not hasattr(user, 'student_profile') and not hasattr(user, 'teacher_profile') and not hasattr(user, 'officestaff_profile') and not Applicant.objects.filter(user=user).exists()]
        
        for program in programs:
            accepted_applicants = program_applicants.get(program.id, [])
            current_student_count = Student.objects.filter(program=program).count()
            needed_students = max(0, min_students_per_program - current_student_count)
            
            if not accepted_applicants:
                continue
            
            # Distribute applicants across sessions
            applicants_per_session = len(accepted_applicants) // len(sessions) if sessions else 0
            for i, session in enumerate(sessions):
                start_idx = i * applicants_per_session
                end_idx = (i + 1) * applicants_per_session if i < len(sessions) - 1 else len(accepted_applicants)
                session_apps = accepted_applicants[start_idx:end_idx]
                
                # Calculate current semester based on years elapsed
                years_elapsed = CURRENT_YEAR - session.start_year + 1
                current_semester_number = min(program.total_semesters, years_elapsed * 2)  # 2 semesters per year
                semester = next((s for s in semesters if s.program == program and s.number == current_semester_number), None)
                if not semester:
                    print(f"No semester {current_semester_number} found for program '{program.name}'. Skipping...")
                    continue
                
                # Fixed enrollment date for the session
                enrollment_date = datetime.strptime(f"{session.start_year}-09-01", "%Y-%m-%d").date()
                
                for applicant in session_apps[:needed_students]:
                    if not hasattr(applicant.user, 'student_profile'):
                        try:
                            student = Student.objects.create(
                                applicant=applicant,
                                user=applicant.user,
                                university_roll_no=fake.random_int(100000, 999999),
                                college_roll_no=fake.random_int(100000, 999999),
                                enrollment_date=enrollment_date,
                                program=program,
                                current_semester=semester,
                                current_status='active',
                                emergency_contact=fake.name(),
                                emergency_phone=fake.phone_number()[:15]
                            )
                            students.append(student)
                        except django.db.utils.IntegrityError as e:
                            print(f"Failed to create student for applicant {applicant.full_name} in program '{program.name}': {e}")
                            continue
                
                # Create additional students if needed
                remaining_needed = max(0, min_students_per_program - len([s for s in students if s.program == program]))
                for _ in range(min(remaining_needed, len(available_users))):
                    if not available_users:
                        print(f"No more available users for additional students in program '{program.name}'.")
                        break
                    user = random.choice(available_users)
                    try:
                        applicant = Applicant.objects.create(
                            user=user,
                            faculty=program.department.faculty,
                            department=program.department,
                            program=program,
                            status='accepted',
                            applicant_photo='',
                            full_name=fake.name(),
                            religion=fake.word(),
                            caste=fake.word(),
                            cnic=fake.numerify('#####-#######-#'),
                            dob=fake.date_of_birth(minimum_age=18, maximum_age=30),
                            contact_no=fake.phone_number()[:15],
                            identification_mark=fake.text(max_nb_chars=100),
                            father_name=fake.name(),
                            father_occupation=fake.job(),
                            father_cnic=fake.numerify('#####-#######-#'),
                            monthly_income=random.randint(20000, 100000),
                            relationship=random.choice(['father', 'guardian']),
                            permanent_address=fake.address(),
                            declaration=True
                        )
                        student = Student.objects.create(
                            applicant=applicant,
                            user=applicant.user,
                            university_roll_no=fake.random_int(100000, 999999),
                            college_roll_no=fake.random_int(100000, 999999),
                            enrollment_date=enrollment_date,
                            program=program,
                            current_semester=semester,
                            current_status='active',
                            emergency_contact=fake.name(),
                            emergency_phone=fake.phone_number()[:15]
                        )
                        students.append(student)
                        available_users.remove(user)
                    except django.db.utils.IntegrityError as e:
                        print(f"Failed to create additional student for program '{program.name}': {e}")
                        available_users.remove(user)
                        continue
    print(f"Using {len(students)} existing or newly created students.")
    return students

def create_student_semester_enrollments(students, semesters):
    enrollments = StudentSemesterEnrollment.objects.all() or []
    if not enrollments:
        for student in students:
            try:
                enrollment = StudentSemesterEnrollment.objects.create(
                    student=student,
                    semester=student.current_semester,
                    status='enrolled'
                )
                enrollments.append(enrollment)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create semester enrollment for student {student.applicant.full_name}: {e}")
                continue
    print(f"Using {len(enrollments)} existing or newly created semester enrollments.")
    return enrollments

def create_courses(num_courses=10):
    courses = Course.objects.all() or []
    if not courses:
        for _ in range(num_courses):
            code = fake.numerify('###')
            counter = 1
            while Course.objects.filter(code=code).exists():
                code = f"{fake.numerify('###')}-{counter}"
                counter += 1
            try:
                course = Course.objects.create(
                    code=code,
                    name=fake.catch_phrase(),
                    credits=random.randint(1, 4),
                    is_active=True,
                    description=fake.text(max_nb_chars=300)
                )
                courses.append(course)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create course with code {code}: {e}")
                continue
    print(f"Using {len(courses)} existing or newly created courses.")
    return courses

def create_course_offerings(courses, teachers, departments, programs, sessions, semesters):
    offerings = CourseOffering.objects.all() or []
    if not offerings:
        for program in programs:
            for session in sessions:
                years_elapsed = CURRENT_YEAR - session.start_year + 1
                current_semester_number = min(program.total_semesters, years_elapsed * 2)
                semester = next((s for s in semesters if s.program == program and s.number == current_semester_number), None)
                if not semester:
                    continue
                
                for _ in range(3):
                    course = random.choice(courses)
                    try:
                        offering = CourseOffering.objects.create(
                            course=course,
                            teacher=random.choice(teachers),
                            department=program.department,
                            program=program,
                            academic_session=session,
                            semester=semester,
                            is_active=True,
                            current_enrollment=0,
                            offering_type=random.choice([t[0] for t in CourseOffering.OFFERING_TYPES])
                        )
                        offerings.append(offering)
                    except django.db.utils.IntegrityError as e:
                        print(f"Failed to create course offering for course {course.code}: {e}")
                        continue
    print(f"Using {len(offerings)} existing or newly created course offerings.")
    return offerings

def create_study_materials(offerings, teachers):
    materials = StudyMaterial.objects.all() or []
    if not materials:
        for offering in offerings:
            for i in range(2):
                try:
                    material = StudyMaterial.objects.create(
                        course_offering=offering,
                        title=f"Material {i+1} for {offering.course.name}",
                        description=fake.text(max_nb_chars=200),
                        file='',
                        uploaded_by=random.choice(teachers),
                        is_active=True
                    )
                    materials.append(material)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create study material for course offering {offering}: {e}")
                    continue
    print(f"Using {len(materials)} existing or newly created study materials.")
    return materials

def create_assignments(offerings, teachers):
    assignments = Assignment.objects.all() or []
    if not assignments:
        for offering in offerings:
            for i in range(2):
                try:
                    assignment = Assignment.objects.create(
                        course_offering=offering,
                        title=f"Assignment {i+1} for {offering.course.name}",
                        description=fake.text(max_nb_chars=300),
                        file='',
                        created_by=random.choice(teachers),
                        due_date=fake.date_time_this_year(tzinfo=timezone.get_current_timezone(), after_now=True),
                        total_marks=100,
                        is_active=True
                    )
                    assignments.append(assignment)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create assignment for course offering {offering}: {e}")
                    continue
    print(f"Using {len(assignments)} existing or newly created assignments.")
    return assignments

def create_assignment_submissions(assignments, students, teachers):
    submissions = AssignmentSubmission.objects.all() or []
    if not submissions:
        for assignment in assignments:
            offering = assignment.course_offering
            session = offering.academic_session
            program = offering.program
            batch_students = [s for s in students if s.program == program and s.enrollment_date == datetime.strptime(f"{session.start_year}-09-01", "%Y-%m-%d").date()]
            
            for student in batch_students:
                try:
                    submission = AssignmentSubmission.objects.create(
                        assignment=assignment,
                        student=student,
                        file='',
                        marks_obtained=random.randint(50, 100),
                        feedback=fake.text(max_nb_chars=200),
                        graded_by=random.choice(teachers),
                        graded_at=fake.date_time_this_year(tzinfo=timezone.get_current_timezone())
                    )
                    submissions.append(submission)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create assignment submission for student {student.applicant.full_name}: {e}")
                    continue
    print(f"Using {len(submissions)} existing or newly created assignment submissions.")
    return submissions

def create_exam_results(offerings, students, teachers):
    results = ExamResult.objects.all() or []
    if not results:
        for offering in offerings:
            session = offering.academic_session
            program = offering.program
            batch_students = [s for s in students if s.program == program and s.enrollment_date == datetime.strptime(f"{session.start_year}-09-01", "%Y-%m-%d").date()]
            
            for student in batch_students:
                try:
                    result = ExamResult.objects.create(
                        course_offering=offering,
                        student=student,
                        exam_type=random.choice([t[0] for t in ExamResult.EXAM_TYPES]),
                        total_marks=100,
                        marks_obtained=random.randint(50, 100),
                        graded_by=random.choice(teachers),
                        remarks=fake.text(max_nb_chars=200)
                    )
                    results.append(result)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create exam result for student {student.applicant.full_name}: {e}")
                    continue
    print(f"Using {len(results)} existing or newly created exam results.")
    return results

def create_course_enrollments(enrollments, offerings):
    course_enrollments = CourseEnrollment.objects.all() or []
    if not course_enrollments:
        for enrollment in enrollments:
            student = enrollment.student
            session = next(s for s in sessions if student.enrollment_date == datetime.strptime(f"{s.start_year}-09-01", "%Y-%m-%d").date())
            program = student.program
            relevant_offerings = [o for o in offerings if o.academic_session == session and o.program == program]
            for offering in relevant_offerings:
                try:
                    course_enrollment = CourseEnrollment.objects.create(
                        student_semester_enrollment=enrollment,
                        course_offering=offering,
                        status='enrolled'
                    )
                    course_enrollments.append(course_enrollment)
                    offering.current_enrollment += 1
                    offering.save()
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create course enrollment for student {enrollment.student.applicant.full_name}: {e}")
                    continue
    print(f"Using {len(course_enrollments)} existing or newly created course enrollments.")
    return course_enrollments

if __name__ == '__main__':
    print("Starting fake data generation...")

    try:
        Student.objects.all().delete()
        StudentSemesterEnrollment.objects.all().delete()
        CourseEnrollment.objects.all().delete()
        CourseOffering.objects.all().delete()
        StudyMaterial.objects.all().delete()
        Assignment.objects.all().delete()
        AssignmentSubmission.objects.all().delete()
        ExamResult.objects.all().delete()
        print("Existing student and course-related data cleared successfully.")
    except Exception as e:
        print(f"Error clearing existing data: {e}")

    try:
        users = create_users(700)
        faculties = create_faculties(3)
        departments = create_departments(faculties, 2)
        programs = create_programs(departments, 2)
        semesters = create_semesters(programs, 8)
        sessions = create_academic_sessions(3)
        admission_cycles = create_admission_cycles(programs, sessions)
        applicants = create_applicants(users, faculties, departments, programs, 55)
        qualifications = create_academic_qualifications(applicants)
        activities = create_extra_curricular_activities(applicants)
        teachers = create_teachers(users, departments, 7)
        offices = create_offices(3)
        office_staff = create_office_staff(users, offices)
        students = create_students(applicants, programs, semesters, sessions, 50)
        semester_enrollments = create_student_semester_enrollments(students, semesters)
        courses = create_courses(10)
        course_offerings = create_course_offerings(courses, teachers, departments, programs, sessions, semesters)
        study_materials = create_study_materials(course_offerings, teachers)
        assignments = create_assignments(course_offerings, teachers)
        assignment_submissions = create_assignment_submissions(assignments, students, teachers)
        exam_results = create_exam_results(course_offerings, students, teachers)
        course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)
        print("Fake data generation completed!")
    except Exception as e:
        print(f"Error during data generation: {e}")  