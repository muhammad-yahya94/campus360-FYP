# Standard Library Imports
import os
import json
import logging
import datetime
from datetime import time
import random

# Third-Party Imports
import pytz

# Django Imports
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.storage import default_storage, FileSystemStorage
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count, Max
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth import (
    authenticate, login, logout, update_session_auth_hash,
    get_user_model
)
from django.contrib.auth.decorators import login_required

# Local App Imports
from academics.models import Department, Program, Semester
from admissions.models import (
    AcademicSession, AdmissionCycle, Applicant, AcademicQualification
)
from courses.models import (
    Course, CourseOffering, ExamResult, StudyMaterial, Assignment,
    AssignmentSubmission, Notice, Attendance, Venue, TimetableSlot,
    Quiz, Question, Option, QuizSubmission
)
from faculty_staff.models import Teacher, TeacherDetails
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment






# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CustomUser = get_user_model()

def student_login(request):
    if request.user.is_authenticated:
        return redirect('students:dashboard')

    if request.method == 'POST':
        email = request.POST.get('username')  # Email field is used as username
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            try:  
                student = Student.objects.get(user=user)
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('students:dashboard')
            except Student.DoesNotExist:
                messages.error(request, 'You are not authorized as a student.')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')



@login_required
def student_dashboard(request):
    logger.info("Starting student_dashboard view for user: %s", request.user)

    try:
        student = Student.objects.get(user=request.user)
        logger.debug(
            "Found student: %s (User ID: %s, Program: %s, Program ID: %s)",
            student.applicant.full_name,
            student.user.id,
            student.program.name,
            student.program.id
        )
    except Student.DoesNotExist:
        logger.error("No Student found for user: %s", request.user)
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()

    if not current_session:
        logger.warning("No active academic session found.")
        return render(request, 'dashboard.html', {
            'student': student,
            'active_semester': None,
            'enrollments': [],
        })

    # ✅ Get active semester in current session for student's program
    active_semester = Semester.objects.filter(
        program=student.program,
        session=current_session,
        is_active=True
    ).order_by('-number').first()

    if not active_semester:
        logger.warning(
            "No active semester found for student: %s in session: %s",
            student.applicant.full_name,
            current_session.name
        )
        return render(request, 'dashboard.html', {
            'student': student,
            'active_semester': None,
            'enrollments': [],
        })

    logger.debug(
        "Active semester found: %s (Semester ID: %s) in session: %s",
        active_semester.name,
        active_semester.id,
        current_session.name
    )

    current_session = AcademicSession.objects.filter(is_active=True).first()
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        course_offering__academic_session=current_session,
        course_offering__semester__is_active=True  # ✅ Filter only active semester courses
    ).select_related(
        'course_offering__course',
        'course_offering__semester',
        'course_offering__teacher__user'
    )

    logger.debug("Found %d course(s) in active semester", enrollments.count())

    return render(request, 'dashboard.html', {
        'student': student,
        'active_semester': active_semester,
        'enrollments': enrollments,
    })








