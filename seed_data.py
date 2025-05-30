import os
import django
from faker import Faker
from django.utils import timezone
from datetime import datetime, timedelta
import random
import logging
from django.utils.timezone import get_current_timezone
from django.contrib.auth.models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus360FYP.settings')
django.setup()

from academics.models import Faculty, Department, Program, Semester, Session
from admissions.models import Applicant, AdmissionCycle, Qualification
from faculty_staff.models import Teacher, Office, OfficeStaff
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
from courses.models import Course, CourseOffering, Assignment, AssignmentSubmission, ExamResult, StudyMaterial
from extracurricular.models import Activity

fake = Faker()

def create_users():
    users = User.objects.all()
    if len(users) >= 300:
        logger.info("300 users already exist; skipping user creation.")
        return list(users)
    remaining = 300 - len(users)
    new_users = []
    for _ in range(remaining):
        try:
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name()
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            new_users.append(user)
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
    logger.info(f"Created {len(new_users)} new users.")
    return list(users) + new_users

def create_faculties():
    faculties = Faculty.objects.all()
    if len(faculties) >= 1:
        logger.info("1 faculty already exists; skipping faculty creation.")
        return list(faculties)
    faculties = []
    try:
        faculty = Faculty.objects.create(
            name="Engineering",
            description="Faculty of Engineering",
            established_date=timezone.make_aware(datetime(2000, 1, 1), timezone=get_current_timezone())
        )
        faculties.append(faculty)
    except Exception as e:
        logger.error(f"Failed to create faculty: {str(e)}")
    logger.info(f"Created {len(faculties)} faculties.")
    return faculties

def create_departments(faculties):
    departments = Department.objects.all()
    if len(departments) >= 3:
        logger.info("3 departments already exist; skipping department creation.")
        return list(departments)
    departments = []
    dept_names = ["Computer Science", "Electrical Engineering", "Mechanical Engineering"]
    for name in dept_names:
        try:
            dept = Department.objects.create(
                name=name,
                faculty=faculties[0],
                description=fake.text(max_nb_chars=200),
                head=fake.name(),
                established_date=timezone.make_aware(datetime(2000, 1, 1), timezone=get_current_timezone())
            )
            departments.append(dept)
        except Exception as e:
            logger.error(f"Failed to create department {name}: {str(e)}")
    logger.info(f"Created {len(departments)} departments.")
    return departments

def create_programs(departments):
    programs = Program.objects.all()
    if len(programs) >= 6:
        logger.info("6 programs already exist; skipping program creation.")
        return list(programs)
    programs = []
    program_names = [
        ("BS Computer Science", departments[0]),
        ("BS Software Engineering", departments[0]),
        ("BS Electrical Engineering", departments[1]),
        ("BS Power Engineering", departments[1]),
        ("BS Mechanical Engineering", departments[2]),
        ("BS Mechatronics Engineering", departments[2])
    ]
    for name, dept in program_names:
        try:
            program = Program.objects.create(
                name=name,
                department=dept,
                duration_years=4,
                total_credits=130,
                description=fake.text(max_nb_chars=200)
            )
            programs.append(program)
        except Exception as e:
            logger.error(f"Failed to create program {name}: {str(e)}")
    logger.info(f"Created {len(programs)} programs.")
    return programs

def create_sessions():
    sessions = Session.objects.all()
    if len(sessions) >= 1:
        logger.info("1 session already exists; skipping session creation.")
        return list(sessions)
    sessions = []
    try:
        session = Session.objects.create(
            name="2023-2027",
            start_date=timezone.make_aware(datetime(2023, 9, 1), timezone=get_current_timezone()),
            end_date=timezone.make_aware(datetime(2027, 6, 30), timezone=get_current_timezone())
        )
        sessions.append(session)
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
    logger.info(f"Created {len(sessions)} sessions.")
    return sessions

def create_semesters(programs, sessions):
    semesters = Semester.objects.all()
    if len(semesters) >= 24:
        logger.info("24 semesters already exist; skipping semester creation.")
        return list(semesters)
    semesters = []
    for program in programs:
        for year in range(1, 5):
            for term in ["Fall", "Spring"]:
                try:
                    start_date = timezone.make_aware(
                        datetime(2023 + year - 1, 9 if term == "Fall" else 1, 15),
                        timezone=get_current_timezone()
                    )
                    end_date = timezone.make_aware(
                        datetime(2023 + year - 1, 12 if term == "Fall" else 5, 15),
                        timezone=get_current_timezone()
                    )
                    semester = Semester.objects.create(
                        name=f"{term} {2023 + year - 1}",
                        program=program,
                        session=sessions[0],
                        number=(year - 1) * 2 + (1 if term == "Fall" else 2),
                        start_time=start_date,
                        end_time=end_date
                    )
                    semesters.append(semester)
                except Exception as e:
                    logger.error(f"Failed to create semester for {program.name} {term}: {str(e)}")
    logger.info(f"Created {len(semesters)} semesters.")
    return semesters

