import os
import django
from faker import Faker
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
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

# # Notice model (for reference)
# class Notice(models.Model):
#     title = models.CharField(max_length=200, help_text="Title of the notice (e.g., 'Exam Schedule Update').")
#     content = models.TextField(help_text="The content of the notice.")
#     created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_notices', help_text="The teacher who created this notice.")
#     created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the notice was created.")
#     is_active = models.BooleanField(default=True, help_text="Check if this notice is currently visible to students.")

#     def __str__(self):
#         return self.title

#     class Meta:
#         verbose_name = "Notice"
#         verbose_name_plural = "Notices"

fake = Faker()

def create_users(num_users=700):  # Increased to accommodate all roles
    users = []
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
    return users

def create_faculties(num_faculties=3):
    faculties = []
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
    return faculties

def create_departments(faculties, num_depts_per_faculty=2):
    departments = []  
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
    return departments

def create_programs(departments, num_programs_per_dept=2):
    programs = []
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
                    duration_years=random.randint(2, 5),
                    total_semesters=random.randint(4, 10),
                    start_year=fake.year(),
                    is_active=True
                )
                programs.append(program)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create program '{name}' for department '{dept.name}': {e}")
                continue
    return programs

def create_semesters(programs, num_semesters_per_program=8):
    semesters = []
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
    return semesters

def create_academic_sessions(num_sessions=3):
    sessions = []
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
    return sessions

def create_admission_cycles(programs, sessions):
    cycles = []
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
    return cycles

def create_applicants(users, faculties, departments, programs, num_applicants_per_program=55):
    applicants = []
    # Track available users globally
    available_users = [user for user in users if not Applicant.objects.filter(user=user).exists() and not hasattr(user, 'teacher_profile') and not hasattr(user, 'student_profile') and not hasattr(user, 'officestaff_profile')]
    for program in programs:
        # Create applicants for each program
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
    return applicants

def create_academic_qualifications(applicants):
    qualifications = []
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
    return qualifications

def create_extra_curricular_activities(applicants):
    activities = []
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
    return activities

def create_teachers(users, departments, num_teachers_per_dept=7):
    teachers = []
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
    return teachers

def create_offices(num_offices=3):
    offices = []
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
    return offices

def create_office_staff(users, offices):
    staff = []
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
    return staff

def create_students(applicants, programs, semesters, min_students_per_program=50):
    students = []
    program_applicants = {program.id: [] for program in programs}
    for applicant in applicants:
        if applicant.status == 'accepted':
            program_applicants[applicant.program.id].append(applicant)
    
    available_users = [user for user in users if not hasattr(user, 'student_profile') and not hasattr(user, 'teacher_profile') and not hasattr(user, 'officestaff_profile') and not Applicant.objects.filter(user=user).exists()]
    
    for program in programs:
        accepted_applicants = program_applicants.get(program.id, [])
        current_student_count = Student.objects.filter(program=program).count()
        needed_students = max(0, min_students_per_program - current_student_count)
        
        # Use accepted applicants
        for applicant in accepted_applicants[:needed_students]:
            if not hasattr(applicant.user, 'student_profile'):
                try:
                    student = Student.objects.create(
                        applicant=applicant,
                        user=applicant.user,
                        university_roll_no=fake.random_int(100000, 999999),
                        college_roll_no=fake.random_int(100000, 999999),
                        enrollment_date=fake.date_this_decade(),
                        program=program,
                        current_semester=random.choice([s for s in semesters if s.program == program]),
                        current_status='active',
                        emergency_contact=fake.name(),
                        emergency_phone=fake.phone_number()[:15]
                    )
                    students.append(student)
                except django.db.utils.IntegrityError as e:
                    print(f"Failed to create student for applicant {applicant.full_name} in program '{program.name}': {e}")
                    continue
        
        # Create additional students if needed
        remaining_needed = max(0, min_students_per_program - (len([s for s in students if s.program == program]) + current_student_count))
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
                    enrollment_date=fake.date_this_decade(),
                    program=program,
                    current_semester=random.choice([s for s in semesters if s.program == program]),
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
    return students

def create_student_semester_enrollments(students, semesters):
    enrollments = []
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
    return enrollments

def create_courses(num_courses=10):
    courses = []
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
    return courses

def create_course_offerings(courses, teachers, departments, programs, sessions, semesters):
    offerings = []
    for course in courses:
        try:
            offering = CourseOffering.objects.create(
                course=course,
                teacher=random.choice(teachers),
                department=random.choice(departments),
                program=random.choice(programs),
                academic_session=random.choice(sessions),
                semester=random.choice(semesters),
                is_active=True,
                current_enrollment=random.randint(10, 50),
                offering_type=random.choice([t[0] for t in CourseOffering.OFFERING_TYPES])
            )
            offerings.append(offering)
        except django.db.utils.IntegrityError as e:
            print(f"Failed to create course offering for course {course.code}: {e}")
            continue
    return offerings

def create_study_materials(offerings, teachers):
    materials = []
    for offering in offerings:
        for _ in range(random.randint(1, 3)):
            try:
                material = StudyMaterial.objects.create(
                    course_offering=offering,
                    title=fake.sentence(),
                    description=fake.text(max_nb_chars=200),
                    file='',
                    uploaded_by=random.choice(teachers),
                    is_active=True
                )
                materials.append(material)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create study material for course offering {offering}: {e}")
                continue
    return materials