def my_courses(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.warning(f"Unauthorized access attempt to my_courses by non-student user: {user}")
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    # Get the selected semester number from the query parameter
    selected_semester_number = request.GET.get('semester')
    if selected_semester_number:
        try:
            selected_semester_number = int(selected_semester_number)
            enrollments = CourseEnrollment.objects.filter(
                student_semester_enrollment__student=student,
                course_offering__academic_session=current_session,
                course_offering__semester__number=selected_semester_number
            ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
        except ValueError:
            enrollments = CourseEnrollment.objects.filter(
                student_semester_enrollment__student=student,
                course_offering__academic_session=current_session
            ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
    else:
        # Default to the first semester number if no selection
        first_semester_number = CourseOffering.objects.filter(
            academic_session=current_session
        ).values_list('semester__number', flat=True).order_by('semester__number').first()
        if first_semester_number:
            enrollments = CourseEnrollment.objects.filter(
                student_semester_enrollment__student=student,
                course_offering__academic_session=current_session,
                course_offering__semester__number=first_semester_number
            ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
        else:
            enrollments = CourseEnrollment.objects.none()  # No enrollments if no semesters exist



    semester_numbers = Semester.objects.filter(
    program=student.program,
    is_active=True
).order_by('number').values_list('number', flat=True)
    print(f'this is queery set only numbers --  {semester_numbers}')
    context = {
        'enrollments': enrollments,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
        'semester_numbers': semester_numbers,
        'selected_semester_number': selected_semester_number or first_semester_number,
    }
    return render(request, 'my_courses.html', context)



@login_required
def assignments(request, course_offering_id):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.error(f"User {user} is not authorized as a student.")
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    try:
        course_offering = CourseOffering.objects.get(
            id=course_offering_id,
            enrollments__student_semester_enrollment__student=student
        )
        assignments = Assignment.objects.filter(course_offering=course_offering).select_related('course_offering__course')
        course_offerings = [course_offering]
        logger.info(f"Found course offering: {course_offering}, assignments: {list(assignments)}")
    except CourseOffering.DoesNotExist:
        logger.error(f"Course offering {course_offering_id} not found or unauthorized for student: {student}")
        messages.error(request, 'Invalid or unauthorized course offering.')
        return redirect('students:my_courses')

    # Get submissions for the student, ordered by submission date (newest first)
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    ).select_related('assignment__course_offering__course').order_by('-submitted_at')
    logger.info(f"Found submissions: {list(submissions)}")

    # Combine all assignments with status
    all_assignments = []
    now = timezone.now()

    for assignment in assignments:
        submission = submissions.filter(assignment=assignment).first()
        if submission and submission.submitted_at:
            status = "Submitted"
            can_submit = False
            assignment_data = submission
        else:
            submission = submission or AssignmentSubmission(student=student, assignment=assignment)
            can_submit = assignment.due_date is None or assignment.due_date > now
            status = "Pending" if can_submit else "Overdue"
            assignment_data = {'submission': submission, 'can_submit': can_submit}

        all_assignments.append({
            'assignment_data': assignment_data,
            'status': status,
            'is_pending': status == "Pending"
        })
        logger.debug(f"Assignment: {assignment.title}, status: {status}, can_submit: {can_submit}")

    # Sort assignments: First by status (Pending > Submitted > Overdue), then by creation date (newest first)
    all_assignments.sort(key=lambda x: (
        not x['is_pending'],  # Pending first
        x['status'] != "Submitted",  # Then Submitted
        # Finally by due date (or max date if none) for same status items
        (x['assignment_data']['submission'].assignment.due_date if isinstance(x['assignment_data'], dict)
         else x['assignment_data'].assignment.due_date) or timezone.datetime.max,
        # Add creation date for sorting (newest first)
        -((x['assignment_data']['submission'].assignment.created_at.timestamp() if isinstance(x['assignment_data'], dict)
           else x['assignment_data'].assignment.created_at.timestamp()) or 0)
    ))

    logger.info(f"Total assignments: {len(all_assignments)}, Pending: {sum(1 for a in all_assignments if a['status'] == 'Pending')}, Submitted: {sum(1 for a in all_assignments if a['status'] == 'Submitted')}, Overdue: {sum(1 for a in all_assignments if a['status'] == 'Overdue')}")

    context = {
        'all_assignments': all_assignments,
        'selected_course_offering': course_offering,
        'now': now,
    }
    return render(request, 'assignments.html', context)

@login_required
def submit_assignment(request, assignment_id):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.error(f"User {user} is not authorized as a student.")
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    try:
        assignment = Assignment.objects.get(
            id=assignment_id,
            course_offering__enrollments__student_semester_enrollment__student=student
        )
        submission = AssignmentSubmission.objects.get(student=student, assignment=assignment)
    except Assignment.DoesNotExist:
        logger.error(f"Assignment {assignment_id} not found or unauthorized for student: {student}")
        messages.error(request, 'Invalid assignment.')
        return redirect('students:my_courses')
    except AssignmentSubmission.DoesNotExist:
        submission = AssignmentSubmission.objects.create(
            student=student,
            assignment=assignment
        )

    has_submitted = submission.submitted_at is not None

    if request.method == 'POST':
        if assignment.due_date and assignment.due_date < timezone.now():
            logger.error(f"Submission deadline passed for assignment {assignment_id}")
            messages.error(request, 'Submission deadline has passed.')
            return redirect('students:assignments', course_offering_id=assignment.course_offering.id)

        content = request.POST.get('content')
        file = request.FILES.get('files')

        submission.content = content
        submission.submitted_at = timezone.now()

        if file:
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            submission.file = filename

        submission.save()
        logger.info(f"Assignment {assignment_id} submitted successfully by student: {student}")
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('students:assignments', course_offering_id=assignment.course_offering.id)

    context = {
        'assignment': assignment,
        'submission': submission,
        'has_submitted': has_submitted,
    }
    return render(request, 'submit_assignment.html', context)

@login_required
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        logger.info(f"Image uploaded: {filename}")
        return JsonResponse({'url': fs.url(filename)})
    logger.error("Invalid request for image upload")
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def study_materials(request, course_offering_id):
    logger.info(f"Study materials requested for course_offering_id: {course_offering_id} by user: {request.user}")
    
    try:
        logger.debug("Attempting to fetch student and course offering...")
        student = Student.objects.get(user=request.user)
        course_offering = CourseOffering.objects.get(
            id=course_offering_id,
            enrollments__student_semester_enrollment__student=student,
            is_active=True,
            course__is_active=True
        )
        logger.info(f"Found course offering: {course_offering}")
    except Student.DoesNotExist:
        logger.error(f"Student not found for user: {request.user}")
        messages.error(request, 'You are not authorized to view these materials or the course does not exist.')
        return redirect('students:my_courses')
    except CourseOffering.DoesNotExist:
        logger.error(f"Course offering not found or access denied - ID: {course_offering_id}, User: {request.user}")
        messages.error(request, 'You are not authorized to view these materials or the course does not exist.')
        return redirect('students:my_courses')
    except Exception as e:
        logger.exception(f"Unexpected error in study_materials view: {str(e)}")
        messages.error(request, 'An error occurred while loading study materials.')
        return redirect('students:my_courses')

    # Get current date in PKT
    current_date = timezone.now().astimezone(pytz.timezone('Asia/Karachi')).date()
    logger.debug(f"Current date in PKT: {current_date}")

    try:
        # Get all materials for this course offering
        logger.debug("Fetching study materials from database...")
        materials = StudyMaterial.objects.filter(
            course_offering=course_offering
        ).select_related(
            'course_offering__course',
            'course_offering__semester',
            'course_offering__teacher__user',
            'teacher__user'
        ).order_by('-created_at')
        
        logger.info(f"Found {materials.count()} study materials for course offering {course_offering_id}")
        
        # Pagination
        paginator = Paginator(materials, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Group materials by topic (for context compatibility)
        materials_by_topic = {}
        for material in materials:
            if material.topic not in materials_by_topic:
                materials_by_topic[material.topic] = []
            materials_by_topic[material.topic].append(material)
        
        logger.debug(f"Grouped materials into {len(materials_by_topic)} topics")
        
        context = {
            'student': student,
            'course_offering': course_offering,
            'materials': materials,
            'page_obj': page_obj,
            'materials_by_topic': materials_by_topic,
            'topics': sorted(materials_by_topic.keys()) if materials_by_topic else []
        }
        
        logger.debug("Rendering study materials template")
        return render(request, 'study_materials.html', context)
        
    except Exception as e:
        logger.exception(f"Error processing study materials: {str(e)}")
        messages.error(request, 'An error occurred while processing study materials.')
        return redirect('students:my_courses')

@login_required
def notices(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    notices = Notice.objects.all().order_by('-created_at')

    context = {
        'student': student,
        'notices': notices,
    }
    return render(request, 'notice.html', context)

@login_required
def exam_results(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    results = ExamResult.objects.filter(
        student=student
    ).select_related('course_offering__course', 'course_offering__academic_session')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'results': results,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'exam_results.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('students:login')









@login_required
def student_attendance(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    # Get the active semester
    active_semester = Semester.objects.filter(
        is_active=True,
        program=student.program,
    ).first()

    # Initialize attendance records and stats
    attendances = []
    course_stats = []

    # Get course_offering_id from query parameter (optional)
    course_offering_id = request.GET.get('course_offering_id')

    # Fetch attendance for the active semester's courses
    if active_semester:
        semester_enrollment = StudentSemesterEnrollment.objects.filter(
            student=student,
            semester=active_semester,
            status='enrolled'
        ).first()
        if semester_enrollment:
            # Fetch attendance records
            query = Attendance.objects.filter(
                course_offering__enrollments__student_semester_enrollment=semester_enrollment,
                course_offering__is_active=True,
                course_offering__course__is_active=True
            ).select_related(
                'course_offering__course',
                'course_offering__semester',
                'course_offering__teacher__user',
                'recorded_by__user'
            ).order_by('-date')

            if course_offering_id:
                query = query.filter(course_offering__id=course_offering_id)

            attendances = query

            # Aggregate stats for each course
            stats_query = CourseEnrollment.objects.filter(
                student_semester_enrollment=semester_enrollment,
                course_offering__is_active=True,
                course_offering__course__is_active=True
            ).annotate(
                present_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='present')),
                absent_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='absent')),
                leave_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='leave')),
                total_count=Count('course_offering__attendances')
            )

            if course_offering_id:
                stats_query = stats_query.filter(course_offering__id=course_offering_id)

            course_stats = [
                {
                    'course': enrollment.course_offering.course,
                    'present': enrollment.present_count,
                    'absent': enrollment.absent_count,
                    'leave': enrollment.leave_count,
                    'total': enrollment.total_count,
                    'percentage': (enrollment.present_count / enrollment.total_count * 100) if enrollment.total_count > 0 else 0
                } for enrollment in stats_query
            ]

    context = {
        'student': student,
        'active_semester': active_semester,
        'attendances': attendances,
        'course_stats': course_stats,
        'course_offering_id': course_offering_id,
    }
    return render(request, 'attendance.html', context)







@login_required
def student_attendance_stats(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    # Get current date in PKT
    current_date = timezone.now().astimezone(pytz.timezone('Asia/Karachi')).date()

    # Get the active semester (optional use)
    active_semester = Semester.objects.filter(
        is_active=True,
        program=student.program,
    ).first()

    # Get all semester enrollments for the student
    semester_enrollments = StudentSemesterEnrollment.objects.filter(
        student=student
    ).select_related('semester').order_by('semester__number')

    print("Total semester enrollments found:", semester_enrollments.count())

    # Aggregate stats
    stats_by_semester = []
    for sem_enrollment in semester_enrollments:
        semester = sem_enrollment.semester
        print(f"Processing Semester {semester.number} (Status: {sem_enrollment.status})")

        # Course-level stats
        course_stats = CourseEnrollment.objects.filter(
            student_semester_enrollment=sem_enrollment,
            course_offering__is_active=True,
            course_offering__course__is_active=True
        ).annotate(
            present_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='present')),
            absent_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='absent')),
            leave_count=Count('course_offering__attendances', filter=Q(course_offering__attendances__status='leave')),
            total_count=Count('course_offering__attendances')
        ).select_related('course_offering__course', 'course_offering__semester')

        stats = [
            {
                'course': enrollment.course_offering.course,
                'total': enrollment.total_count,
                'present': enrollment.present_count,
                'absent': enrollment.absent_count,
                'leave': enrollment.leave_count,
                'percentage': (enrollment.present_count / enrollment.total_count * 100) if enrollment.total_count > 0 else 0
            } for enrollment in course_stats
        ]

        # Semester-level stats
        semester_stats = Attendance.objects.filter(
            course_offering__enrollments__student_semester_enrollment=sem_enrollment,
            course_offering__is_active=True,
            course_offering__course__is_active=True
        ).aggregate(
            present_count=Count('id', filter=Q(status='present')),
            absent_count=Count('id', filter=Q(status='absent')),
            leave_count=Count('id', filter=Q(status='leave')),
            total_count=Count('id')
        )
        semester_stats['percentage'] = (
            semester_stats['present_count'] / semester_stats['total_count'] * 100
            if semester_stats['total_count'] > 0 else 0
        )

        # Append regardless of whether attendance exists
        stats_by_semester.append({
            'semester': semester,
            'course_stats': stats,
            'semester_stats': semester_stats
        })

    # Pagination
    paginator = Paginator(stats_by_semester, 1)  # 1 semester per page
    page = request.GET.get('page')
    try:
        stats_by_page = paginator.page(page)
    except PageNotAnInteger:
        stats_by_page = paginator.page(1)
    except EmptyPage:
        stats_by_page = paginator.page(paginator.num_pages)

    context = {
        'student': student,
        'active_semester': active_semester,
        'stats_by_semester': stats_by_page,
    }
    return render(request, 'attendance_stats.html', context)




