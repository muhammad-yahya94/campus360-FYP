import random
import queue
import threading
import multiprocessing
from datetime import datetime, timedelta, date, time
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from faker import Faker
import PIL.Image
import io
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import your models (adjust based on your project structure)
from myapp.models import (
    Faculty, Session, Course, User, Department, Program, Semester, AdmissionCycle,
    Venue, Teacher, Applicant, CourseOffering, TimetableSlot, StudyMaterial,
    Assignment, Student, StudentSemesterEnrollment, CourseEnrollment,
    AssignmentSubmission, ExamResult, Attendance
)

fake = Faker()
logging.basicConfig(level=logging.INFO)

def create_fake_image():
    image = PIL.Image.new('RGB', (100, 100), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), f"fake_image_{fake.uuid4()}.png")

def worker_init():
    from django import setup
    setup()

def threaded_create(model, objects_queue, lock, model_name):
    while True:
        try:
            obj_data = objects_queue.get_nowait()
            with transaction.atomic():
                with lock:
                    try:
                        model.objects.create(**obj_data)
                    except Exception as e:
                        print(f"Error creating {model_name}: {e}")
        except queue.Empty:
            break
        except Exception as e:
            print(f"Error in threaded {model_name} creation: {e}")

def create_fake_semesters(programs, sessions, result_dict=None, key=None):
    worker_init()
    existing_semesters = Semester.objects.count()
    session_data = {
        '2021-2025': 8, '2022-2026': 8, '2023-2027': 8, '2024-2028': 8,
        '2023-2025': 4, '2024-2026': 4
    }
    expected_semesters = sum(session_data.get(s.name, 2) for s in sessions for p in programs)
    if existing_semesters >= expected_semesters:
        print(f"Skipping semester creation: {existing_semesters} semesters already exist")
        result = list(Semester.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    semesters_created = 0
    semesters = []

    for program in programs:
        available_sessions = [s for s in sessions if (
            (program.degree_type == 'BS' and s.name in ['2021-2025', '2022-2026', '2023-2027', '2024-2028']) or
            (program.degree_type == 'MS' and s.name in ['2023-2025', '2024-2026'])
        )]
        for session in available_sessions:
            semester_count = session_data.get(session.name, 2)
            session_start_year = int(session.name.split('-')[0])
            for i in range(1, semester_count + 1):
                if not Semester.objects.filter(program=program, session=session, number=i).exists():
                    try:
                        months_offset = (i - 1) * 6
                        semester_start = date(session_start_year, 1, 1) + timedelta(days=int(months_offset * 30.42))
                        semester_end = semester_start + timedelta(days=180)
                        semester = Semester.objects.create(
                            program=program,
                            session=session,
                            number=i,
                            name=f"Semester {i}",
                            start_time=semester_start,
                            end_time=semester_end,
                            is_active=(i == 1 and session.is_active),
                            description=fake.text(max_nb_chars=200)
                        )
                        semesters_created += 1
                        semesters.append(semester)
                    except Exception as e:
                        print(f"Error creating semester {i} for {program.name}: {e}")
                        continue

    print(f"Created {semesters_created} new semesters")
    if result_dict is not None and key is not None:
        result_dict[key] = semesters
    return semesters

def create_fake_assignment_submissions(assignments, students, result_dict=None, key=None):
    worker_init()
    existing_submissions = AssignmentSubmission.objects.count()
    students = list(Student.objects.all())  # Fetch directly from database
    expected_submissions = sum(min(10, len(students)) for _ in assignments)
    if existing_submissions >= expected_submissions:
        print(f"Skipping assignment submission creation: {existing_submissions} submissions already exist")
        result = list(AssignmentSubmission.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    submissions = []
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for assignment in assignments:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=assignment.course_offering).exists()]
            existing_students = set(AssignmentSubmission.objects.filter(assignment=assignment).values_list('student__id', flat=True))
            available_students = [s for s in relevant_students if s.id not in existing_students]
            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                try:
                    submit_offset_days = random.randint(0, 5)
                    submitted_at = assignment.due_date - timedelta(days=submit_offset_days)
                    semester_start = assignment.course_offering.semester.start_time
                    if isinstance(semester_start, date) and not isinstance(semester_start, datetime):
                        semester_start = datetime.combine(semester_start, time(0, 0))
                    submitted_at = max(submitted_at, semester_start)
                    if not timezone.is_aware(submitted_at):
                        submitted_at = timezone.make_aware(submitted_at)
                    objects_queue.put({
                        'assignment': assignment,
                        'student': student,
                        'file': create_fake_image() if random.choice([True, False]) else None,
                        'submitted_at': submitted_at,
                        'marks': random.randint(0, assignment.max_points) if random.choice([True, False]) else None,
                        'feedback': fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None,
                        'graded_by': assignment.teacher if random.choice([True, False]) else None
                    })
                except Exception as e:
                    print(f"Error queuing submission for {student.applicant.full_name} on {assignment.title}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing submissions for {assignment.title}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(AssignmentSubmission, objects_queue, lock, 'assignment submission'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in assignment submission creation threads: {e}")

    try:
        submissions = list(AssignmentSubmission.objects.all())
        print(f"Created {len(submissions) - existing_submissions} new assignment submissions")
        if result_dict is not None and key is not None:
            result_dict[key] = submissions
    except Exception as e:
        print(f"Error retrieving submissions: {e}")
        submissions = []
    return submissions