def create_admission_cycles(sessions):
    cycles = AdmissionCycle.objects.all()
    if len(cycles) >= 6:
        logger.info("6 admission cycles already exist; skipping cycle creation.")
        return list(cycles)
    cycles = []
    for year in range(2023, 2029):
        try:
            cycle = AdmissionCycle.objects.create(
                name=f"Admission {year}",
                session=sessions[0],
                start_date=timezone.make_aware(datetime(year, 3, 1), timezone=get_current_timezone()),
                end_date=timezone.make_aware(datetime(year, 8, 31), timezone=get_current_timezone())
            )
            cycles.append(cycle)
        except Exception as e:
            logger.error(f"Failed to create admission cycle {year}: {str(e)}")
    logger.info(f"Created {len(cycles)} admission cycles.")
    return cycles

def create_applicants(users, programs, cycles):
    applicants = Applicant.objects.all()
    if len(applicants) >= 48:
        logger.info("48 applicants already exist; skipping applicant creation.")
        return list(applicants)
    applicants = []
    available_users = [u for u in users if not hasattr(u, 'applicant') and not hasattr(u, 'student_profile')]
    for program in programs:
        for _ in range(8):  # 8 applicants per program
            if not available_users:
                logger.warning("No available users for applicants.")
                break
            user = available_users.pop(0)
            try:
                applicant = Applicant.objects.create(
                    user=user,
                    full_name=f"{user.first_name} {user.last_name}",
                    program=program,
                    admission_cycle=cycles[0],
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=25),
                    gender=random.choice(['M', 'F']),
                    nationality="Pakistani",
                    phone_number=f"+923{fake.numerify('#########')}",
                    address=fake.address(),
                    application_status='accepted',
                    application_date=timezone.make_aware(datetime(2023, 6, 1), timezone=get_current_timezone())
                )
                applicants.append(applicant)
            except Exception as e:
                logger.error(f"Failed to create applicant for {user.username}: {str(e)}")
    logger.info(f"Created {len(applicants)} applicants.")
    return applicants

def create_qualifications(applicants):
    qualifications = Qualification.objects.all()
    if len(qualifications) >= 96:
        logger.info("96 qualifications already exist; skipping qualification creation.")
        return list(qualifications)
    qualifications = []
    for applicant in applicants:
        for qual in ["Matriculation", "Intermediate"]:
            try:
                qualification = Qualification.objects.create(
                    applicant=applicant,
                    degree_name=qual,
                    institution_name=fake.company(),
                    board=fake.company_suffix(),
                    marks_obtained=random.randint(700, 1000),
                    total_marks=1100,
                    grade='A',
                    passing_year=2021 if qual == "Matriculation" else 2023
                )
                qualifications.append(qualification)
            except Exception as e:
                logger.error(f"Failed to create qualification for {applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(qualifications)} qualifications.")
    return qualifications

def create_activities(applicants):
    activities = Activity.objects.all()
    if len(activities) >= 43:
        logger.info("43 activities already exist; skipping activity creation.")
        return list(activities)
    activities = []
    for applicant in applicants:
        try:
            activity = Activity.objects.create(
                applicant=applicant,
                activity_type=random.choice(['Sports', 'Debate', 'Volunteer']),
                title=fake.sentence(nb_words=4),
                description=fake.text(max_nb_chars=200),
                start_date=timezone.make_aware(datetime(2022, 1, 1), timezone=get_current_timezone()),
                end_date=timezone.make_aware(datetime(2023, 1, 1), timezone=get_current_timezone())
            )
            activities.append(activity)
        except Exception as e:
            logger.error(f"Failed to create activity for {applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(activities)} activities.")
    return activities

def create_teachers(users, departments):
    teachers = Teacher.objects.all()
    if len(teachers) >= 12:
        logger.info("12 teachers already exist; skipping teacher creation.")
        return list(teachers)
    teachers = []
    available_users = [u for u in users if not hasattr(u, 'applicant') and not hasattr(u, 'student_profile') and not hasattr(u, 'teacher_profile')]
    for dept in departments:
        for _ in range(4):  # 4 teachers per department
            if not available_users:
                logger.warning("No available users for teachers.")
                break
            user = available_users.pop(0)
            try:
                teacher = Teacher.objects.create(
                    user=user,
                    department=dept,
                    designation="Assistant Professor",
                    qualification="PhD",
                    contact_number=f"+923{fake.numerify('#########')}",
                    joining_date=timezone.make_aware(datetime(2020, 1, 1), timezone=get_current_timezone())
                )
                teachers.append(teacher)
            except Exception as e:
                logger.error(f"Failed to create teacher for {user.username}: {str(e)}")
    logger.info(f"Created {len(teachers)} teachers.")
    return teachers

