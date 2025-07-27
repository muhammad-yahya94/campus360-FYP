# Standard Library Imports
import os
import json
import logging
import datetime
from datetime import time
import random
import uuid

# Third-Party Imports
import pytz
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist

# Django Imports
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.storage import default_storage, FileSystemStorage
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.conf import settings
import os
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count, Max
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from django.contrib.auth import (
    authenticate, login, logout, update_session_auth_hash,
    get_user_model
)
from django.contrib.auth.decorators import login_required   
from django.db.models import Q
# Local App Imports
from academics.models import Department, Program, Semester
from admissions.models import (
    AcademicSession, AdmissionCycle, Applicant, AcademicQualification
)
from courses.models import (  
    Course, CourseOffering, ExamResult, StudyMaterial, Assignment,
    AssignmentSubmission, Notice, Attendance, Venue, TimetableSlot,
    Quiz, Question, Option, QuizSubmission, LectureReplacement
)
from faculty_staff.models import Teacher, TeacherDetails, DepartmentFund,ExamDateSheet
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment, StudentFundPayment
from fee_management.models import SemesterFee, StudentFeePayment, FeeToProgram, FeeVoucher
from collections import defaultdict
import math
from django.core.exceptions import PermissionDenied


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

        # Attempt to authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if the user is associated with a Student profile
            try:
                student = Student.objects.get(user=user)
                if student.current_status in ['active', 'graduated']:  
                    login(request, user)
                    messages.success(request, 'Login successful!')
                    return redirect('students:dashboard')
                else:
                    messages.error(request, 'Your account is not in an active or graduated status.')
            except Student.DoesNotExist:
                messages.error(request, 'You are not authorized as a student. Only students can log in.')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')




def student_dashboard(request):
    logger.info("Starting student_dashboard view for user: %s", request.user)
    
    try:
        student = Student.objects.get(user=request.user)
        current_session = student.applicant.session
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

    # Get all semester enrollments for the student with related data
    semester_enrollments = StudentSemesterEnrollment.objects.filter(
        student=student
    ).select_related(
        'semester',
        'semester__session',
        'semester__program'
    ).order_by('-semester__start_time', '-semester__number')

    # Get all course enrollments across all semesters, including reattempts
    course_enrollments = []
    semester_courses = {}
    
    # Get all course enrollments with is_repeat flag
    all_enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student
    ).select_related(
        'course_offering__course',
        'student_semester_enrollment__semester'
    ).order_by('student_semester_enrollment__semester__start_time')
    
    # Debug: Print course enrollment status
    logger.debug("Course enrollments for student %s:", student.applicant.full_name)
    for enroll in all_enrollments:
        logger.debug(
            "  Course %s (ID: %s) - Status: %s, is_repeat: %s",
            enroll.course_offering.course.code,
            enroll.id,
            enroll.status,
            enroll.is_repeat
        )
    
    for sem_enrollment in semester_enrollments:
        # Get all course enrollments for this semester
        sem_courses = CourseEnrollment.objects.filter(
            student_semester_enrollment=sem_enrollment,
            status__in=['enrolled', 'reattempt']  # Include both regular and reattempt enrollments
        ).select_related(
            'course_offering__course',
            'course_offering__semester',
            'course_offering__teacher__user',
            'course_offering__academic_session'
        ).order_by('course_offering__course__code')
        
        # Use the is_repeat flag directly from the model
        annotated_courses = list(sem_courses)
        for course in annotated_courses:
            logger.debug(
                "Course %s (ID: %s) - Status: %s, is_repeat: %s",
                course.course_offering.course.code,
                course.id,
                course.status,
                course.is_repeat
            )
        
        if annotated_courses:
            semester_courses[sem_enrollment.semester.id] = {
                'semester': sem_enrollment.semester,
                'courses': annotated_courses,
                'session': sem_enrollment.semester.session,
                'is_active': sem_enrollment.semester.is_active
            }
            course_enrollments.extend(annotated_courses)

    # Get the most recent active semester for the student's program and session
    active_semester = Semester.objects.filter(
        program=student.program,
        session=current_session,
        is_active=True
    ).order_by('-number').first()

    # Get recent notices
    from django.utils import timezone
    notices = Notice.objects.filter(
        Q(programs__in=[student.program]) | Q(programs__isnull=True)
    ).filter(
        is_active=True,
        valid_from__lte=timezone.now(),
    ).distinct().order_by('-created_at')[:3]

    logger.debug("Found %d course enrollment(s) across %d semesters", 
                len(course_enrollments), len(semester_courses))

    # Check if student has graduated
    is_graduated = student.current_status == 'graduated'
    
    return render(request, 'dashboard.html', {
        'student': student,
        'active_semester': active_semester,
        'semester_courses': semester_courses,
        'notices': notices,
        'current_session': current_session,
        'all_enrollments': course_enrollments,
        'is_graduated': is_graduated,
    })