def create_fake_exam_results(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_results = ExamResult.objects.count()
    students = list(Student.objects.all())  # Fetch directly from database
    expected_results = sum(min(10, len(students)) for _ in offerings)
    if existing_results >= expected_results:
        print(f"Skipping exam result creation: {existing_results} results already exist")
        result = list(ExamResult.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    results = []
    exam_types = ['Midterm', 'Final', 'Test', 'Project', 'Practical']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=offering).exists()]
            existing_students = set(ExamResult.objects.filter(course_offering=offering).values_list('student__id', flat=True))
            available_students = [s for s in relevant_students if s.id not in existing_students]
            selected_students = random.sample(available_students, min(10, len(available_students)))
            for student in selected_students:
                exam_type = random.choice(exam_types)
                if not ExamResult.objects.filter(course_offering=offering, student=student, exam_type=exam_type).exists():
                    try:
                        total_marks = random.choice([50, 100, 200])
                        objects_queue.put({
                            'course_offering': offering,
                            'student': student,
                            'exam_type': exam_type,
                            'total_marks': total_marks,
                            'marks_obtained': random.randint(int(total_marks * 0.6), total_marks),
                            'graded_by': offering.teacher,
                            'remarks': fake.sentence(max_nb_chars=100) if random.choice([True, False]) else None
                        })
                    except Exception as e:
                        print(f"Error queuing exam result for {student.applicant.full_name} in {offering.course.code}: {e}")
                        continue
        except Exception as e:
            print(f"Error processing exam results for {offering.course.code}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(ExamResult, objects_queue, lock, 'exam result'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in exam result creation threads: {e}")

    try:
        results = list(ExamResult.objects.all())
        print(f"Created {len(results) - existing_results} new exam results")
        if result_dict is not None and key is not None:
            result_dict[key] = results
    except Exception as e:
        print(f"Error retrieving exam results: {e}")
        results = []
    return results