def create_offices(departments):
    offices = Office.objects.all()
    if len(offices) >= 3:
        logger.info("3 offices already exist; skipping office creation.")
        return list(offices)
    offices = []
    for dept in departments:
        try:
            office = Office.objects.create(
                department=dept,
                name=f"{dept.name} Office",
                location=fake.building_number(),
                contact_number=f"+923{fake.numerify('#########')}"
            )
            offices.append(office)
        except Exception as e:
            logger.error(f"Failed to create office for {dept.name}: {str(e)}")
    logger.info(f"Created {len(offices)} offices.")
    return offices

def create_office_staff(users, offices):
    staff = OfficeStaff.objects.all()
    if len(staff) >= 13:
        logger.info("13 office staff already exist; skipping staff creation.")
        return list(staff)
    staff = []
    available_users = [u for u in users if not hasattr(u, 'applicant') and not hasattr(u, 'student_profile') and not hasattr(u, 'teacher_profile') and not hasattr(u, 'office_staff_profile')]
    for office in offices:
        for _ in range(4):  # ~4 staff per office
            if not available_users:
                logger.warning("No available users for office staff.")
                break
            user = available_users.pop(0)
            try:
                staff_member = OfficeStaff.objects.create(
                    user=user,
                    office=office,
                    designation="Clerk",
                    contact_number=f"+923{fake.numerify('#########')}",
                    joining_date=timezone.make_aware(datetime(2020, 1, 1), timezone=get_current_timezone())
                )
                staff.append(staff_member)
            except Exception as e:
                logger.error(f"Failed to create office staff for {user.username}: {str(e)}")
    logger.info(f"Created {len(staff)} office staff.")
    return staff

def create_courses(departments):
    courses = Course.objects.all()
    if len(courses) >= 20:
        logger.info("20 courses already exist; skipping course creation.")
        return list(courses)
    courses = []
    course_names = {
        departments[0]: ["Introduction to Programming", "Data Structures", "Algorithms", "Operating Systems", "Web Development", "Software Engineering", "Artificial Intelligence", "Computer Networks", "Database Systems", "Cybersecurity"],
        departments[1]: ["Circuit Theory", "Electronics", "Signals and Systems", "Control Systems", "Power Systems", "Digital Systems", "Embedded Systems"],
        departments[2]: ["Mechanics", "Thermodynamics", "Fluid Dynamics"]
    }
    for dept in departments:
        for name in course_names.get(dept, []):
            try:
                course = Course.objects.create(
                    name=name,
                    department=dept,
                    code=f"{name[:3].upper()}{random.randint(100, 999)}",
                    credits=3,
                    description=fake.text(max_nb_chars=200)
                )
                courses.append(course)
            except Exception as e:
                logger.error(f"Failed to create course {name}: {str(e)}")
    logger.info(f"Created {len(courses)} courses.")
    return courses

def create_course_offerings(courses, semesters, teachers, programs):
    offerings = CourseOffering.objects.all()
    if len(offerings) >= 94:
        logger.info("94 course offerings already exist; skipping offering creation.")
        return list(offerings)
    offerings = []
    for course in courses:
        program = random.choice([p for p in programs if p.department == course.department])
        spring_2025_semesters = [s for s in semesters if s.program == program and s.number == 4]
        if not spring_2025_semesters:
            continue
        semester = random.choice(spring_2025_semesters)
        try:
            offering = CourseOffering.objects.create(
                course=course,
                semester=semester,
                teacher=random.choice(teachers),
                program=program,
                year=2025,
                section=random.choice(['A', 'B'])
            )
            offerings.append(offering)
        except Exception as e:
            logger.error(f"Failed to create offering for {course.name}: {str(e)}")
    logger.info(f"Created {len(offerings)} course offerings.")
    return offerings

