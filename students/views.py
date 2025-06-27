# Standard library imports
import os
import logging
# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Q, Count, Max
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
# Local app imports
from academics.models import Department, Program, Semester
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification
from courses.models import Course, CourseOffering, ExamResult, StudyMaterial, Assignment, AssignmentSubmission, Notice, Attendance, Venue, TimetableSlot
from faculty_staff.models import Teacher, TeacherDetails
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
import datetime
import pytz  # Added import for pytz
# Custom user model
from django.urls import reverse
from datetime import time
CustomUser = get_user_model()




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
def session_courses(request, session_id):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    session = get_object_or_404(AcademicSession, id=session_id)
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        course_offering__academic_session=session
    ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'enrollments': enrollments,
        'session': session,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'session_courses.html', context)

@login_required
def assignments(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__course_offering__academic_session=current_session
    ).select_related('assignment__course_offering__course')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'submissions': submissions,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
    }
    return render(request, 'assignments.html', context)

@login_required
def study_materials(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    # Get current date in PKT
    current_date = timezone.now().astimezone(pytz.timezone('Asia/Karachi')).date()

    # Get the active semester
    active_semester = Semester.objects.filter(
        is_active=True,
        program=student.program,
        start_time__lte=current_date,
        end_time__gte=current_date
    ).first()

    # Initialize materials
    materials = []

    # Fetch study materials for the active semester's courses
    if active_semester:
        semester_enrollment = StudentSemesterEnrollment.objects.filter(
            student=student,
            semester=active_semester,
            status='enrolled'
        ).first()
        if semester_enrollment:
            materials = StudyMaterial.objects.filter(
                course_offering__enrollments__student_semester_enrollment=semester_enrollment,
                course_offering__is_active=True,
                course_offering__course__is_active=True
            ).select_related(
                'course_offering__course',
                'course_offering__semester',
                'course_offering__teacher__user'
            ).order_by('-uploaded_at')

    context = {
        'student': student,
        'active_semester': active_semester,
        'materials': materials,
    }
    return render(request, 'study_materials.html', context)

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
        return render(request, 'students/timetable.html', {
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