def student_timetable(request):
    logger.info("Starting student_timetable view for user: %s", request.user)
    
    # Get the student
    try:
        student = Student.objects.get(user=request.user)
        logger.debug("Found student: %s (ID: %s)", student.applicant.full_name, student.user.id)
    except Student.DoesNotExist:
        logger.error("No Student found for user: %s", request.user)
        return render(request, 'timetable.html', {
            'student': None,
            'timetable_data': [],
            'active_session': None,
        })

    # Get the active semester enrollment (latest active semester)
    active_enrollment = StudentSemesterEnrollment.objects.filter(
        student=student,
        semester__is_active=True
    ).order_by('-semester__start_time').first()

    if not active_enrollment:
        logger.warning("No active semester enrollment found for student: %s", student.applicant.full_name)
        return render(request, 'timetable.html', {
            'student': student,
            'timetable_data': [],
            'active_session': None,
        })

    active_semester = active_enrollment.semester
    active_session = active_semester.session
    logger.debug("Active semester: %s, Session: %s", active_semester.name, active_session.name)

    # Get course enrollments for the active semester
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        student_semester_enrollment__semester=active_semester
    ).select_related('course_offering__course', 'course_offering__program', 'course_offering__semester', 'course_offering__teacher')
    logger.debug("Found %d course enrollments for student in semester %s", enrollments.count(), active_semester.name)

    # Get timetable slots for enrolled courses
    course_offerings = enrollments.values_list('course_offering', flat=True)
    timetable_slots = TimetableSlot.objects.filter(
        course_offering__in=course_offerings
    ).select_related('course_offering__course', 'course_offering__teacher', 'venue', 'course_offering__program', 'course_offering__semester')
    logger.debug("Retrieved %d timetable slots for student", timetable_slots.count())

    # Organize slots by day
    days = [
        {'day_value': 'monday', 'day_label': 'Monday'},
        {'day_value': 'tuesday', 'day_label': 'Tuesday'},
        {'day_value': 'wednesday', 'day_label': 'Wednesday'},
        {'day_value': 'thursday', 'day_label': 'Thursday'},
        {'day_value': 'friday', 'day_label': 'Friday'},
        {'day_value': 'saturday', 'day_label': 'Saturday'},
    ]
    timetable_data = []
    for day in days:
        day_slots = timetable_slots.filter(day=day['day_value'])
        slots = [
            {
                'course_code': slot.course_offering.course.code,
                'course_name': slot.course_offering.course.name,
                'teacher_name': f"{slot.course_offering.teacher.user.first_name} {slot.course_offering.teacher.user.last_name}",
                'venue': slot.venue.name,
                'room_no': slot.venue.capacity,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'shift': slot.course_offering.get_shift_display(),
                'program': slot.course_offering.program.name if slot.course_offering.program else 'N/A',
                'semester': slot.course_offering.semester.name,
            }
            for slot in day_slots
        ]
        if slots:  # Only include days with slots
            timetable_data.append({
                'day_value': day['day_value'],
                'day_label': day['day_label'],
                'slots': slots
            })
            logger.debug("Added %d slots for %s", len(slots), day['day_label'])

    logger.info("Timetable data prepared for student: %s, with %d days", student.applicant.full_name, len(timetable_data))

    context = {
        'student': student,
        'timetable_data': timetable_data,
        'active_session': active_session,
    }
    return render(request, 'timetable.html', context)   