def create_study_materials(course_offerings, teachers):
    materials = StudyMaterial.objects.all()
    if len(materials) >= 141:
        logger.info("141 study materials already exist; skipping material creation.")
        return list(materials)
    materials = []
    for offering in course_offerings:
        for _ in range(random.randint(1, 3)):
            try:
                material = StudyMaterial.objects.create(
                    course_offering=offering,
                    title=fake.sentence(),
                    file='material.pdf',
                    uploaded_by=offering.teacher,
                    upload_date=timezone.make_aware(datetime(2025, random.randint(1, 5), random.randint(1, 15)), timezone=get_current_timezone())
                )
                materials.append(material)
            except Exception as e:
                logger.error(f"Failed to create study material for {offering.course.name}: {str(e)}")
    logger.info(f"Created {len(materials)} study materials.")
    return materials

def create_students(applicants, programs, semesters):
    students = Student.objects.all()
    if len(students) >= 48:
        logger.info("48 students already exist; skipping student creation.")
        return list(students)
    students = []
    spring_2025_semesters = [s for s in semesters if s.number == 4]
    for applicant in applicants:
        program = applicant.program
        applicable_semesters = [s for s in spring_2025_semesters if s.program == program]
        if not applicable_semesters:
            logger.warning(f"No Spring 2025 semester for {program.name}")
            continue
        current_semester = random.choice(applicable_semesters)
        try:
            student = Student.objects.create(
                applicant=applicant,
                user=applicant.user,
                university_roll_no=int(fake.numerify('######')),
                college_roll_no=int(fake.numerify('######')),
                enrollment_date=timezone.make_aware(datetime(2023, 9, 1), timezone=get_current_timezone()),
                program=program,
                current_semester=current_semester,
                current_status='active',
                emergency_contact=f"{fake.first_name()} {fake.last_name()}",
                emergency_phone=f"+923{fake.numerify('#########')}"
            )
            students.append(student)
        except Exception as e:
            logger.error(f"Failed to create student for {applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(students)} students.")
    return students

def create_student_semester_enrollments(students):
    enrollments = StudentSemesterEnrollment.objects.all()
    if len(enrollments) >= 48:
        logger.info("48 semester enrollments already exist; skipping enrollment creation.")
        return list(enrollments)
    enrollments = []
    for student in students:
        try:
            enrollment = StudentSemesterEnrollment.objects.create(
                student=student,
                semester=student.current_semester,
                status='enrolled'
            )
            enrollments.append(enrollment)
        except Exception as e:
            logger.error(f"Failed to create enrollment for {student.applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(enrollments)} semester enrollments.")
    return enrollments

def create_assignments(course_offerings, teachers):
    assignments = Assignment.objects.all()
    if len(assignments) >= 188:
        logger.info("188 assignments already exist; skipping assignment creation.")
        return list(assignments)
    assignments = []
    for offering in course_offerings:
        for _ in range(2):
            try:
                semester_end = offering.semester.end_time
                if not timezone.is_aware(semester_end):
                    semester_end = timezone.make_aware(semester_end, timezone=get_current_timezone())
                due_date = semester_end - timedelta(days=random.randint(1, 30))
                assignment = Assignment.objects.create(
                    course_offering=offering,
                    title=fake.sentence(),
                    description=fake.text(max_nb_chars=300),
                    file='',
                    created_by=offering.teacher,
                    due_date=due_date,
                    total_marks=100,
                    is_active=True
                )
                assignments.append(assignment)
            except Exception as e:
                logger.error(f"Failed to create assignment for {offering.course.name}: {str(e)}")
    logger.info(f"Created {len(assignments)} assignments.")
    return assignments

def create_assignment_submissions(assignments, students):
    submissions = AssignmentSubmission.objects.all()
    if len(submissions) >= 1504:
        logger.info("1504 assignment submissions already exist; skipping submission creation.")
        return list(submissions)
    submissions = []
    for assignment in assignments:
        program_students = [
            s for s in students
            if s.program == assignment.course_offering.program
        ]
        if not program_students:
            logger.warning(f"No students for assignment in {assignment.course_offering.course.name}")
            continue
        for student in random.sample(program_students, min(len(program_students), 8)):
            try:
                due_date = assignment.due_date
                if not timezone.is_aware(due_date):
                    due_date = timezone.make_aware(due_date, timezone=get_current_timezone())
                graded_at = due_date + timedelta(days=random.randint(1, 7))
                if AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
                    continue
                submission = AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=student,
                    file='submission.pdf',
                    marks_obtained=random.randint(50, 100),
                    feedback=fake.text(max_nb_chars=200),
                    graded_by=assignment.created_by,
                    graded_at=graded_at
                )
                submissions.append(submission)
            except Exception as e:
                logger.error(f"Failed to create submission for {student.applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(submissions)} assignment submissions.")
    return submissions

