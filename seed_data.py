import os
import django
import random
import sys
from datetime import timedelta
from faker import Faker

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')

try:
    django.setup()
    # Import Django modules after setup
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
        email = fake.email()
        while email in existing_emails:
            email = fake.email()
        existing_emails.add(email)
        first_name = fake.first_name()
        last_name = fake.last_name()
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
    for _ in range(count):
        name = fake.company() + " Faculty"
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
        for _ in range(count_per_faculty):
            name = fake.company() + " Department"
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
    degree_types = ['BS', 'MS', 'PhD', 'MPhil']
    for department in departments:
        for _ in range(count_per_department):
            try:
                program = Program.objects.create(
                    department=department,
                    name=fake.catch_phrase() + " Program",
                    degree_type=random.choice(degree_types),
                    duration_years=random.randint(2, 5),
                    total_semesters=random.randint(4, 10),
                    start_year=random.randint(2000, 2020),
                    end_year=None if random.choice([True, False]) else random.randint(2020, 2025),
                    is_active=random.choice([True, False])
                )
                programs.append(program)
            except Exception as e:
                print(f"Error creating program: {e}")
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
                    is_active=random.choice([True, False])
                )
                semesters.append(semester)
            except Exception as e:
                print(f"Error creating semester for program {program.name}: {e}")
    return semesters

def create_fake_academic_sessions(count=5):
    sessions = []
    for i in range(count):
        start_year = 2020 + i
        try:
            session = AcademicSession.objects.create(
                name=f"{start_year}-{start_year+4}",
                start_year=start_year,
                end_year=start_year + 4,
                is_active=(i == count - 1),
                description=fake.text(max_nb_chars=300)
            )
            sessions.append(session)
        except Exception as e:
            print(f"Error creating academic session {start_year}: {e}")
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
                    is_open=random.choice([True, False])
                )
                admission_cycles.append(admission_cycle)
            except Exception as e:
                print(f"Error creating admission cycle for program {program.name}: {e}")
    return admission_cycles

def create_fake_applicants(users, faculties, departments, programs, count=600):
    applicants = []
    available_users = users.copy()
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users for applicants")
            break
        user = random.choice(available_users)
        try:
            applicant = Applicant.objects.create(
                user=user,
                faculty=random.choice(faculties),
                department=random.choice(departments),
                program=random.choice(programs),
                status=random.choice(['pending', 'accepted', 'rejected']),
                applicant_photo=create_fake_image() if random.choice([True, False]) else None,
                full_name=fake.name(),
                religion=fake.word(),
                caste=fake.word() if random.choice([True, False]) else '',
                cnic=fake.ssn(),
                dob=fake.date_of_birth(minimum_age=18, maximum_age=30),
                contact_no=fake.phone_number()[:15],
                identification_mark=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                father_name=fake.name_male(),
                father_occupation=fake.job(),
                father_cnic=fake.ssn() if random.choice([True, False]) else '',
                monthly_income=random.randint(50000, 200000) if random.choice([True, False]) else None,
                relationship=random.choice(['father', 'guardian']),
                permanent_address=fake.address(),
                shift=random.choice(['morning', 'evening']),
                declaration=True
            )
            applicants.append(applicant)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating applicant for user {user.email}: {e}")
    return applicants

def create_fake_academic_qualifications(applicants, count_per_applicant=2):
    qualifications = []
    for applicant in applicants:
        for _ in range(count_per_applicant):
            try:
                qualification = AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=fake.word().capitalize() + " Exam",
                    passing_year=random.randint(2015, 2023),
                    marks_obtained=random.randint(500, 1000),
                    total_marks=1000,
                    division=random.choice(['1st', '2nd', '3rd']),
                    subjects=fake.text(max_nb_chars=100),
                    board=fake.company(),
                    certificate_file=create_fake_image() if random.choice([True, False]) else None
                )
                qualifications.append(qualification)
            except Exception as e:
                print(f"Error creating academic qualification for applicant {applicant.full_name}: {e}")
    return qualifications

def create_fake_extra_curricular_activities(applicants, count_per_applicant=1):
    activities = []
    for applicant in applicants:
        for _ in range(count_per_applicant):
            try:
                activity = ExtraCurricularActivity.objects.create(
                    applicant=applicant,
                    activity=fake.catch_phrase(),
                    position=fake.job() if random.choice([True, False]) else '',
                    achievement=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                    activity_year=random.randint(2015, 2023),
                    certificate_file=create_fake_image() if random.choice([True, False]) else None
                )
                activities.append(activity)
            except Exception as e:
                print(f"Error creating extra-curricular activity for applicant {applicant.full_name}: {e}")
    return activities

def create_fake_teachers(users, departments, count=20):
    teachers = []
    available_users = users.copy()
    count = min(count, len(available_users))
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users available for teachers")
            break
        user = random.choice(available_users)
        try:
            teacher = Teacher.objects.create(
                user=user,
                department=random.choice(departments),
                designation=random.choice(['head_of_department', 'professor']),
                contact_no=fake.phone_number()[:15],
                qualification=fake.catch_phrase() + " Degree",
                hire_date=fake.date_this_decade(),
                is_active=random.choice([True, False]),
                linkedin_url=fake.url() if random.choice([True, False]) else '',
                twitter_url=fake.url() if random.choice([True, False]) else '',
                personal_website=fake.url() if random.choice([True, False]) else '',
                experience=fake.text(max_nb_chars=300)
            )
            teachers.append(teacher)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating teacher for user {user.email}: {e}")
    return teachers