def my_courses(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.warning(f"Unauthorized access attempt to my_courses by non-student user: {user}")
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = student.applicant.session.name
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    # Get the selected semester number from the query parameter
    selected_semester_number = request.GET.get('semester')
    if selected_semester_number:
        try:
            selected_semester_number = int(selected_semester_number)
            print(f"Selected semester number: {selected_semester_number}")
            enrollments = CourseEnrollment.objects.filter(
                student_semester_enrollment__student=student,
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
        ).values_list('semester__number', flat=True).order_by('semester__number').first()
        print(f"First semester number: {first_semester_number}")
        if first_semester_number:
            enrollments = CourseEnrollment.objects.filter(
                student_semester_enrollment__student=student,
                course_offering__semester__number=first_semester_number
            ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
        else:
            enrollments = CourseEnrollment.objects.none()  # No enrollments if no semesters exist

    semester_numbers = Semester.objects.filter(
        program=student.program,
        session=student.applicant.session,
    ).order_by('number').values_list('number', flat=True).distinct()
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

from django.db.models import Q
from datetime import datetime
import subprocess
import tempfile
import os

@login_required
def notices(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    # Get filter parameters
    notice_type = request.GET.get('notice_type', '')
    priority = request.GET.get('priority', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Start with base queryset
    notices = Notice.objects.filter(
        Q(programs__in=[student.program]) | Q(programs__isnull=True),
        # Q(sessions__in=[student.current_session]) | Q(sessions__isnull=True),
        is_active=True,
        valid_from__lte=timezone.now(),
    ).distinct()

    # Apply filters
    if notice_type:
        notices = notices.filter(notice_type=notice_type)
    
    if priority:
        notices = notices.filter(priority=priority)
    
    if search:
        notices = notices.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search)
        )
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            notices = notices.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            notices = notices.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Order and paginate
    notices = notices.order_by('-is_pinned', '-created_at')[:20]
    
    # Get unique notice types and priorities for filter dropdowns
    notice_types = Notice.NOTICE_TYPES
    priorities = Notice.PRIORITY_LEVELS

    context = {
        'student': student,
        'notices': notices,
        'notice_types': notice_types,
        'priorities': priorities,
        'current_filters': {
            'notice_type': notice_type,
            'priority': priority,
            'search': search,
            'date_from': date_from if date_from else '',
            'date_to': date_to if date_to else '',
        },
    }
    return render(request, 'notice.html', context)





















def calculate_grade(percentage):
    """Calculate grade based on percentage according to the provided conversion table."""
    if percentage is None:
        return 'N/A'
    percentage = float(percentage)
    if percentage >= 85:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 75:
        return 'B+'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 65:
        return 'C+'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


@login_required
def exam_results(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(request, 'exam_results.html', {'msg': 'No student profile found for this user.'})

    roll_no = student.university_roll_no or 'N/A'
    session = student.applicant.session
    print(f"Student: {student}, Roll No: {roll_no}, Session: {session}, Time: 07:59 PM PKT, July 12, 2025")

    # Fetch exam results with shift filter
    results = ExamResult.objects.filter(
        student=student,
    ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__academic_session').order_by(
        'course_offering__semester__name', 'course_offering__course__code'
    )
    print(f"Results fetched: {results.count()} entries.")

    # Handle case where no results are found
    not_found_roll = f"No results found for roll number {roll_no}" if roll_no and not results else None

    # Separate optional and non-optional results
    opt_results = results.filter(course_offering__course__opt=True)
    non_opt_results = results.exclude(course_offering__course__opt=True)
    print(f"Optional results count: {opt_results.count()}, Non-optional results count: {non_opt_results.count()}.")

    def calculate_quality_points(result):
        credit_hour = result.course_offering.course.credits
        total_marks = math.ceil(float(result.percentage or 0))
        print(f"Result for {result.student.university_roll_no}: Percentage: {result.percentage}, Ceiled: {total_marks}")

        quality_points_mapping = {
            40: 1.0, 41: 1.1, 42: 1.2, 43: 1.3, 44: 1.4, 45: 1.5,
            46: 1.6, 47: 1.7, 48: 1.8, 49: 1.9, 50: 2.0, 51: 2.07,
            52: 2.14, 53: 2.21, 54: 2.28, 55: 2.35, 56: 2.42, 57: 2.49,
            58: 2.56, 59: 2.63, 60: 2.70, 61: 2.76, 62: 2.82, 63: 2.88,
            64: 2.94, 65: 3.00, 66: 3.05, 67: 3.10, 68: 3.15, 69: 3.20,
            70: 3.25, 71: 3.30, 72: 3.35, 73: 3.40, 74: 3.45, 75: 3.50,
            76: 3.55, 77: 3.60, 78: 3.65, 79: 3.70, 80: 3.75, 81: 3.80,
            82: 3.85, 83: 3.90, 84: 3.95, 85: 4.0, 86: 4.0, 87: 4.0,
            88: 4.0, 89: 4.0, 90: 4.0, 91: 4.0, 92: 4.0, 93: 4.0,
            94: 4.0, 95: 4.0, 96: 4.0, 97: 4.0, 98: 4.0, 99: 4.0,
            100: 4.0
        }
        quality_points = quality_points_mapping.get(total_marks, 0.0) * credit_hour
        print(f"Result: {result.student.university_roll_no}, Marks: {total_marks}, Quality Points: {quality_points}")
        return round(quality_points, 2)

    # Add calculated fields to non-optional results
    for result in non_opt_results:
        result.quality_points = calculate_quality_points(result)
        result.grade = calculate_grade(result.percentage)
        
        # Set is_fail based on grade and save to database
        if result.grade == 'F' and not result.is_fail:
            result.is_fail = True
            result.save(update_fields=['is_fail'])
        
        # Get enrollment info to check if this is a repeat course
        try:
            enrollment = CourseEnrollment.objects.get(
                student_semester_enrollment__student=result.student,
                course_offering=result.course_offering
            )
            result.is_repeat = enrollment.is_repeat
        except CourseEnrollment.DoesNotExist:
            result.is_repeat = False
        
        result.effective_credit_hour = result.course_offering.course.credits
        result.course_marks = result.course_offering.course.credits * 20 + (
            result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
        )
        print(f"Result: {result.student.university_roll_no}, Quality Points: {result.quality_points}, "
              f"Effective Credit Hours: {result.effective_credit_hour}, Course Marks: {result.course_marks}")
    # Add grades and repeat status to optional results
    for opt_result in opt_results:
        opt_result.grade = calculate_grade(opt_result.percentage)
        # Get enrollment info to check if this is a repeat course
        try:
            enrollment = CourseEnrollment.objects.get(
                student_semester_enrollment__student=opt_result.student,
                course_offering=opt_result.course_offering
            )
            opt_result.is_repeat = enrollment.is_repeat
        except CourseEnrollment.DoesNotExist:
            opt_result.is_repeat = False

    # Group non-optional results by semester
    semester_results = defaultdict(list)
    for result in non_opt_results:
        semester_results[result.course_offering.semester.name].append(result)

    # Calculate semester-wise metrics
    semester_gpas = {}
    semester_totals = {}
    for semester, semester_data in semester_results.items():
        total_qp = sum(calculate_quality_points(result) for result in semester_data)
        total_credit_hours = sum(result.course_offering.course.credits for result in semester_data)
        semester_gpas[semester] = round(total_qp / total_credit_hours, 2) if total_credit_hours > 0 else 0

        total_marks = sum(float(result.percentage or 0) * result.course_offering.course.credits for result in semester_data)
        avg_percentage = math.ceil(total_marks / total_credit_hours) if total_credit_hours > 0 else 0
        total_full_marks = sum(
            (result.course_offering.course.credits * 20 + (
                result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
            )) for result in semester_data
        )
        max_marks = sum(result.total_marks or 0 for result in semester_data)
        total_quality_points = round(sum(calculate_quality_points(result) for result in semester_data), 2)

        semester_totals[semester] = {
            'total_credit_hours': total_credit_hours,
            'total_full_marks': total_full_marks,
            'max_marks': max_marks,
            'average_percentage': avg_percentage,
            'total_quality_points': total_quality_points
        }
        print(f"Semester: {semester}")
        print(f"  Total Credit Hours: {total_credit_hours}")
        print(f"  Total Full Marks: {total_full_marks}")
        print(f"  Max Marks: {max_marks}")
        print(f"  Average Percentage: {avg_percentage}%")
        print(f"  Total Quality Points: {total_quality_points}")

    # Calculate overall CGPA (excluding optional courses)
    total_quality_points = round(sum(result.quality_points for result in non_opt_results), 2)
    total_credit_hours = sum(result.course_offering.course.credits for result in non_opt_results)
    cgpa = round(total_quality_points / total_credit_hours, 2) if total_credit_hours > 0 else 0
    print(f"Total Quality Points: {total_quality_points}, Total Credit Hours: {total_credit_hours}, CGPA: {cgpa}")

    total_marks = sum(float(result.percentage or 0) * result.course_offering.course.credits for result in non_opt_results)
    avg_percentage = math.ceil(total_marks / total_credit_hours) if total_credit_hours > 0 else 0
    print(f"Total Marks: {total_marks}, Average Percentage: {avg_percentage}")

    total_full_marks = sum(
        (result.course_offering.course.credits * 20 + (
            result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
        )) for result in non_opt_results
    )
    max_marks = sum(result.total_marks or 0 for result in non_opt_results)
    print(f"Total Full Marks: {total_full_marks}, Max Marks: {max_marks}")

    context = {
        'student': student,
        'semester_results': dict(semester_results),
        'semester_gpas': semester_gpas,
        'opt_results': opt_results,
        'roll_no': roll_no,
        'session': session,
        'semester_totals': semester_totals,
        'msg': not_found_roll,
        'total_credit_hours': total_credit_hours,
        'total_full_marks': total_full_marks,
        'max_marks': max_marks,
        'avg_percentage': avg_percentage,
        'total_quality_points': total_quality_points,
        'cgpa': cgpa,
    }

    return render(request, 'exam_results.html', context)






















@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('students:login')

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your old password was entered incorrectly.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2



def student_attendance(request, course_offering_id):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    # Get the course offering
    course_offering = get_object_or_404(CourseOffering, id=course_offering_id)

    # Get attendance records for this student and course offering
    attendances = Attendance.objects.filter(
        course_offering_id=course_offering_id,
        student=student
    ).select_related(
        'course_offering__course',
        'recorded_by__user'
    ).order_by('-date')

    # Calculate attendance statistics
    total_classes = attendances.count()
    present_count = attendances.filter(status='present').count()
    absent_count = attendances.filter(status='absent').count()
    leave_count = attendances.filter(status='leave').count()
    
    percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

    course_stats = {
        'course': course_offering.course,
        'present': present_count,
        'absent': absent_count,
        'leave': leave_count,
        'total': total_classes,
        'percentage': round(percentage, 2)
    }

    context = {
        'student': student,
        'attendances': attendances,
        'course_stats': course_stats,
        'course_offering': course_offering,
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
        logger.debug("Step 1: Found student: %s (ID: %s)", student.applicant.full_name, student.user.id)
    except Student.DoesNotExist:
        logger.error("No Student found for user: %s", request.user)
        return render(request, 'timetable.html', {
            'student': None,
            'timetable_data': [],
            'active_session': None,
        })

    # Get the active semester enrollment
    try:
        active_enrollment = StudentSemesterEnrollment.objects.filter(
            student=student,
            semester__is_active=True
        ).order_by('-semester__start_time').first()
        if not active_enrollment:
            logger.warning("Step 2: No active semester enrollment found for student: %s", student.applicant.full_name)
            return render(request, 'timetable.html', {
                'student': student,
                'timetable_data': [],
                'active_session': None,
            })
        active_semester = active_enrollment.semester
        active_session = active_semester.session
        logger.debug("Step 3: Active semester: %s, Session: %s", active_semester.name, active_session.name)
    except Exception as e:
        logger.error("Error querying active enrollment: %s", str(e))
        return render(request, 'timetable.html', {
            'student': student,
            'timetable_data': [],
            'active_session': None,
        })

    # Get course enrollments for the active semester
    try:
        enrollments = CourseEnrollment.objects.filter(
            student_semester_enrollment__student=student,
            student_semester_enrollment__semester=active_semester
        ).select_related('course_offering__course', 'course_offering__program', 'course_offering__semester', 'course_offering__teacher', 'course_offering__replacement_teacher')
        logger.debug("Step 4: Found %d course enrollments for student in semester %s", enrollments.count(), active_semester.name)
    except Exception as e:
        logger.error("Error querying course enrollments: %s", str(e))
        enrollments = CourseEnrollment.objects.none()

    # Get timetable slots for enrolled courses
    try:
        course_offerings = enrollments.values_list('course_offering', flat=True)
        timetable_slots = TimetableSlot.objects.filter(
            course_offering__in=course_offerings
        ).filter(
            Q(course_offering__shift=student.applicant.shift) | Q(course_offering__shift='both')
        ).select_related(
            'course_offering__course',
            'course_offering__teacher',
            'course_offering__replacement_teacher',
            'venue',
            'course_offering__program',
            'course_offering__semester'
        )
        logger.debug("Step 5: Retrieved %d timetable slots for student", timetable_slots.count())
    except Exception as e:
        logger.error("Error querying timetable slots: %s", str(e))
        timetable_slots = TimetableSlot.objects.none()

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
    current_date = timezone.now().date()
    for day in days:
        day_slots = timetable_slots.filter(day=day['day_value'])
        slots = []
        for slot in day_slots:
            # Check for replacement teacher
            replacement = None
            original_teacher_name = None
            try:
                replacement = LectureReplacement.objects.filter(
                    course_offering=slot.course_offering,
                    replacement_date__lte=current_date
                ).filter(
                    Q(replacement_type='permanent') |
                    Q(replacement_type='temporary', replacement_date__lte=current_date)
                ).select_related('replacement_teacher', 'original_teacher').first()
                if replacement:
                    original_teacher_name = f"{replacement.original_teacher.user.first_name} {replacement.original_teacher.user.last_name}"
                    logger.debug(
                        "Step 6a: Found LectureReplacement for CourseOffering %s: Replacement Teacher ID=%s, Original Teacher=%s, Type=%s, Date=%s",
                        slot.course_offering.id, replacement.replacement_teacher.id, original_teacher_name, replacement.replacement_type, replacement.replacement_date
                    )
            except Exception as e:
                logger.error("Step 6b: Error querying LectureReplacement for CourseOffering %s: %s", slot.course_offering.id, str(e))

            # Check CourseOffering.replacement_teacher if no LectureReplacement
            if not replacement and slot.course_offering.replacement_teacher:
                original_teacher_name = f"{slot.course_offering.teacher.user.first_name} {slot.course_offering.teacher.user.last_name}"
                logger.debug(
                    "Step 6c: CourseOffering %s has replacement_teacher ID=%s, Original Teacher=%s",
                    slot.course_offering.id, slot.course_offering.replacement_teacher.id, original_teacher_name
                )

            # Determine teacher to display
            teacher = (
                replacement.replacement_teacher if replacement else
                slot.course_offering.replacement_teacher or
                slot.course_offering.teacher
            )
            teacher_name = f"{teacher.user.first_name} {teacher.user.last_name}" if teacher else 'N/A'
            replaced_for = original_teacher_name if (replacement or slot.course_offering.replacement_teacher) else None

            logger.debug(
                "Step 6d: Slot for %s, Course: %s (ID: %s), Teacher: %s, Replaced for: %s",
                day['day_label'], slot.course_offering.course.code, slot.course_offering.id, teacher_name, replaced_for or 'None'
            )

            slots.append({
                'course_code': slot.course_offering.course.code,
                'course_name': slot.course_offering.course.name,
                'teacher_name': teacher_name,
                'replaced_for': replaced_for,
                'venue': slot.venue.name,
                'room_no': slot.venue.capacity,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'shift': slot.course_offering.get_shift_display(),
                'program': slot.course_offering.program.name if slot.course_offering.program else 'N/A',
                'semester': slot.course_offering.semester.name,
            })
        if slots:
            timetable_data.append({
                'day_value': day['day_value'],
                'day_label': day['day_label'],
                'slots': slots
            })
            logger.debug("Step 7: Added %d slots for %s", len(slots), day['day_label'])

    logger.info("Step 8: Timetable data prepared for student: %s, with %d days", student.applicant.full_name, len(timetable_data))

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

def settings_view(request):
    """
    View for the student settings page.
    Displays account information and settings options.
    """
    try:
        student = Student.objects.get(user=request.user)
        user = request.user

        # Initialize data with current user and applicant information
        initial_data = {
            'full_name': student.applicant.full_name,
            'email': user.email,
            'contact_no': student.applicant.contact_no or '',
            'address': student.applicant.permanent_address or '',
        }

        # Create a simple form-like object for the template
        user_form = type('UserForm', (), {'instance': type('Instance', (), initial_data)})()

        # Password change form (using Django's built-in form)
        from django.contrib.auth.forms import PasswordChangeForm
        password_form = PasswordChangeForm(user)

        context = {
            'student': student,
            'user': user,
            'user_form': user_form,
            'password_form': password_form,
            'form_errors': {},
            'student_full_name': student.applicant.full_name,
            'today_date': timezone.now().date(),
        }
        return render(request, 'settings.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:dashboard')
    except Exception as e:
        logger.error(f"Error in settings_view: {str(e)}")
        messages.error(request, 'An error occurred while loading settings.')
        return redirect('students:dashboard')
    
    
@login_required
def profile_view(request):
    """
    Display student profile information with all related details.
    """
    try:
        student = Student.objects.select_related('applicant', 'program', 'program__department', 'program__department__faculty').get(user=request.user)
        
        # Get academic qualifications
        academic_qualifications = student.applicant.academic_qualifications.all().order_by('-passing_year')
        
        # Get extra curricular activities
        extra_curriculars = student.applicant.extra_curricular_activities.all().order_by('-activity_year')
        
        context = {
            'student': student,
            'user': request.user,
            'applicant': student.applicant,
            'academic_qualifications': academic_qualifications,
            'extra_curriculars': extra_curriculars,
            'student_full_name': student.applicant.full_name if hasattr(student, 'applicant') else '',
            'today_date': timezone.now().date(),
        }
        return render(request, 'profile.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:dashboard')
    except Exception as e:
        logger.error(f"Error in profile_view: {str(e)}")
        messages.error(request, 'An error occurred while loading your profile.')
        return redirect('students:dashboard')


@login_required
def update_account(request):
    """
    Handle updating student account information.
    """
    try:
        student = Student.objects.get(user=request.user)
        user = request.user
        form_errors = {}

        # Get form data
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        contact_no = request.POST.get('contact_no', '').strip()
        address = request.POST.get('address', '').strip()

        # Validate required fields
        if not full_name:
            form_errors['full_name'] = 'Full name is required.'
        if not email:
            form_errors['email'] = 'Email is required.'
        elif '@' not in email:
            form_errors['email'] = 'Enter a valid email address.'

        # If there are validation errors, return to the form with errors
        if form_errors:
            initial_data = {
                'full_name': full_name,
                'email': email,
                'contact_no': contact_no,
                'address': address,
            }
            user_form = type('UserForm', (), {'instance': type('Instance', (), initial_data)})()
            context = {
                'student': student,
                'user': user,
                'user_form': user_form,
                'password_form': PasswordChangeForm(user),
                'form_errors': form_errors,
                'student_full_name': full_name,
                'today_date': timezone.now().date(),
            }
            return render(request, 'settings.html', context, status=400)

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            # Validate file size (max 2MB)
            if profile_picture.size > 2 * 1024 * 1024:
                messages.error(request, 'Profile picture size should not exceed 2MB.')
                return redirect('students:settings')

            # Validate file type
            if not profile_picture.content_type.startswith('image/'):
                messages.error(request, 'Only image files are allowed for profile pictures.')
                return redirect('students:settings')

            # Delete old profile picture if exists
            if user.profile_picture:
                try:
                    if os.path.isfile(user.profile_picture.path):
                        os.remove(user.profile_picture.path)
                except (ValueError, FileNotFoundError):
                    pass  # File doesn't exist or path is not accessible

            # Save new profile picture
            fs = FileSystemStorage()
            # Create a clean filename and path
            import os
            import uuid
            
            # Generate a unique filename to prevent collisions
            file_ext = os.path.splitext(profile_picture.name)[1]
            filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # Create the relative path for storage
            relative_path = os.path.join('profile_pictures', f'user_{user.id}', filename)
            
            # Save the file
            saved_path = fs.save(relative_path, profile_picture)
            
            # Store just the relative path in the database
            # Django's FileField will handle the URL construction
            user.profile_picture.name = saved_path

        # Update user information
        user.email = email
        user.save()

        # Update applicant information
        applicant = student.applicant
        applicant.full_name = full_name
        applicant.contact_no = contact_no
        applicant.address = address
        applicant.save()

        messages.success(request, 'Account updated successfully!')
        return redirect('students:settings')

    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:dashboard')
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        messages.error(request, 'An error occurred while updating your account.')
        return redirect('students:settings')
    
    
    
    

@login_required
def ide(request):
    """
    View for the online code editor.
    """
    return render(request, 'ide.html')
 
    
def semester_fees(request):
    """
    Display student's semester fees with voucher status and total amounts.
    """
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all semesters for the student's program and session
        semesters = Semester.objects.filter(
            program=student.program,
            session=student.applicant.session,
        ).order_by('name')
        
        # Get all fee vouchers for this student with related data
        fee_vouchers = FeeVoucher.objects.filter(
            student=student
        ).select_related(
            'semester', 
            'semester_fee',
            'semester_fee__fee_type',
            'payment'
        ).order_by('-due_date')
        
        # Create a dictionary to store semester data
        semester_data = {}
        
        # Process fee vouchers
        for voucher in fee_vouchers:
            if voucher.semester_id not in semester_data:
                semester_data[voucher.semester_id] = {
                    'semester': voucher.semester,
                    'vouchers': [],
                    'total_amount': 0,
                    'is_fully_paid': True,
                    'due_date': voucher.due_date
                }
            
            semester_data[voucher.semester_id]['vouchers'].append(voucher)
            semester_data[voucher.semester_id]['total_amount'] += voucher.semester_fee.total_amount
            if not voucher.is_paid:
                semester_data[voucher.semester_id]['is_fully_paid'] = False
        
        # Convert to list and sort by semester name
        semester_list = sorted(
            semester_data.values(), 
            key=lambda x: x['semester'].name
        )
        
        context = {
            'student': student,
            'semester_list': semester_list,
            'student_full_name': student.applicant.full_name,
            'today_date': timezone.now().date(),
            'has_payments': any(sem['is_fully_paid'] for sem in semester_list)
        }
        
        return render(request, 'students/semester_fees.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:semester_fees')
    except Exception as e:
        logger.error(f"Error in semester_fees view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while loading your fee status.')
        return redirect('students:semester_fees')

def change_password(request):
    """
    Handle password change for the student.
    """
    try:
        student = Student.objects.get(user=request.user)
        user = request.user
        
        if request.method == 'POST':
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('students:settings')
            else:
                form_errors = {}
                for field, errors in form.errors.items():
                    form_errors[field] = errors
        else:
            form = PasswordChangeForm(user)
            form_errors = {}

        # Get current user and applicant data for the form
        initial_data = {
            'full_name': student.applicant.full_name,
            'email': user.email,
            'contact_no': student.applicant.contact_no or '',
            'address': student.applicant.permanent_address or '',
        }

        context = {
            'student': student,
            'user': user,
            'user_form': type('UserForm', (), {'instance': type('Instance', (), initial_data)})(),
            'password_form': form,
            'form_errors': form_errors,
            'password_errors': True,  # Flag to show password tab by default
            'student_full_name': student.applicant.full_name,
            'today_date': timezone.now().date(),
        }
        
        if request.method == 'POST' and form_errors:
            return render(request, 'settings.html', context, status=400)
        return render(request, 'settings.html', context)

    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students:dashboard')
    except Exception as e:
        logger.error(f"Error in change_password view: {str(e)}")
        messages.error(request, 'An unexpected error occurred. Please try again later.')
        return redirect('students:settings')
    
    
    
@login_required
def fund_payments(request):
    student = get_object_or_404(Student, user=request.user)
    print(f'student is -- {student}, Session: {student.applicant.session}, Program: {student.program}, Shift: {student.applicant.shift}, Role: {student.role}, Gender: {student.applicant.gender}')
    
    # Get funds associated with the student's program (and optionally session, if model supports)
    funds = DepartmentFund.objects.filter(
        programs=student.program,
        is_active=True
    ).distinct()
    print(f'funds are -- {funds}')

    # Get payment records for the student
    payments = StudentFundPayment.objects.filter(student=student)
    print(f'payments are -- {payments}')

    # Determine if the student can verify payments
    is_cr = student.role == 'CR'
    is_gr = student.role == 'GR'
    verifiable_payments = []
    show_verification = False
    all_pending_payments = []
    
    try:
        # Check if filter form was submitted
        filter_submitted = 'apply_filters' in request.GET
        fund_filter = request.GET.get('fund', '')
        
        # Base query for all pending payments in the same session, program, and shift
        all_pending_payments = StudentFundPayment.objects.filter(
            student__applicant__session=student.applicant.session,  # Same session
            student__program=student.program,                      # Same program
            student__applicant__shift=student.applicant.shift,     # Same shift
            status='pending'
        )
        
        # Apply gender filter for CR/GR
        if is_cr:
            all_pending_payments = all_pending_payments.filter(
                student__applicant__gender='male'
            )
        elif is_gr:
            all_pending_payments = all_pending_payments.filter(
                student__applicant__gender='female'
            )
            
        all_pending_payments = all_pending_payments.select_related('student__applicant', 'fund')
        
        # Apply fund filter if selected
        if fund_filter and fund_filter != 'all':
            all_pending_payments = all_pending_payments.filter(fund_id=fund_filter)
        
        # For CR/GR, show verifiable payments when filters are applied
        if is_cr or is_gr:
            show_verification = filter_submitted
            if show_verification:
                # Get or create payment records for all students in the same session, program, and shift
                if fund_filter and fund_filter != 'all':
                    fund = get_object_or_404(DepartmentFund, id=fund_filter)
                    # Get students in the same session, program, and shift
                    students_in_program = Student.objects.filter(
                        applicant__session=student.applicant.session,  # Same session
                        program=student.program,                      # Same program
                        applicant__shift=student.applicant.shift       # Same shift
                    )
                    if is_cr:
                        students_in_program = students_in_program.filter(
                            applicant__gender='male'
                        )
                    elif is_gr:
                        students_in_program = students_in_program.filter(
                            applicant__gender='female'
                        )
                    
                    # Create payment records for students who don't have one for this fund
                    for std in students_in_program:
                        StudentFundPayment.objects.get_or_create(
                            student=std,
                            fund=fund,
                            defaults={
                                'status': 'pending',
                                'amount_paid': 0,
                                'notes': 'Auto-created for verification'
                            }
                        )
                    
                    # Get all payments for this fund, filtered by session, program, shift, and gender
                    verifiable_payments = StudentFundPayment.objects.filter(
                        fund=fund,
                        student__applicant__session=student.applicant.session,  # Same session
                        student__program=student.program,                      # Same program
                        student__applicant__shift=student.applicant.shift      # Same shift
                    )
                    
                    if is_cr:
                        verifiable_payments = verifiable_payments.filter(
                            student__applicant__gender='male'
                        )
                    elif is_gr:
                        verifiable_payments = verifiable_payments.filter(
                            student__applicant__gender='female'
                        )
                else:
                    # If no specific fund is selected, show all payments for the session, program, and shift
                    verifiable_payments = StudentFundPayment.objects.filter(
                        student__applicant__session=student.applicant.session,  # Same session
                        student__program=student.program,                      # Same program
                        student__applicant__shift=student.applicant.shift      # Same shift
                    )
                    
                    if is_cr:
                        verifiable_payments = verifiable_payments.filter(
                            student__applicant__gender='male'
                        )
                    elif is_gr:
                        verifiable_payments = verifiable_payments.filter(
                            student__applicant__gender='female'
                        )
                
                verifiable_payments = verifiable_payments.distinct()
                print(f'Verifiable payments: {verifiable_payments.query}')
                print(f'Verifiable payments count: {verifiable_payments.count()}')
            
            # Always show all pending payments for CR/GR
            all_pending_payments = all_pending_payments.distinct()
        
    except Exception as e:
        messages.error(request, f'Error fetching payments: {str(e)}')
        import traceback
        print(traceback.format_exc())
        verifiable_payments = []
        all_pending_payments = []

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_payment':
            fund_id = request.POST.get('fund_id')
            fund = get_object_or_404(DepartmentFund, id=fund_id)
            amount_paid = request.POST.get('amount_paid')
            payment_date = request.POST.get('payment_date')
            notes = request.POST.get('notes')
            proof = request.FILES.get('proof')

            try:
                payment, created = StudentFundPayment.objects.get_or_create(
                    student=student,
                    fund=fund,
                    defaults={
                        'status': 'pending',
                        'amount_paid': amount_paid or 0,
                        'payment_date': payment_date or None,
                        'notes': notes or '',
                        'proof': proof
                    }
                )
                if not created:
                    payment.amount_paid = amount_paid or payment.amount_paid
                    payment.payment_date = payment_date or payment.payment_date
                    payment.notes = notes or payment.notes
                    if proof:
                        payment.proof = proof
                    payment.status = 'pending'
                    payment.save()
                messages.success(request, 'Payment details uploaded successfully.')
            except Exception as e:
                messages.error(request, f'Error uploading payment: {str(e)}')
            return redirect('students:fund_payments')

        elif action == 'verify_payment':
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(StudentFundPayment, id=payment_id)
            
            # Allow students to update their own payment status
            if payment.student == student:
                new_status = request.POST.get('new_status')
                if new_status in ['paid', 'pending', 'partial', 'unpaid']:
                    payment.status = new_status
                    if new_status == 'pending':
                        payment.verified_by = None
                    payment.save()
                    messages.success(request, f'Your payment status has been updated to {new_status}.')
                else:
                    messages.error(request, 'Invalid payment status.')
                return redirect('students:fund_payments')
            
            # CR/GR verification for other students
            elif is_cr or is_gr:
                # Check session, program, shift, and gender restrictions
                if payment.student.applicant.session != student.applicant.session:
                    raise PermissionDenied("You can only verify payments for students in your academic session.")
                if payment.student.program != student.program:
                    raise PermissionDenied("You can only verify payments for students in your program.")
                if payment.student.applicant.shift != student.applicant.shift:
                    raise PermissionDenied("You can only verify payments for students in your shift.")
                if is_cr and payment.student.applicant.gender != 'male':
                    raise PermissionDenied("CR can only verify payments for male students.")
                if is_gr and payment.student.applicant.gender != 'female':
                    raise PermissionDenied("GR can only verify payments for female students.")
                
                new_status = request.POST.get('new_status')
                if new_status not in ['paid', 'partial', 'unpaid']:
                    messages.error(request, 'Invalid payment status.')
                    return redirect('students:fund_payments')
                    
                payment.status = new_status
                payment.verified_by = student
                payment.save()
                messages.success(request, f'Payment for {payment.student.applicant.full_name} verified as {new_status}.')
                return redirect('students:fund_payments')
            else:
                raise PermissionDenied("You are not authorized to verify this payment.")

    # Get current date in Asia/Karachi timezone
    karachi_tz = pytz.timezone('Asia/Karachi')
    current_date = timezone.now().astimezone(karachi_tz).date()
    
    context = {
        'student': student,
        'funds': funds,
        'payments': payments,
        'is_cr': is_cr,
        'is_gr': is_gr,
        'verifiable_payments': verifiable_payments,
        'all_pending_payments': all_pending_payments,
        'show_verification': show_verification,
        'now': current_date,
    }
    return render(request, 'fund_payments.html', context)




def exam_slip(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.warning(f"Unauthorized access attempt to exam_slip by non-student user: {user}")
        messages.error(request, "You are not registered as a student.")
        return redirect('students:login')

    # Get the student's program and session
    program = student.program
    current_session = student.applicant.session
    if not program or not current_session:
        messages.error(request, "No program or session associated with your profile.")
        return redirect('students:login')

    # Get all semesters for the student's program and session (without is_active filter)
    semester_numbers = Semester.objects.filter(
        program=program,
        session=current_session
    ).order_by('number').values_list('number', flat=True).distinct()

    # Get the selected semester number from the query parameter
    selected_semester_number = request.GET.get('semester')
    if selected_semester_number:
        try:
            selected_semester_number = int(selected_semester_number)
        except ValueError:
            selected_semester_number = None
    else:
        selected_semester_number = semester_numbers.first() if semester_numbers else None

    # Get exam slips for the selected semester, filtered by the student's enrollments (without is_active filter)
    if selected_semester_number:
        exam_slips = ExamDateSheet.objects.filter(
            semester__number=selected_semester_number,
            program=program,
            academic_session=current_session
        ).select_related(
            'course_offering__course',
            'program',
            'academic_session',
            'semester'
        ).order_by('exam_date', 'start_time')
    else:
        exam_slips = ExamDateSheet.objects.none()

    context = {
        'student': student,
        'semester_numbers': semester_numbers,
        'selected_semester_number': selected_semester_number,
        'exam_slips': exam_slips,
        'current_session': current_session.name,
    }
    return render(request, 'exam_slip.html', context)