@login_required
def solve_quiz(request, course_offering_id):
    try:
        student = Student.objects.get(user=request.user)
        course_offering = CourseOffering.objects.get(id=course_offering_id)
        quizzes = list(Quiz.objects.filter(course_offering=course_offering, publish_flag=True))
        random.shuffle(quizzes)
        # Check if student has taken each quiz
        quiz_data = []
        for quiz in quizzes:
            has_taken = QuizSubmission.objects.filter(student=student, quiz=quiz).exists()
            quiz_data.append({'quiz': quiz, 'has_taken': has_taken})
        context = {
            'course_offering': course_offering,
            'quizzes': quiz_data,
            'today_date': request.GET.get('today_date', None),
            'student_full_name': student.applicant.full_name
        }
        logger.info(f"Fetched {len(quizzes)} randomized quizzes for course offering {course_offering_id} for user {student.applicant.full_name}")
        return render(request, 'solve_quiz.html', context)
    except ObjectDoesNotExist as e:
        if isinstance(e, CourseOffering.DoesNotExist):
            logger.error(f"CourseOffering {course_offering_id} not found")
            return JsonResponse({'success': False, 'message': 'Course offering not found'}, status=404)
        elif isinstance(e, Student.DoesNotExist):
            logger.error(f"User {request.user.first_name} has no associated Student profile")
            return JsonResponse({'success': False, 'message': 'Student profile not found'}, status=400)