def create_fake_offices(count=3):
    offices = []
    for _ in range(count):
        name = fake.company() + " Office"
        try:
            office = Office.objects.create(
                name=name,
                description=fake.text(max_nb_chars=300),
                image=create_fake_image() if random.choice([True, False]) else None,
                location=fake.address(),
                contact_email=fake.email(),
                contact_phone=fake.phone_number()[:20],
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
    for _ in range(count):
        if not available_users:
            print("Warning: Not enough unique users for office staff")
            break
        user = random.choice(available_users)
        try:
            office_staff = OfficeStaff.objects.create(
                user=user,
                office=random.choice(offices),
                position=fake.job(),
                contact_no=fake.phone_number()[:15] if random.choice([True, False]) else ''
            )
            staff.append(office_staff)
            available_users.remove(user)
        except Exception as e:
            print(f"Error creating office staff for user {user.email}: {e}")
    return staff

def create_fake_courses(count=20):
    courses = []
    for _ in range(count):
        try:
            course = Course.objects.create(
                code=fake.lexify(text="???###").upper(),
                name=fake.catch_phrase() + " Course",
                credits=random.randint(1, 4),
                is_active=True,
                description=fake.text(max_nb_chars=300)
            )
            courses.append(course)
        except Exception as e:
            print(f"Error creating course: {e}")
    for course in courses:
        prereqs = random.sample(courses, random.randint(0, min(2, len(courses) - 1)))
        course.prerequisites.set([c for c in prereqs if c != course])
    return courses

def create_fake_course_offerings(courses, teachers, departments, programs, sessions, semesters, count_per_course=3):
    offerings = []
    offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
    for course in courses:
        for _ in range(count_per_course):
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
                    offering_type=random.choice(offering_types)
                )
                offerings.append(offering)
            except Exception as e:
                print(f"Error creating course offering for course {course.code}: {e}")
    return offerings

def create_fake_study_materials(course_offerings, teachers, count_per_offering=3):
    materials = []
    for offering in course_offerings:
        for _ in range(count_per_offering):
            try:
                material = StudyMaterial.objects.create(
                    course_offering=offering,
                    title=fake.catch_phrase(),
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
    for offering in course_offerings:
        for _ in range(count_per_offering):
            try:
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    title=fake.catch_phrase(),
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
                amount=random.uniform(100.00, 1000.00),
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
                    try:
                        applicant = Applicant.objects.create(
                            user=user,
                            faculty=program.department.faculty,
                            department=program.department,
                            program=program,
                            status='accepted',
                            applicant_photo=create_fake_image() if random.choice([True, False]) else None,
                            full_name=fake.name(),
                            religion=fake.word(),
                            caste=fake.word() if random.choice([True, False]) else '',
                            cnic=fake.ssn(),
                            dob=fake.date_of_birth(minimum_age=18, maximum_age=30),
                            contact_no=fake.phone_number()[:15],
                            identification_mark=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                            father_name=fake.name_male(),
                            father_occupation=fake.job(),
                            father_cnic=fake.ssn() if random.choice([True, False]) else '',
                            monthly_income=random.randint(50000, 200000) if random.choice([True, False]) else None,
                            relationship=random.choice(['father', 'guardian']),
                            permanent_address=fake.address(),
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
                            university_roll_no=random.randint(100000, 999999),
                            college_roll_no=random.randint(1000, 9999) if random.choice([True, False]) else None,
                            enrollment_date=fake.date_this_decade(),
                            graduation_date=None,
                            program=program,
                            current_semester=random.choice(program_semesters),
                            current_status='active',
                            emergency_contact=fake.name(),
                            emergency_phone=fake.phone_number()[:15]
                        )
                        students.append(student)
                        available_applicants.remove(applicant)
                    except Exception as e:
                        print(f"Error creating student for applicant {applicant.full_name}: {e}")
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
                    print(f"Error creating semester enrollment for student {student.applicant.full_name}: {e}")
    return enrollments

def create_fake_course_enrollments(semester_enrollments, course_offerings, count_per_enrollment=3):
    enrollments = []
    for se in semester_enrollments:
        available_offerings = [co for co in course_offerings if co.semester == se.semester]
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
                    print(f"Error creating course enrollment for student {se.student.applicant.full_name}: {e}")
    return enrollments

def create_fake_assignment_submissions(assignments, students, teachers, count_per_assignment=10):
    submissions = []
    for assignment in assignments:
        available_students = random.sample(students, min(count_per_assignment, len(students)))
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
                    print(f"Error creating assignment submission for student {student.applicant.full_name}: {e}")
    return submissions

def create_fake_exam_results(course_offerings, students, teachers, count_per_offering=10):
    results = []
    exam_types = [choice[0] for choice in ExamResult.EXAM_TYPES]
    for offering in course_offerings:
        available_students = random.sample(students, min(count_per_offering, len(students)))
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
                    print(f"Error creating exam result for student {student.applicant.full_name}: {e}")
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