def create_assignments(offerings, teachers):
    assignments = []
    for offering in offerings:
        for _ in range(random.randint(1, 2)):
            try:
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    title=fake.sentence(),
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
    return assignments

def create_assignment_submissions(assignments, students, teachers):
    submissions = []
    for assignment in assignments:
        for student in random.sample(students, k=min(len(students), 5)):
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
    return submissions

# def create_notices(offerings, teachers):
    notices = []
    for offering in offerings:
        try:
            notice = Notice.objects.create(
                title=fake.sentence(),
                content=fake.text(max_nb_chars=500),
                created_by=random.choice(teachers),
                is_active=True
            )
            notices.append(notice)
        except django.db.utils.IntegrityError as e:
            print(f"Failed to create notice for course offering {offering}: {e}")
            continue
    return notices

def create_exam_results(offerings, students, teachers):
    results = []
    for offering in offerings:
        for student in random.sample(students, k=min(len(students), 5)):
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
    return results

def create_course_enrollments(enrollments, offerings):
    course_enrollments = []
    for enrollment in enrollments:
        for offering in random.sample(offerings, k=min(len(offerings), 3)):
            try:
                course_enrollment = CourseEnrollment.objects.create(
                    student_semester_enrollment=enrollment,
                    course_offering=offering,
                    status='enrolled'
                )
                course_enrollments.append(course_enrollment)
            except django.db.utils.IntegrityError as e:
                print(f"Failed to create course enrollment for student {enrollment.student.applicant.full_name}: {e}")
                continue
    return course_enrollments

if __name__ == '__main__':
    print("Starting fake data generation...")

    # Clear existing data
    try:
        CustomUser.objects.all().delete()
        Faculty.objects.all().delete()
        Department.objects.all().delete()
        Program.objects.all().delete()
        Semester.objects.all().delete()
        AcademicSession.objects.all().delete()
        AdmissionCycle.objects.all().delete()
        Applicant.objects.all().delete()
        AcademicQualification.objects.all().delete()
        ExtraCurricularActivity.objects.all().delete()
        Teacher.objects.all().delete()
        Office.objects.all().delete()
        OfficeStaff.objects.all().delete()
        Student.objects.all().delete()
        StudentSemesterEnrollment.objects.all().delete()
        Course.objects.all().delete()
        CourseOffering.objects.all().delete()
        StudyMaterial.objects.all().delete()
        Assignment.objects.all().delete()
        AssignmentSubmission.objects.all().delete()
        # Notice.objects.all().delete()
        ExamResult.objects.all().delete()
        CourseEnrollment.objects.all().delete()
        print("Existing data cleared successfully.")
    except Exception as e:
        print(f"Error clearing existing data: {e}")

    # Generate data
    try:
        users = create_users(700)
        print(f"Created {len(users)} users.")
        faculties = create_faculties(3)
        print(f"Created {len(faculties)} faculties.")
        departments = create_departments(faculties, 2)
        print(f"Created {len(departments)} departments.")
        programs = create_programs(departments, 2)
        print(f"Created {len(programs)} programs.")
        semesters = create_semesters(programs, 8)
        print(f"Created {len(semesters)} semesters.")
        sessions = create_academic_sessions(3)
        print(f"Created {len(sessions)} academic sessions.")
        admission_cycles = create_admission_cycles(programs, sessions)
        print(f"Created {len(admission_cycles)} admission cycles.")
        applicants = create_applicants(users, faculties, departments, programs, 55)
        print(f"Created {len(applicants)} applicants.")
        qualifications = create_academic_qualifications(applicants)
        print(f"Created {len(qualifications)} academic qualifications.")
        activities = create_extra_curricular_activities(applicants)
        print(f"Created {len(activities)} extra-curricular activities.")
        teachers = create_teachers(users, departments, 7)
        print(f"Created {len(teachers)} teachers.")
        offices = create_offices(3)
        print(f"Created {len(offices)} offices.")
        office_staff = create_office_staff(users, offices)
        print(f"Created {len(office_staff)} office staff.")
        students = create_students(applicants, programs, semesters, 50)
        print(f"Created {len(students)} students.")
        semester_enrollments = create_student_semester_enrollments(students, semesters)
        print(f"Created {len(semester_enrollments)} semester enrollments.")
        courses = create_courses(10)
        print(f"Created {len(courses)} courses.")
        course_offerings = create_course_offerings(courses, teachers, departments, programs, sessions, semesters)
        print(f"Created {len(course_offerings)} course offerings.")
        study_materials = create_study_materials(course_offerings, teachers)
        print(f"Created {len(study_materials)} study materials.")
        assignments = create_assignments(course_offerings, teachers)
        print(f"Created {len(assignments)} assignments.")
        assignment_submissions = create_assignment_submissions(assignments, students, teachers)
        print(f"Created {len(assignment_submissions)} assignment submissions.")
        # notices = create_notices(course_offerings, teachers)
        # print(f"Created {len(notices)} notices.")
        exam_results = create_exam_results(course_offerings, students, teachers)
        print(f"Created {len(exam_results)} exam results.")
        course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)
        print(f"Created {len(course_enrollments)} course enrollments.")
        print("Fake data generation completed!")
    except Exception as e:
        print(f"Error during data generation: {e}")