def create_exam_results(course_offerings, students, teachers):
    results = ExamResult.objects.all()
    if len(results) >= 752:
        logger.info("752 exam results already exist; skipping result creation.")
        return list(results)
    results = []
    for offering in course_offerings:
        program_students = [
            s for s in students
            if s.program == offering.program
        ]
        if not program_students:
            logger.warning(f"No students for exam in {offering.course.name}")
            continue
        for student in random.sample(program_students, min(len(program_students), 8)):
            try:
                if ExamResult.objects.filter(course_offering=offering, student=student).exists():
                    continue
                result = ExamResult.objects.create(
                    course_offering=offering,
                    student=student,
                    exam_type='final',
                    total_marks=100,
                    marks_obtained=random.randint(50, 100),
                    graded_by=offering.teacher,
                    remarks=fake.text(max_nb_chars=200)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create exam result for {student.applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(results)} exam results.")
    return results

def create_course_enrollments(semester_enrollments, course_offerings):
    enrollments = CourseEnrollment.objects.all()
    if len(enrollments) >= 180:
        logger.info("180 course enrollments already exist; skipping enrollment creation.")
        return list(enrollments)
    enrollments = []
    for enrollment in semester_enrollments:
        program_offerings = [
            o for o in course_offerings
            if o.program == enrollment.student.program
        ]
        if not program_offerings:
            logger.warning(f"No offerings for {enrollment.student.applicant.full_name} in {enrollment.semester.name}")
            continue
        for offering in random.sample(program_offerings, k=min(len(program_offerings), random.randint(3, 5))):
            try:
                if CourseEnrollment.objects.filter(student_semester_enrollment=enrollment, course_offering=offering).exists():
                    continue
                course_enrollment = CourseEnrollment.objects.create(
                    student_semester_enrollment=enrollment,
                    course_offering=offering,
                    status='enrolled'
                )
                enrollments.append(course_enrollment)
            except Exception as e:
                logger.error(f"Failed to create enrollment for {enrollment.student.applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(enrollments)} course enrollments.")
    return enrollments

# Placeholder for potential additional models
"""
def create_attendance(students, course_offerings):
    # Example: Generate attendance records
    attendances = []
    for offering in course_offerings:
        for student in students:
            try:
                attendance = Attendance.objects.create(
                    student=student,
                    course_offering=offering,
                    date=timezone.make_aware(datetime(2025, random.randint(1, 5), random.randint(1, 15))),
                    status=random.choice(['Present', 'Absent'])
                )
                attendances.append(attendance)
            except Exception as e:
                logger.error(f"Failed to create attendance for {student.applicant.full_name}: {str(e)}")
    logger.info(f"Created {len(attendances)} attendance records.")
    return attendances

def create_timetables(course_offerings):
    # Example: Generate timetable entries
    timetables = []
    for offering in course_offerings:
        try:
            timetable = Timetable.objects.create(
                course_offering=offering,
                day=random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']),
                start_time="09:00",
                end_time="10:30",
                room=fake.building_number()
            )
            timetables.append(timetable)
        except Exception as e:
            logger.error(f"Failed to create timetable for {offering.course.name}: {str(e)}")
    logger.info(f"Created {len(timetables)} timetable entries.")
    return timetables
"""

if __name__ == '__main__':
    logger.info(f"Starting data generation at {datetime.now().strftime('%H:%M %p')} on {datetime.now().strftime('%A, %B %d, %Y')}...")
    logger.info("Using existing data; no deletion performed.")

    try:
        # Load or create data for all models
        users = create_users()
        faculties = create_faculties()
        departments = create_departments(faculties)
        programs = create_programs(departments)
        sessions = create_sessions()
        semesters = create_semesters(programs, sessions)
        admission_cycles = create_admission_cycles(sessions)
        applicants = create_applicants(users, programs, admission_cycles)
        qualifications = create_qualifications(applicants)
        activities = create_activities(applicants)
        teachers = create_teachers(users, departments)
        offices = create_offices(departments)
        office_staff = create_office_staff(users, offices)
        courses = create_courses(departments)
        course_offerings = create_course_offerings(courses, semesters, teachers, programs)
        study_materials = create_study_materials(course_offerings, teachers)
        students = create_students(applicants, programs, semesters)
        semester_enrollments = create_student_semester_enrollments(students)
        assignments = create_assignments(course_offerings, teachers)
        assignment_submissions = create_assignment_submissions(assignments, students)
        exam_results = create_exam_results(course_offerings, students, teachers)
        course_enrollments = create_course_enrollments(semester_enrollments, course_offerings)

        # Uncomment if additional models exist
        # attendance_records = create_attendance(students, course_offerings)
        # timetables = create_timetables(course_offerings)

        logger.info("Data generation completed!")
    except Exception as e:
        logger.error(f"Error during data generation: {str(e)}")