def create_fake_attendance(offerings, students, teachers, result_dict=None, key=None):
    worker_init()
    existing_attendance = Attendance.objects.count()
    students = list(Student.objects.all())  # Fetch directly from database
    expected_attendance = sum(20 * len([s for s in students if CourseEnrollment.objects.filter(
        student_semester_enrollment__student=s, course_offering=o).exists()]) for o in offerings)
    if existing_attendance >= expected_attendance:
        print(f"Skipping attendance creation: {existing_attendance} attendance records already exist")
        result = list(Attendance.objects.all())
        if result_dict is not None and key is not None:
            result_dict[key] = result
        return result
    attendance_records = []
    status_choices = ['present', 'absent', 'leave']
    objects_queue = queue.Queue()
    lock = threading.Lock()

    for offering in offerings:
        try:
            relevant_students = [s for s in students if CourseEnrollment.objects.filter(
                student_semester_enrollment__student=s, course_offering=offering).exists()]
            timetable_slots = TimetableSlot.objects.filter(course_offering=offering)
            semester_start = offering.semester.start_time  # DateField, already a date
            semester_end = offering.semester.end_time      # DateField, already a date
            for student in relevant_students:
                existing_count = Attendance.objects.filter(student=student, course_offering=offering).count()
                needed = 20 - existing_count
                available_slots = []
                for slot in timetable_slots:
                    current_date = semester_start  # Use date object directly
                    while current_date <= semester_end:
                        if slot.day.lower() == current_date.strftime('%A').lower():
                            available_slots.append((current_date, slot.start_time))
                        current_date += timedelta(days=1)
                available_slots = sorted(set(available_slots))[:needed]
                for date, start_time in available_slots:
                    try:
                        attendance_date = datetime.combine(date, start_time)
                        if not timezone.is_aware(attendance_date):
                            attendance_date = timezone.make_aware(attendance_date)
                        if not Attendance.objects.filter(
                            student=student,
                            course_offering=offering,
                            date=attendance_date
                        ).exists():
                            objects_queue.put({
                                'student': student,
                                'course_offering': offering,
                                'date': attendance_date,
                                'status': random.choice(status_choices),
                                'shift': offering.shift,
                                'recorded_by': offering.teacher
                            })
                    except Exception as e:
                        print(f"Error queuing attendance for {student.applicant.full_name} in {offering.course.code}: {e}")
                        continue
        except Exception as e:
            print(f"Error processing attendance for {offering.course.code}: {e}")
            continue

    threads = []
    try:
        for _ in range(10):
            t = threading.Thread(target=threaded_create, args=(Attendance, objects_queue, lock, 'attendance record'))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    except Exception as e:
        print(f"Error in attendance creation threads: {e}")

    try:
        attendance_records = list(Attendance.objects.all())
        print(f"Created {len(attendance_records) - existing_attendance} new attendance records")
        if result_dict is not None and key is not None:
            result_dict[key] = attendance_records
    except Exception as e:
        print(f"Error retrieving attendance records: {e}")
        attendance_records = []
    return attendance_records

def main():
    manager = multiprocessing.Manager()
    result_dict = manager.dict()

    # Create faculties, sessions, courses, etc. (placeholders for brevity)
    faculties = create_fake_faculties()  # Assume this creates 2 faculties
    sessions = create_fake_sessions()   # 6 sessions
    courses = create_fake_courses()     # 40 courses
    users = create_users()              # 600 users
    departments = create_departments()  # 4 departments
    programs = create_programs()        # 7 programs
    semesters = create_fake_semesters(programs, sessions, result_dict, 'semesters')  # 176 semesters
    admission_cycles = create_admission_cycles()  # 24 admission cycles
    venues = create_venues()            # 424 venues
    teachers = create_teachers()        # 100 teachers
    applicants = create_applicants()    # 290 applicants
    course_offerings = create_course_offerings()  # 880 course offerings
    timetable_slots = create_timetable_slots()   # 880 timetable slots
    study_materials = create_study_materials()    # 8800 study materials
    assignments = create_assignments()           # 4400 assignments
    students = create_students()        # 290 students
    semester_enrollments = create_semester_enrollments()  # 290 semester enrollments

    # Create remaining data with ProcessPoolExecutor
    with ProcessPoolExecutor(initializer=worker_init) as executor:
        futures = [
            executor.submit(create_fake_assignment_submissions, assignments, students, result_dict, 'submissions'),
            executor.submit(create_fake_exam_results, course_offerings, students, teachers, result_dict, 'exam_results'),
            executor.submit(create_fake_attendance, course_offerings, students, teachers, result_dict, 'attendance')
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in process: {e}")

if __name__ == '__main__':
    main()