@require_GET
@login_required
def get_quiz(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id, publish_flag=True)
        questions = quiz.questions.all()
        if not questions:
            logger.error(f"No questions found for quiz {quiz_id}")
            return JsonResponse({'success': False, 'message': 'No questions available'}, status=400)
        response_data = {
            'id': quiz.id,
            'title': quiz.title,
            'timer_seconds': quiz.timer_seconds,
            'questions': [
                {
                    'id': q.id,
                    'text': q.text,
                    'marks': q.marks,
                    'options': [
                        {'id': o.id, 'text': o.text, 'is_correct': o.is_correct}
                        for o in q.options.all()
                    ]
                }
                for q in questions
            ]
        }
        logger.info(f"Fetched quiz {quiz_id} for student")
        return JsonResponse(response_data)
    except ObjectDoesNotExist:
        logger.error(f"Quiz {quiz_id} not found or not published")
        return JsonResponse({'success': False, 'message': 'Quiz not found or not published'}, status=404)

@login_required
def submit_quiz(request, quiz_id):
    try:
        student = Student.objects.get(user=request.user)
        quiz = Quiz.objects.get(id=quiz_id, publish_flag=True)
        if request.method == 'GET':
            # View existing result
            try:
                result = QuizSubmission.objects.get(student=student, quiz=quiz)
                # Reconstruct answers for quiz_result.html
                answers = []
                for question in quiz.questions.all():
                    selected_option_id = result.answers.get(str(question.id))
                    answer = {
                        'question': {
                            'id': question.id,
                            'text': question.text,
                            'marks': question.marks
                        },
                        'marks_awarded': 0
                    }
                    correct_option = question.options.filter(is_correct=True).first()
                    answer['correct_option'] = {'id': correct_option.id, 'text': correct_option.text}
                    if selected_option_id:
                        try:
                            selected_option = Option.objects.get(id=selected_option_id, question=question)
                            answer['selected_option'] = {'id': selected_option.id, 'text': selected_option.text}
                            answer['is_correct'] = selected_option.is_correct
                            if selected_option.is_correct:
                                answer['marks_awarded'] = question.marks
                        except ObjectDoesNotExist:
                            answer['selected_option'] = None
                            answer['is_correct'] = False
                    else:
                        answer['selected_option'] = None
                        answer['is_correct'] = False
                    answers.append(answer)
                context = {
                    'quiz': quiz,
                    'result': {
                        'score': result.score,
                        # 'max_score': result.score,
                        'answers': answers
                    },
                    'today_date': timezone.now().date(),
                    'student_full_name': student.applicant.full_name
                }
                logger.info(f"Displayed result for quiz {quiz_id} for user {student.applicant.full_name}")
                return render(request, 'quiz_result.html', context)
            except ObjectDoesNotExist:
                logger.error(f"No result found for quiz {quiz_id} for user {student.applicant.full_name}")
                return JsonResponse({'success': False, 'message': 'No result found for this quiz'}, status=404)

        elif request.method == 'POST':
            # Check if quiz already taken
            if QuizSubmission.objects.filter(student=student, quiz=quiz).exists():
                logger.info(f"User {student.applicant.full_name} attempted to retake quiz {quiz_id}")
                return JsonResponse({'success': False, 'message': 'Quiz already taken'}, status=400)

            # Process new submission
            data = request.POST
            answers = {}
            score = 0
            max_score = 0
            logger.info(f"Received quiz submission for quiz {quiz_id}: {data}")

            for question in quiz.questions.all():
                max_score += question.marks
                answer_key = f"answers[{question.id}]"
                selected_option_id = data.get(answer_key)
                if selected_option_id:
                    answers[str(question.id)] = selected_option_id
                    try:
                        selected_option = Option.objects.get(id=selected_option_id, question=question)
                        if selected_option.is_correct:
                            score += question.marks
                    except ObjectDoesNotExist:
                        pass  # Invalid option ID, treat as incorrect

            # Save result
            result = QuizSubmission.objects.create(
                student=student,
                quiz=quiz,
                score=score,
                # score=score,
                answers=answers
            )
            logger.info(f"Quiz {quiz_id} submitted by user {student.applicant.full_name}. Score: {score}")

            # Prepare context for quiz_result.html
            answers_list = []
            for question in quiz.questions.all():
                answer = {
                    'question': {
                        'id': question.id,
                        'text': question.text,
                        'marks': question.marks
                    },
                    'marks_awarded': 0
                }
                selected_option_id = answers.get(str(question.id))  
                correct_option = question.options.filter(is_correct=True).first()
                answer['correct_option'] = {'id': correct_option.id, 'text': correct_option.text}
                if selected_option_id:
                    try:
                        selected_option = Option.objects.get(id=selected_option_id, question=question)
                        answer['selected_option'] = {'id': selected_option.id, 'text': selected_option.text}
                        answer['is_correct'] = selected_option.is_correct
                        if selected_option.is_correct:
                            answer['marks_awarded'] = question.marks
                    except ObjectDoesNotExist:
                        answer['selected_option'] = None
                        answer['is_correct'] = False
                else:
                    answer['selected_option'] = None
                    answer['is_correct'] = False
                answers_list.append(answer)

            context = {
                'quiz': quiz,
                'result': {
                    'score': score,
                    # 'max_score': max_score,
                    'answers': answers_list
                },
                'today_date': timezone.now().date(),
                'student_full_name': student.applicant.full_name
            }
            return render(request, 'quiz_result.html', context)
    except ObjectDoesNotExist as e:
        if isinstance(e, Quiz.DoesNotExist):
            logger.error(f"Quiz {quiz_id} not found or not published")
            return JsonResponse({'success': False, 'message': 'Quiz not found or not published'}, status=404)
        elif isinstance(e, Student.DoesNotExist):
            logger.error(f"User {request.user.first_name} has no associated Student profile")
            return JsonResponse({'success': False, 'message': 'Student profile not found'}, status=400)
    except Exception as e:
        logger.error(f"Error processing quiz submission {quiz_id}: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)