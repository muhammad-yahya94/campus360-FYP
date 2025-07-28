# Standard Library Imports
import os
import logging
import datetime
import json
import random
import string
from datetime import time, date

# Third-party Imports
import pytz
from django.core.mail import send_mail   
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Django Core Imports
from django import forms
from django.contrib import messages  
from django.contrib.auth import (
    authenticate, login, logout,
    update_session_auth_hash, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Sum, Q, Count, Max, Subquery, OuterRef, F, Value
from django.db.utils import IntegrityError
from django.db.models.functions import ExtractYear
from django.forms.models import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods


# Custom User Model  
CustomUser = get_user_model()

# App Imports (Local Apps)
from academics.models import Department, Program, Semester
from admissions.models import (
    AcademicSession, AdmissionCycle,
    Applicant, AcademicQualification
)
from courses.models import (
    Course, CourseOffering, ExamResult, StudyMaterial,
    Assignment, AssignmentSubmission, Notice,
    Attendance, Venue, TimetableSlot,
    Quiz, Question, QuizSubmission, Option, LectureReplacement
)
from faculty_staff.models import Teacher, TeacherDetails, OfficeStaff, Office, DepartmentFund, ExamDateSheet
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment

# Forms
from .forms import (
    UserUpdateForm, TeacherUpdateForm, TeacherStatusForm,
    PasswordChangeForm, QuestionForm, QuizForm
)

# Decorators
from .decorators import hod_or_professor_required, hod_required



# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if hasattr(user, 'teacher_profile'):
                login(request, user)
                designation = user.teacher_profile.designation

                if designation == 'head_of_department':
                    messages.success(request, 'Login successful! Welcome, Head of Department.')
                    return redirect(reverse('faculty_staff:hod_dashboard'))
                elif designation == 'professor':
                    messages.success(request, 'Login successful! Welcome, Professor.')
                    return redirect(reverse('faculty_staff:professor_dashboard'))  
                else:
                    messages.error(request, 'You do not have the required faculty staff role.')
                    logout(request)  # Log out if the role is not HOD or Professor
                    return redirect('faculty_staff:login')
            else:
                messages.error(request, 'You do not have faculty staff access.')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'faculty_staff/login.html')


@hod_required
def hod_dashboard(request):
    try:
        teacher_profile = request.user.teacher_profile
        if teacher_profile.designation != 'head_of_department':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('home')
    except Teacher.DoesNotExist:
        messages.error(request, 'You do not have a teacher profile. Please contact the administrator.')
        return redirect('home')

    hod_department = teacher_profile.department

    # Fetch counts for the dashboard cards
    total_staff = Teacher.objects.filter(department=hod_department).count()
    active_staff = Teacher.objects.filter(department=hod_department, is_active=True).count()
    active_students = Student.objects.filter(
        program__department=hod_department,
        current_status='active'
    ).count()
    current_sessions = AcademicSession.objects.filter(is_active=True).count()
    department_programs = Program.objects.filter(department=hod_department).count()
    working_semesters = Semester.objects.filter(
        program__department=hod_department,
        is_active=True
    ).count()



    context = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'active_students': active_students,
        'current_sessions': current_sessions,
        'department_programs': department_programs,
        'working_semesters': working_semesters,
        'department': hod_department,
    }
    return render(request, 'faculty_staff/hod_dashboard.html', context)


@hod_or_professor_required
def professor_dashboard(request):
    # Fetch courses assigned to the professor, filtered for active semesters
    course_offerings = CourseOffering.objects.filter(
        teacher=request.user.teacher_profile,
        semester__is_active=True
    ).select_related('course', 'semester', 'academic_session', 'program', 'department')

    context = {
        'course_offerings': course_offerings,
        'user_name': f"{request.user.first_name} {request.user.last_name}",
    }
    return render(request, 'faculty_staff/professor_dashboard.html', context)






def staff_management(request):
    hod_department = request.user.teacher_profile.department
    staff_list = Teacher.objects.filter(department=hod_department).order_by('user__last_name', 'user__first_name')
    print(f"this is staff -- {staff_list}")
    search_query = request.GET.get('search', '')
    if search_query:
        staff_list = staff_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )  

    status = request.GET.get('status')
    if status == 'active':
        staff_list = staff_list.filter(is_active=True)
    elif status == 'inactive':
        staff_list = staff_list.filter(is_active=False)

    paginator = Paginator(staff_list, 10)
    page_number = request.GET.get('page')
    staff_members = paginator.get_page(page_number)
    print(f'this is employettpe {TeacherDetails.EMPLOYMENT_TYPE_CHOICES}')
    context = {
        'staff_members': staff_members,
        'department': hod_department,
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
        'status_choices': TeacherDetails.STATUS_CHOICES,
        'gender_choices': Teacher.GENDER_CHOICES,
    }
    return render(request, 'faculty_staff/staff_management.html', context)

@hod_required
def add_staff(request):
    hod_department = request.user.teacher_profile.department

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation = request.POST.get('designation')
        gender = request.POST.get('gender')  # New field
        contact_no = request.POST.get('contact_no', '')
        qualification = request.POST.get('qualification', '')
        hire_date = request.POST.get('hire_date', None)
        is_active = request.POST.get('is_active') == 'on'
        linkedin_url = request.POST.get('linkedin_url', '')
        twitter_url = request.POST.get('twitter_url', '')
        personal_website = request.POST.get('personal_website', '')
        experience = request.POST.get('experience', '')
        employment_type = request.POST.get('employment_type', '')
        salary_per_lecture = request.POST.get('salary_per_lecture', None)
        fixed_salary = request.POST.get('fixed_salary', None)
        status = request.POST.get('status', '')

        if not all([first_name, last_name, email, designation, gender]):
            messages.error(request, 'Please fill in all required fields (First Name, Last Name, Email, Designation, Gender).')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {
                    'first_name': not first_name,
                    'last_name': not last_name,
                    'email': not email,
                    'designation': not designation,
                    'gender': not gender,  # Add gender to form errors
                },
            })

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'email': 'exists'},
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'designation': True},
            })

        if gender not in dict(Teacher.GENDER_CHOICES).keys():
            messages.error(request, 'Invalid gender selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'gender': True},
            })

        try:
            # Generate random 8-digit password
            password = ''.join(random.choices(string.digits, k=8))
            
            user = CustomUser.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=True
            )
            user.set_password(password)
            user.save()
            
            # Send email with credentials
            subject = 'Your Campus360 Faculty Account Has Been Created'
            html_message = render_to_string('faculty_staff/account_created_email.html', {
                'first_name': first_name,
                'email': email,
                'password': password,
                # 'login_url': request.build_absolute_uri('/faculty/login/')
            })
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=None,  # Will use DEFAULT_FROM_EMAIL from settings
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error but don't fail the user creation
                logger.error(f'Failed to send email to {email}: {str(e)}')

            teacher = Teacher.objects.create(
                user=user,
                department=hod_department,
                designation=designation,
                gender=gender,  # Add gender
                contact_no=contact_no,
                qualification=qualification,
                hire_date=hire_date if hire_date else None,
                is_active=is_active,
                linkedin_url=linkedin_url,
                twitter_url=twitter_url,
                personal_website=personal_website,
                experience=experience
            )

            # Create TeacherDetails
            TeacherDetails.objects.create(
                teacher=teacher,
                employment_type=employment_type if employment_type else None,
                salary_per_lecture=salary_per_lecture if salary_per_lecture else None,
                fixed_salary=fixed_salary if fixed_salary else None,
                status=status if status else None
            )

            messages.success(request, f'Teacher {user.get_full_name()} has been added successfully.')
            return redirect('faculty_staff:staff_management')

        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {},
            })

    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
        'status_choices': TeacherDetails.STATUS_CHOICES,
        'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
    })
    
    
        
@hod_required
def edit_staff(request, staff_id):
    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=staff_id, department=hod_department)
    details = teacher.details if hasattr(teacher, 'details') else None

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation = request.POST.get('designation')
        gender = request.POST.get('gender')  # New field
        contact_no = request.POST.get('contact_no', '')
        qualification = request.POST.get('qualification', '')
        hire_date = request.POST.get('hire_date', None)
        is_active = request.POST.get('is_active') == 'on'
        linkedin_url = request.POST.get('linkedin_url', '')
        twitter_url = request.POST.get('twitter_url', '')
        personal_website = request.POST.get('personal_website', '')
        experience = request.POST.get('experience', '')
        employment_type = request.POST.get('employment_type', '')
        salary_per_lecture = request.POST.get('salary_per_lecture', None)
        fixed_salary = request.POST.get('fixed_salary', None)
        status = request.POST.get('status', '')

        if not all([first_name, last_name, email, designation, gender]):
            messages.error(request, 'Please fill in all required fields (First Name, Last Name, Email, Designation, Gender).')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {
                    'first_name': not first_name,
                    'last_name': not last_name,
                    'email': not email,
                    'designation': not designation,
                    'gender': not gender,  # Add gender to form errors
                },
            })

        if CustomUser.objects.filter(email=email).exclude(id=teacher.user.id).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'email': 'exists'},
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'designation': True},
            })

        if gender not in dict(Teacher.GENDER_CHOICES).keys():
            messages.error(request, 'Invalid gender selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {'gender': True},
            })

        try:
            teacher.user.first_name = first_name
            teacher.user.last_name = last_name
            teacher.user.email = email
            teacher.user.save()

            teacher.designation = designation
            teacher.gender = gender  # Update gender
            teacher.contact_no = contact_no
            teacher.qualification = qualification
            teacher.hire_date = hire_date if hire_date else None
            teacher.is_active = is_active
            teacher.linkedin_url = linkedin_url
            teacher.twitter_url = twitter_url
            teacher.personal_website = personal_website
            teacher.experience = experience
            teacher.save()

            # Update or create TeacherDetails
            if details:
                details.employment_type = employment_type if employment_type else None
                details.salary_per_lecture = salary_per_lecture if salary_per_lecture else None
                details.fixed_salary = fixed_salary if fixed_salary else None
                details.status = status if status else None
                details.save()
            else:
                TeacherDetails.objects.create(
                    teacher=teacher,
                    employment_type=employment_type if employment_type else None,
                    salary_per_lecture=salary_per_lecture if salary_per_lecture else None,
                    fixed_salary=fixed_salary if fixed_salary else None,
                    status=status if status else None
                )

            messages.success(request, f'Teacher {teacher.user.get_full_name()} has been updated successfully.')
            return redirect('faculty_staff:staff_management')

        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
                'status_choices': TeacherDetails.STATUS_CHOICES,
                'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
                'form_errors': {},
            })

    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'employment_type_choices': TeacherDetails.EMPLOYMENT_TYPE_CHOICES,
        'status_choices': TeacherDetails.STATUS_CHOICES,
        'gender_choices': Teacher.GENDER_CHOICES,  # Add gender choices
    })
    
    
        
@hod_required
def delete_staff(request, staff_id):
    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=staff_id, department=hod_department)

    if request.method == 'POST':
        teacher_name = teacher.user.get_full_name()
        teacher.delete()  # This will cascade delete TeacherDetails due to on_delete=models.CASCADE
        messages.success(request, f'Teacher {teacher_name} has been deleted successfully.')
        return redirect('faculty_staff:staff_management')

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,
    })



import calendar  
from datetime import date
import logging


def hod_required(view_func):
    from django.contrib.auth.decorators import login_required
    return login_required(view_func)


@login_required
def teacher_lecture_details(request, teacher_id):
    # Ensure teacher_id is an integer
    try:
        teacher_id = int(teacher_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid teacher_id: {teacher_id}")
        return render(request, 'faculty_staff/error.html', {
            'message': 'Invalid teacher ID provided.'
        }, status=400)

    # Ensure the teacher is in the HOD's department
    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=teacher_id, department=hod_department)
    logger.debug(f"Step 1: Teacher retrieved: {teacher}, ID: {teacher_id}, Type: {type(teacher)}")

    # Step 1: Get total course offerings for active sessions
    try:
        current_year = timezone.now().year
        active_sessions = AcademicSession.objects.filter(
            Q(is_active=True) | Q(end_year__gte=current_year)
        ).values_list('id', flat=True)
        logger.debug(f"Step 2: Active sessions: {list(active_sessions)}")

        course_offerings = CourseOffering.objects.filter(
            teacher=teacher,
            academic_session__id__in=active_sessions
        ).select_related('course', 'semester', 'program', 'academic_session')
        course_offering_ids = course_offerings.values_list('id', flat=True)
        logger.debug(f"Step 3: Total course offerings: {list(course_offering_ids)}")
    except Exception as e:
        logger.error(f"Error querying CourseOffering: {str(e)}")
        return render(request, 'faculty_staff/error.html', {
            'message': f'Error retrieving course offerings: {str(e)}'
        }, status=500)

    # Step 2: Get replacement course offerings
    try:
        replacement_course_offerings = CourseOffering.objects.filter(
            Q(replacement_teacher=teacher) |
            Q(id__in=LectureReplacement.objects.filter(
                replacement_teacher=teacher,
                course_offering__academic_session__id__in=active_sessions
            ).values_list('course_offering__id', flat=True))
        ).select_related('course', 'semester', 'program', 'academic_session')
        replacement_course_offering_ids = replacement_course_offerings.values_list('id', flat=True)
        logger.debug(f"Step 4: Replacement course offerings: {list(replacement_course_offering_ids)}")
    except Exception as e:
        logger.error(f"Error querying replacement CourseOffering: {str(e)}")
        replacement_course_offerings = CourseOffering.objects.none()
        replacement_course_offering_ids = []

    # Step 3: Get unique normal lectures (recorded_by=teacher and teacher is original teacher)
    try:
        normal_lectures = Attendance.objects.filter(
            recorded_by=teacher,
            course_offering__teacher=teacher,
            course_offering__academic_session__id__in=active_sessions
        ).values('course_offering__id', 'date', 'shift').distinct()
        normal_lecture_count = normal_lectures.count()
        logger.debug(f"Step 5: Normal lectures (unique course_offering, date, shift): {normal_lecture_count}")
    except Exception as e:
        logger.error(f"Error querying normal lectures: {str(e)}")
        normal_lectures = Attendance.objects.none()
        normal_lecture_count = 0

    # Step 4: Get unique replacement lectures (recorded_by=teacher and teacher is replacement)
    try:
        replacement_lectures = Attendance.objects.filter(
            recorded_by=teacher,
            course_offering__id__in=replacement_course_offering_ids,
            course_offering__academic_session__id__in=active_sessions
        ).values('course_offering__id', 'date', 'shift').distinct()
        replacement_lecture_count = replacement_lectures.count()
        logger.debug(f"Step 6: Replacement lectures (unique course_offering, date, shift): {replacement_lecture_count}")
    except Exception as e:
        logger.error(f"Error querying replacement lectures: {str(e)}")
        replacement_lectures = Attendance.objects.none()
        replacement_lecture_count = 0

    # Step 5: Calculate replacement lecture salary
    teacher_details = teacher.details if hasattr(teacher, 'details') else None
    salary_per_lecture = teacher_details.salary_per_lecture if teacher_details else 0
    replacement_lecture_salary = replacement_lecture_count * salary_per_lecture
    logger.debug(f"Step 7: Replacement lecture salary: {replacement_lecture_salary}")

    # Step 6: Combine unique lectures for total count and details
    try:
        all_lectures = Attendance.objects.filter(
            recorded_by=teacher,
            course_offering__academic_session__id__in=active_sessions
        ).select_related('course_offering__course', 'course_offering__semester').order_by('-date')
        unique_lectures = all_lectures.values('course_offering__id', 'date', 'shift').distinct()
        total_lecture_count = unique_lectures.count()
        logger.debug(f"Step 8: Total unique lectures: {total_lecture_count}")
    except Exception as e:
        logger.error(f"Error combining lectures: {str(e)}")
        return render(request, 'faculty_staff/error.html', {
            'message': f'Error combining lecture data: {str(e)}'
        }, status=500)

    # Step 7: Prepare lecture details (one record per unique lecture)
    lecture_details = []
    for lecture in unique_lectures:
        lecture_record = all_lectures.filter(
            course_offering__id=lecture['course_offering__id'],
            date=lecture['date'],
            shift=lecture['shift']
        ).first()
        if lecture_record:
            is_replacement = lecture['course_offering__id'] in replacement_course_offering_ids
            role = 'Replacement' if is_replacement else 'Normal'
            course_shift = lecture_record.course_offering.shift
            display_shift = lecture['shift'] if lecture['shift'] else course_shift if course_shift != 'both' else 'N/A'
            lecture_details.append({
                'lecture': lecture_record,
                'role': role,
                'course_code': lecture_record.course_offering.course.code,
                'course_name': lecture_record.course_offering.course.name,
                'shift': display_shift,
                'date': lecture_record.date
            })
    logger.debug(f"Step 9: Lecture details prepared (count: {len(lecture_details)})")

    # Step 8: Calculate total salary based on unique lectures
    salary_lecture_count = normal_lecture_count + replacement_lecture_count
    total_salary = salary_lecture_count * salary_per_lecture
    logger.debug(f"Step 10: Lecture counts - Normal: {normal_lecture_count}, Replacement: {replacement_lecture_count}, Total: {total_lecture_count}, Salary lectures: {salary_lecture_count}, Total salary: {total_salary}")

    # Step 9: Get all years for filtering
    years_qs = all_lectures.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct().order_by('-year')
    years = list(years_qs)
    current_year = timezone.now().year
    selected_year = request.GET.get('year')
    try:
        selected_year = int(selected_year)
        if selected_year not in years:
            selected_year = current_year
    except (TypeError, ValueError):
        selected_year = current_year
    logger.debug(f"Step 11: Selected year: {selected_year}, Available years: {years}")

    # Step 10: Monthly statistics
    monthly_stats = []
    current_month = timezone.now().month if selected_year == current_year else 1
    for month in range(1, 13):
        month_lectures = all_lectures.filter(date__year=selected_year, date__month=month)
        month_unique_lectures = month_lectures.values('course_offering__id', 'date', 'shift').distinct()
        month_normal = month_unique_lectures.filter(
            course_offering__teacher=teacher,
            course_offering__replacement_teacher__isnull=True
        )
        month_replacement = month_unique_lectures.filter(
            course_offering__id__in=replacement_course_offering_ids
        )
        month_salary = (month_normal.count() + month_replacement.count()) * salary_per_lecture
        monthly_stats.append({
            'month': calendar.month_name[month],
            'normal_count': month_normal.count(),
            'replacement_count': month_replacement.count(),
            'salary': month_salary,
            'is_current': (month == current_month and selected_year == current_year)
        })
    logger.debug(f"Step 12: Monthly stats generated for {selected_year}")

    # Step 11: Course-wise statistics
    course_stats = all_lectures.filter(date__year=selected_year).values(
        'course_offering__course__code',
        'course_offering__course__name',
        'course_offering__shift'
    ).annotate(
        normal_count=Count('id', filter=Q(
            recorded_by=teacher,
            course_offering__teacher=teacher,
            course_offering__replacement_teacher__isnull=True   
        ), distinct=True),
        replacement_count=Count('id', filter=Q(
            recorded_by=teacher,
            course_offering__id__in=replacement_course_offering_ids
        ), distinct=True),
        salary=Count('id', filter=Q(recorded_by=teacher), distinct=True) * Value(salary_per_lecture)
    ).order_by('-normal_count', '-replacement_count')
    logger.debug(f"Step 13: Course stats generated")

    # Step 12: Recent lectures (last 10)
    recent_lectures = lecture_details[:10]
    logger.debug(f"Step 14: Recent lectures prepared (count: {len(recent_lectures)})")

    context = {
        'teacher': teacher,
        'course_offerings': course_offerings,
        'replacement_course_offerings': replacement_course_offerings,
        'normal_lecture_count': normal_lecture_count,
        'replacement_lecture_count': replacement_lecture_count,
        'total_lecture_count': total_lecture_count,
        'salary_lecture_count': salary_lecture_count,
        'salary_per_lecture': salary_per_lecture,
        'total_salary': total_salary,
        'replacement_lecture_salary': replacement_lecture_salary,
        'monthly_stats': monthly_stats,
        'course_stats': course_stats,
        'recent_lectures': recent_lectures,
        'years': years,
        'selected_year': selected_year,
        'current_year': current_year,
    }
    return render(request, 'faculty_staff/teacher_lecture_details.html', context)



@hod_required
def session_students(request, session_id=None):
    hod_department = request.user.teacher_profile.department
    programs = Program.objects.filter(department=hod_department)
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    
    students = Student.objects.none()
    session = None
    students_by_program = {}
    
    # Handle status updates (both bulk and single)
    if request.method == 'POST' and 'update_status' in request.POST:
        student_ids = request.POST.getlist('student_ids')
        status = request.POST.get('status')
        
        if not student_ids or not status:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'No students selected or status not specified.'}, status=400)
            messages.error(request, 'No students selected or status not specified.')
            return redirect('faculty_staff:session_students', session_id=session_id)
        
        try:
            # Update status for selected students
            # Convert string IDs to integers and filter by applicant_id (primary key)
            student_ids = [int(sid) for sid in student_ids if sid.isdigit()]
            updated = Student.objects.filter(
                applicant_id__in=student_ids,
                program__department=hod_department  # Security: Only update students in HOD's department
            ).update(current_status=status)
            
            message = f'Successfully updated status for {updated} student(s).'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': message,
                    'updated_count': updated
                })
                
            messages.success(request, message)
            return redirect('faculty_staff:session_students', session_id=session_id)
            
        except Exception as e:
            error_message = f'Error updating student statuses: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_message}, status=500)
            messages.error(request, error_message)
            return redirect('faculty_staff:session_students', session_id=session_id)
    
    if session_id:
        # Get the selected session
        session = get_object_or_404(AcademicSession, id=session_id)
        
        # Get students for this session and department's programs
        students = Student.objects.filter(
            applicant__session=session,
            program__in=programs
        ).select_related('applicant', 'program').order_by('program__name', 'university_roll_no')
        
        # Get the selected program filter if any
        program_id = request.GET.get('program_id')
        if program_id and program_id != 'all':
            students = students.filter(program_id=program_id)
        
        # Group students by program
        for program in programs:
            program_students = students.filter(program=program)
            if program_students.exists():
                students_by_program[program] = program_students
    
    # Status choices for the dropdown
    status_choices = dict(Student._meta.get_field('current_status').choices)
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Try to get session_id from GET parameters if not in URL
            if not session_id:
                session_id = request.GET.get('session_id')
                if not session_id:
                    return JsonResponse({'error': 'Session ID is required'}, status=400)
                
                session = get_object_or_404(AcademicSession, id=session_id)
                
                # Re-fetch students with the new session_id
                students = Student.objects.filter(
                    applicant__session=session,
                    program__in=programs
                ).select_related('applicant', 'program').order_by('program__name', 'university_roll_no')
                
                # Re-apply program filter if any
                program_id = request.GET.get('program_id')
                if program_id and program_id != 'all':
                    students = students.filter(program_id=program_id)
                
                # Re-group students by program
                students_by_program = {}
                for program in programs:
                    program_students = students.filter(program=program)
                    if program_students.exists():
                        students_by_program[program] = program_students
            
            html = render_to_string('faculty_staff/includes/student_list.html', {
                'students_by_program': students_by_program,
                'session': session,
                'programs': programs,
                'status_choices': status_choices,
            })
            return JsonResponse({'html': html})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    # For regular GET requests
    context = {
        'session': session,
        'department': hod_department,
        'academic_sessions': academic_sessions,
        'students_by_program': students_by_program,
        'programs': programs,
        'status_choices': status_choices,
    }
    return render(request, 'faculty_staff/session_students.html', context)


@hod_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    hod_department = request.user.teacher_profile.department
    if student.program.department != hod_department:
        return redirect('faculty_staff:dashboard')

    academic_qualifications = student.applicant.academic_qualifications.all()
    extra_curricular_activities = student.applicant.extra_curricular_activities.all()
    semester_enrollments = student.semester_enrollments.all().order_by('-enrollment_date')

    context = {
        'student': student,
        'academic_qualifications': academic_qualifications,
        'extra_curricular_activities': extra_curricular_activities,
        'semester_enrollments': semester_enrollments,
    }
    return render(request, 'faculty_staff/student_details.html', context)


@hod_required
@require_POST
def edit_enrollment_status(request):
    enrollment_id = request.POST.get('enrollment_id')
    new_status = request.POST.get('status')
    
    enrollment = get_object_or_404(StudentSemesterEnrollment, id=enrollment_id)
    student = enrollment.student
    hod_department = request.user.teacher_profile.department
    if student.program.department != hod_department:
        return redirect('faculty_staff:dashboard')

    allowed_statuses = dict(StudentSemesterEnrollment._meta.get_field('status').choices).keys()
    
    if new_status in allowed_statuses:
        enrollment.status = new_status
        enrollment.save()  
        # Update student's current semester based on the new status
        if new_status in ['completed', 'dropped']:
            latest_enrollment = StudentSemesterEnrollment.objects.filter(
                student=student,
                status='enrolled'
            ).exclude(id=enrollment.id).order_by('-enrollment_date').first()
            if latest_enrollment:
                student.current_semester = latest_enrollment.semester
            else:
                first_semester = Semester.objects.filter(
                    program=student.program,
                    number=1
                ).first()
                student.current_semester = first_semester
            student.save()
        elif new_status == 'enrolled':
            student.current_semester = enrollment.semester
            student.save()

    return redirect('faculty_staff:student_detail', student_id=student.pk)


# Course Form Definition
class CourseForm(forms.Form):
    code = forms.CharField(max_length=10, required=True, help_text="Enter the unique course code (e.g., CS101).")
    name = forms.CharField(max_length=200, required=True, help_text="Enter the full name of the course.")
    credits = forms.IntegerField(min_value=1, required=True, help_text="Enter the number of credit hours.")
    lab_work = forms.IntegerField(min_value=0, required=False, help_text="Enter the number of lab hours per week for this course (if applicable).")
    is_active = forms.BooleanField(required=False, initial=True, help_text="Check this if the course is active.")
    opt = forms.BooleanField(required=False, initial=True, help_text="Check this if the course is just optional")
    description = forms.CharField(widget=forms.Textarea, required=False, help_text="Provide a brief description or syllabus summary for the course.")
    prerequisites = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Select any courses that are required to be completed before taking this course (optional)."
    )


@hod_required
def add_course(request):
    hod_department = request.user.teacher_profile.department
    form = CourseForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        if Course.objects.filter(code=code).exists():
            form.add_error('code', 'This course code already exists.')
        else:
            # Create the course first
            course = Course.objects.create(
                code=code,
                name=form.cleaned_data['name'],
                credits=form.cleaned_data['credits'],
                lab_work=form.cleaned_data['lab_work'],
                is_active=form.cleaned_data['is_active'],
                opt=form.cleaned_data['opt'],
                description=form.cleaned_data['description']
            )
            
            # Add prerequisites if any selected
            prerequisites = form.cleaned_data['prerequisites']
            if prerequisites:
                course.prerequisites.set(prerequisites)
            
            messages.success(request, f'Course {code} added successfully.')
            return redirect('faculty_staff:course_offerings')

    context = {
        'form': form,
        'department': hod_department,
        'session_id': None,
    }
    return render(request, 'faculty_staff/add_course.html', context)


@hod_required
def course_offerings(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/course_offerings.html', {
            'error': 'Unauthorized access. Only Heads of Department can access this page.'
        })

    hod_department = request.user.teacher_profile.department
    if not hod_department:
        return render(request, 'faculty_staff/course_offerings.html', {
            'error': 'HOD must be associated with a department.'
        })

    # Get filter parameters from GET request
    session_id = request.GET.get('session_id')
    program_id = request.GET.get('program_id')
    semester_id = request.GET.get('semester_id')
    page = request.GET.get('page', 1)

    # Base querysets with active filters
    academic_sessions = AcademicSession.objects.filter(is_active=True).order_by('-start_year')
    programs = Program.objects.filter(department=hod_department, is_active=True)
    teachers = Teacher.objects.filter(is_active=True, department=hod_department)
    semesters = Semester.objects.filter(program__in=programs, is_active=True).distinct()

    # Filter course offerings for active semesters and programs
    course_offerings = CourseOffering.objects.filter(
        department=hod_department,
        semester__is_active=True,
        program__is_active=True   
    ).order_by('academic_session__start_year', 'program__name', 'semester__name', 'course__code')
    if session_id:
        course_offerings = course_offerings.filter(academic_session_id=session_id)
    if program_id:
        course_offerings = course_offerings.filter(program_id=program_id)
    if semester_id:
        course_offerings = course_offerings.filter(semester_id=semester_id)
    course_offerings = course_offerings.select_related('course', 'teacher', 'program', 'department', 'academic_session', 'semester')

    # Pagination for course offerings
    paginator = Paginator(course_offerings, 20)  # 10 items per page
    page_obj = paginator.get_page(page)

    # Filter timetable slots for active semesters and programs
    timetable_slots = TimetableSlot.objects.filter(
        course_offering__department=hod_department,
        course_offering__semester__is_active=True,
        course_offering__program__is_active=True
    ).order_by('course_offering__academic_session__start_year', 'course_offering__program__name', 'course_offering__semester__name', 'day', 'start_time')
    if session_id:
        timetable_slots = timetable_slots.filter(course_offering__academic_session_id=session_id)
    if program_id:
        timetable_slots = timetable_slots.filter(course_offering__program_id=program_id)
    if semester_id:
        timetable_slots = timetable_slots.filter(course_offering__semester_id=semester_id)
    timetable_slots = timetable_slots.select_related('course_offering__course', 'course_offering__teacher', 'course_offering__program', 'course_offering__semester', 'venue')

    # Pagination for timetable slots
    timetable_paginator = Paginator(timetable_slots, 20)  # 10 items per page
    timetable_page_obj = timetable_paginator.get_page(page)

    context = {
        'academic_sessions': academic_sessions,
        'semesters': semesters,
        'programs': programs,
        'teachers': teachers,
        'course_offerings': page_obj,  # Pass paginated object
        'timetable_slots': timetable_page_obj,  # Pass paginated object
        'department': hod_department,
        'session_id': session_id,
        'program_id': program_id,
        'semester_id': semester_id,
    }
    return render(request, 'faculty_staff/course_offerings.html', context)

@hod_required
def timetable_schedule(request, offering_id):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/timetable_schedule.html', {
            'error': 'Unauthorized access. Only Heads of Department can access this page.'
        })

    hod_department = request.user.teacher_profile.department
    if not hod_department:
        return render(request, 'faculty_staff/timetable_schedule.html', {
            'error': 'HOD must be associated with a department.'
        })

    try:
        course_offering = CourseOffering.objects.get(
            id=offering_id,
            department=hod_department
        )
    except CourseOffering.DoesNotExist:
        return render(request, 'faculty_staff/timetable_schedule.html', {
            'error': 'Course offering not found or you do not have permission to access it.'
        })

    timetable_slots = TimetableSlot.objects.filter(
        course_offering=course_offering
    ).select_related('venue')

    context = {
        'course_offering': course_offering,
        'timetable_slots': timetable_slots,
        'department': hod_department,
        'days_of_week': TimetableSlot.DAYS_OF_WEEK
    }
    return render(request, 'faculty_staff/timetable_schedule.html', context)

def search_courses(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        courses = Course.objects.filter(
            Q(code__icontains=search_query) | Q(name__icontains=search_query)
        ).values('id', 'code', 'name')[:10]
        return JsonResponse({
            'results': [{'id': course['id'], 'text': f"{course['code']}: {course['name']}"} for course in courses],
            'more': False
        })
    return JsonResponse({'results': [], 'more': False})


def search_teachers(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        teachers = Teacher.objects.filter(
            Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query),
            is_active=True,
            # department=request.user.teacher_profile.department
        ).values('id', 'user__first_name', 'user__last_name', 'department__name')[:10]
        return JsonResponse({
            'results': [
                {
                    'id': teacher['id'],
                    'text': f"{teacher['user__first_name']} {teacher['user__last_name']} ({teacher['department__name']})"
                } for teacher in teachers
            ],
            'more': False
        })
    return JsonResponse({'results': [], 'more': False})

def get_academic_sessions(request):
    sessions = AcademicSession.objects.filter(is_active=True)
    results = [{'id': session.id, 'text': session.name} for session in sessions]
    return JsonResponse({'results': results})


def search_programs(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        # academic_session_id = request.GET.get('academic_session_id', '')
        page = int(request.GET.get('page', 1))
        per_page = 10
        hod_department = request.user.teacher_profile.department
        if not hod_department:
            return JsonResponse({'results': [], 'pagination': {'more': False}})

        programs = Program.objects.filter(department=hod_department)

        if search_query:
            programs = programs.filter(
                Q(name__icontains=search_query) | Q(department__name__icontains=search_query)
            )

        start = (page - 1) * per_page
        end = start + per_page
        paginated_programs = programs[start:end]

        results = [
            {'id': program.id, 'text': f"{program.name} ({program.department.name if program.department else 'N/A'})"}
            for program in paginated_programs
        ]

        return JsonResponse({
            'results': results,
            'pagination': {'more': end < programs.count()}
        })
    return JsonResponse({'results': [], 'pagination': {'more': False}})


def search_semesters(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        program_id = request.GET.get('program_id')
        academic_session_id = request.GET.get('academic_session_id')

        filters = Q(name__icontains=search_query) | Q(program__name__icontains=search_query)
        filters &= Q(is_active=True)
        if program_id:
            filters &= Q(program_id=program_id)
        if academic_session_id:
            filters &= Q(session_id=academic_session_id)

        semesters = Semester.objects.filter(filters).values(
            'id', 'name', 'program__name', 'session__name'
        )[:10]

        return JsonResponse({
            'results': [
                {
                    'id': semester['id'],
                    'text': f"{semester['name']} (Session: {semester['session__name']}) (Program: {semester['program__name']})"
                } for semester in semesters
            ],
            'more': False
        })
    return JsonResponse({'results': [], 'more': False})


def get_offering_type_choices(request):
    choices = [{'id': value, 'text': label} for value, label in CourseOffering.OFFERING_TYPES]
    return JsonResponse({'results': choices})


def search_venues(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        per_page = 10
        hod_department = request.user.teacher_profile.department
        venues = Venue.objects.filter(
            Q(name__icontains=search_query),
            department=hod_department,
            is_active=True
        )
        start = (page - 1) * per_page
        end = start + per_page
        paginated_venues = venues[start:end]
        results = [
            {'id': venue.id, 'text': f"{venue.name} (Room no.: {venue.capacity})"}
            for venue in paginated_venues
        ]
        return JsonResponse({
            'results': results,
            'pagination': {'more': end < venues.count()}
        })
    return JsonResponse({'results': [], 'pagination': {'more': False}})


@transaction.atomic
def save_course_offering(request):
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method or insufficient permissions.'
        })

    course_id = request.POST.get('course_id')
    teacher_id = request.POST.get('teacher_id')
    program_id = request.POST.get('program_id')
    semester_id = request.POST.get('semester_id')
    academic_session_id = request.POST.get('academic_session_id')
    offering_type = request.POST.get('offering_type')
    shift = request.POST.get('shift')

    required_fields = {
        'course_id': 'Course',
        'teacher_id': 'Teacher',     
        'program_id': 'Program',
        'semester_id': 'Semester',
        'academic_session_id': 'Academic Session',
        'offering_type': 'Offering Type',
        'shift': 'Shift'
    }
    missing_fields = [field_name for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        return JsonResponse({
            'success': False,
            'message': f'Missing required fields: {", ".join([required_fields[field] for field in missing_fields])}'
        })

    valid_offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
    if offering_type not in valid_offering_types:
        return JsonResponse({
            'success': False,
            'message': 'Invalid offering type selected.'
        })

    valid_shifts = ['morning', 'evening', 'both']
    if shift not in valid_shifts:
        return JsonResponse({
            'success': False,
            'message': 'Invalid shift selected.'
        })

    try:  
        course = Course.objects.get(id=course_id)
        teacher = Teacher.objects.get(id=teacher_id, is_active=True)
        program = Program.objects.get(id=program_id)
        semester = Semester.objects.get(id=semester_id)
        academic_session = AcademicSession.objects.get(id=academic_session_id)
    except (Course.DoesNotExist, Teacher.DoesNotExist, Program.DoesNotExist, 
            Semester.DoesNotExist, AcademicSession.DoesNotExist) as e:
        return JsonResponse({
            'success': False,
            'message': 'One or more selected items no longer exist.'
        })

    # Check for existing offerings with the same credentials
    existing_offerings = CourseOffering.objects.filter(
        course=course,
        program=program,
        academic_session=academic_session,
        semester=semester,
        offering_type=offering_type,
        shift=shift
    )
    if existing_offerings.exists():
        return JsonResponse({
            'success': False,
            'message': 'This exact course offering already exists.'
        })

    # New Validation: Check if the course is already assigned to another teacher with the same credentials
    conflicting_offerings = CourseOffering.objects.filter(
        course=course,
        program=program,
        academic_session=academic_session,
        semester=semester,
        offering_type=offering_type
    ).exclude(teacher__isnull=True).exclude(teacher=teacher)
    if conflicting_offerings.exists():
        return JsonResponse({
            'success': False,
            'message': 'This course is already assigned to another teacher with the same credentials.'
        })

    # New Validation: Check teacher shift conflicts
    teacher_existing_offerings = CourseOffering.objects.filter(
        teacher=teacher,
        course=course,
        program=program,
        academic_session=academic_session,
        semester=semester,
        offering_type=offering_type
    )
    for existing_offering in teacher_existing_offerings:
        existing_shift = existing_offering.shift
        if shift == 'both' and existing_shift in ['morning', 'evening']:
            return JsonResponse({
                'success': False,
                'message': 'Teacher is already assigned this course for a specific shift (morning or evening) and cannot be assigned for both shifts.'
            })
        if existing_shift == 'both' and shift in ['morning', 'evening']:
            return JsonResponse({
                'success': False,
                'message': 'Teacher is already assigned this course for both shifts and cannot be assigned for a specific shift (morning or evening).'
            })

    active_students = Student.objects.filter(
        program=program,
        current_status='active'
    )
    if not active_students.exists():
        return JsonResponse({
            'success': False,
            'message': 'No active students found for this program and semester.'
        })

    compatible_students = []
    for student in active_students:
        applicant_shift = student.applicant.shift
        if shift == 'both' or applicant_shift == shift:
            compatible_students.append(student)

    if not compatible_students:
        return JsonResponse({
            'success': False,
            'message': 'No students have a compatible shift preference for this course offering.'
        })

    try:
        offering = CourseOffering.objects.create(
            course=course,
            teacher=teacher,
            department=program.department,
            program=program,
            academic_session=academic_session,
            semester=semester,
            is_active=True,
            offering_type=offering_type,
            shift=shift,
            current_enrollment=0   
        )

        enrolled_count = 0
        enrolled_student_names = []
        for student in compatible_students:
            semester_enrollment, created = StudentSemesterEnrollment.objects.get_or_create(
                student=student,
                semester=semester,
                defaults={'status': 'enrolled'}
            )
            course_enrollment, created = CourseEnrollment.objects.get_or_create(
                student_semester_enrollment=semester_enrollment,
                course_offering=offering,
                defaults={'status': 'enrolled'}
            )
            if created or course_enrollment.status != 'enrolled':
                course_enrollment.status = 'enrolled'
                course_enrollment.save()
                enrolled_count += 1
                enrolled_student_names.append(student.applicant.full_name)

        offering.current_enrollment = enrolled_count
        offering.save()
        
        return JsonResponse({  
            'success': True,
            'message': f'Successfully created course offering for {course.code} ({shift.capitalize()} shift) with {enrolled_count} students enrolled.',
            'offering_id': offering.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving course offering: {str(e)}'
        })
        
@hod_required
def save_venue(request):
    name = request.POST.get('name')
    capacity = request.POST.get('capacity')
    department_id = request.POST.get('department_id')

    required_fields = {
        'name': 'Venue Name',
        'capacity': 'Capacity',
        'department_id': 'Department'
    }
    missing_fields = [field_name for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        return JsonResponse({
            'success': False,
            'message': f'Missing required fields: {", ".join([required_fields[field] for field in missing_fields])}'
        })

    try:
        capacity = int(capacity)
        if capacity <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Capacity must be a positive number.'
            })
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Capacity must be a valid number.'
        })

    hod_department = request.user.teacher_profile.department
    if not hod_department or str(department_id) != str(hod_department.id):
        return JsonResponse({
            'success': False,
            'message': 'Invalid department or you do not have permission to add venues for this department.'
        })

    try:
        department = Department.objects.get(id=department_id)
    except Department.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Department does not exist.'
        })

    if Venue.objects.filter(name=name, department=department).exists():
        return JsonResponse({
            'success': False,
            'message': f'Venue "{name}" already exists in this department.'
        })

    try:
        venue = Venue.objects.create(
            name=name,
            capacity=capacity,
            department=department,
            is_active=True
        )
        return JsonResponse({
            'success': True,
            'message': f'Venue "{venue.name}" created successfully.',
            'venue_id': venue.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating venue: {str(e)}'
        })
        
@hod_required
@transaction.atomic
def save_timetable_slot(request):
    logger.info("Starting save_timetable_slot view for user: %s", request.user)
    
    # Check request method and permissions
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        logger.warning("Invalid request method or insufficient permissions for user: %s", request.user)
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method or insufficient permissions.'
        }, status=403)

    # Validate course offering ID
    course_offering_id = request.POST.get('course_offering_id')
    if not course_offering_id:
        logger.error("Course Offering ID is required")
        return JsonResponse({
            'success': False,
            'message': 'Course Offering ID is required.',
            'error_field': 'course_offering_id'
        }, status=400)

    # Retrieve course offering
    try:
        course_offering = CourseOffering.objects.get(
            id=course_offering_id,
            department=request.user.teacher_profile.department
        )
        logger.debug("Found course offering: %s (ID: %s)", course_offering.course.code, course_offering_id)
    except CourseOffering.DoesNotExist:
        logger.error("Course offering ID %s does not exist for department %s", 
                     course_offering_id, request.user.teacher_profile.department)
        return JsonResponse({
            'success': False,
            'message': 'Selected course offering does not exist.',
            'error_field': 'course_offering_id'
        }, status=404)

    shift = course_offering.shift
    logger.debug("Course offering shift: %s", shift)

    def validate_and_convert_time(start_time_str, end_time_str, shift_type):
        logger.debug("Validating %s times: start=%s, end=%s", shift_type, start_time_str, end_time_str)
        if not start_time_str or not end_time_str:
            logger.warning("%s start and end times are required", shift_type.capitalize())
            return False, None, None, f"{shift_type.capitalize()} start and end times are required."
        try:
            start_h, start_m = map(int, start_time_str.split(':'))
            end_h, end_m = map(int, end_time_str.split(':'))
            start_t = time(start_h, start_m)
            end_t = time(end_h, end_m)
            if start_t >= end_t:
                logger.warning("%s end time must be after start time", shift_type.capitalize())
                return False, None, None, f"{shift_type.capitalize()} end time must be after start time."
            logger.debug("%s times validated: %s to %s", shift_type, start_t, end_t)
            return True, start_t, end_t, None
        except (ValueError, IndexError) as e:
            logger.error("Invalid %s time format: %s", shift_type, str(e))
            return False, None, None, f"Invalid {shift_type} time format."

    try:
        if shift == 'both':
            morning_days = request.POST.getlist('morning_day[]')
            morning_start_time = request.POST.get('morning_start_time')
            morning_end_time = request.POST.get('morning_end_time')
            morning_venue_id = request.POST.get('morning_venue_id')
            evening_days = request.POST.getlist('evening_day[]')
            evening_start_time = request.POST.get('evening_start_time')
            evening_end_time = request.POST.get('evening_end_time')
            evening_venue_id = request.POST.get('evening_venue_id')

            logger.debug("Morning shift data: days=%s, start=%s, end=%s, venue_id=%s", 
                         morning_days, morning_start_time, morning_end_time, morning_venue_id)
            logger.debug("Evening shift data: days=%s, start=%s, end=%s, venue_id=%s", 
                         evening_days, evening_start_time, evening_end_time, evening_venue_id)

            required_fields = {
                'morning_day': morning_days,
                'morning_start_time': morning_start_time,
                'morning_end_time': morning_end_time,
                'morning_venue_id': morning_venue_id,
                'evening_day': evening_days,
                'evening_start_time': evening_start_time,
                'evening_end_time': evening_end_time,
                'evening_venue_id': evening_venue_id
            }
            missing_fields = [key for key, value in required_fields.items() if not value]
            if missing_fields:
                logger.error("Missing required fields for shift 'both': %s", ", ".join(missing_fields))
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'error_field': missing_fields[0]
                }, status=400)

            morning_valid, morning_start_t, morning_end_t, morning_error = validate_and_convert_time(
                morning_start_time, morning_end_time, 'morning')
            evening_valid, evening_start_t, evening_end_t, evening_error = validate_and_convert_time(
                evening_start_time, evening_end_time, 'evening')
            if not morning_valid:
                logger.error("Morning time validation failed: %s", morning_error)
                return JsonResponse({
                    'success': False,
                    'message': morning_error,
                    'error_field': 'morning_start_time'
                }, status=400)
            if not evening_valid:
                logger.error("Evening time validation failed: %s", evening_error)
                return JsonResponse({
                    'success': False,
                    'message': evening_error,
                    'error_field': 'evening_start_time'
                }, status=400)

            try:
                morning_venue = Venue.objects.get(
                    id=morning_venue_id, 
                    department=request.user.teacher_profile.department, 
                    is_active=True
                )
                logger.debug("Morning venue found: %s (ID: %s)", morning_venue.name, morning_venue_id)
            except Venue.DoesNotExist:
                logger.error("Morning venue ID %s does not exist or is not active", morning_venue_id)
                return JsonResponse({
                    'success': False,
                    'message': 'Selected morning venue does not exist or is not active.',
                    'error_field': 'morning_venue_id'
                }, status=404)

            try:
                evening_venue = Venue.objects.get(
                    id=evening_venue_id, 
                    department=request.user.teacher_profile.department, 
                    is_active=True
                )
                logger.debug("Evening venue found: %s (ID: %s)", evening_venue.name, evening_venue_id)
            except Venue.DoesNotExist:
                logger.error("Evening venue ID %s does not exist or is not active", evening_venue_id)
                return JsonResponse({
                    'success': False,
                    'message': 'Selected evening venue does not exist or is not active.',
                    'error_field': 'evening_venue_id'
                }, status=404)

            saved_slots = []
            for day in morning_days:
                logger.debug("Creating morning slot for %s on %s", course_offering.course.code, day)
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=morning_start_t,
                    end_time=morning_end_t,
                    venue=morning_venue
                )
                try:
                    slot.clean()
                    slot.save()
                    saved_slots.append(f"{dict(TimetableSlot.DAYS_OF_WEEK)[day]} (Morning)")
                    logger.info("Saved morning slot for %s on %s", course_offering.course.code, day)
                except ValidationError as e:
                    logger.error("Validation error for morning slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"Failed to schedule morning slot on {dict(TimetableSlot.DAYS_OF_WEEK)[day]}: {str(e)}",
                        'error_field': 'morning_day'
                    }, status=400)
                except IntegrityError as e:
                    logger.error("Integrity error for morning slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"A timetable slot for {course_offering.course.code} on {dict(TimetableSlot.DAYS_OF_WEEK)[day]} at {morning_start_t.strftime('%H:%M')}–{morning_end_t.strftime('%H:%M')} in {morning_venue.name} already exists.",
                        'error_field': 'morning_day'
                    }, status=400)
            for day in evening_days:
                logger.debug("Creating evening slot for %s on %s", course_offering.course.code, day)
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=evening_start_t,
                    end_time=evening_end_t,
                    venue=evening_venue
                )
                try:
                    slot.clean()
                    slot.save()
                    saved_slots.append(f"{dict(TimetableSlot.DAYS_OF_WEEK)[day]} (Evening)")
                    logger.info("Saved evening slot for %s on %s", course_offering.course.code, day)
                except ValidationError as e:
                    logger.error("Validation error for evening slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"Failed to schedule evening slot on {dict(TimetableSlot.DAYS_OF_WEEK)[day]}: {str(e)}",
                        'error_field': 'evening_day'
                    }, status=400)
                except IntegrityError as e:
                    logger.error("Integrity error for evening slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"A timetable slot for {course_offering.course.code} on {dict(TimetableSlot.DAYS_OF_WEEK)[day]} at {evening_start_t.strftime('%H:%M')}–{evening_end_t.strftime('%H:%M')} in {evening_venue.name} already exists.",
                        'error_field': 'evening_day'
                    }, status=400)

            logger.info("Successfully scheduled %d timetable slots for %s: %s", 
                        len(saved_slots), course_offering.course.code, ", ".join(saved_slots))
            return JsonResponse({
                'success': True,
                'message': f'Timetable slots scheduled for {course_offering.course.code} on {", ".join(saved_slots)}.'
            }, status=200)

        else:
            days = request.POST.getlist('day[]')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            venue_id = request.POST.get('venue_id')

            logger.debug("Single shift data: days=%s, start=%s, end=%s, venue_id=%s", 
                         days, start_time, end_time, venue_id)

            required_fields = {
                'day': days,
                'start_time': start_time,
                'end_time': end_time,
                'venue_id': venue_id
            }
            missing_fields = [key for key, value in required_fields.items() if not value]
            if missing_fields:
                logger.error("Missing required fields for shift '%s': %s", shift, ", ".join(missing_fields))
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'error_field': missing_fields[0]
                }, status=400)

            try:
                venue = Venue.objects.get(
                    id=venue_id, 
                    department=request.user.teacher_profile.department, 
                    is_active=True
                )
                logger.debug("Venue found: %s (ID: %s)", venue.name, venue_id)
            except Venue.DoesNotExist:
                logger.error("Venue ID %s does not exist or is not active", venue_id)
                return JsonResponse({
                    'success': False,
                    'message': 'Selected venue does not exist or is not active.',
                    'error_field': 'venue_id'
                }, status=404)

            valid_time, start_t, end_t, error_msg = validate_and_convert_time(start_time, end_time, shift)
            if not valid_time:
                logger.error("Time validation failed for shift '%s': %s", shift, error_msg)
                return JsonResponse({
                    'success': False,
                    'message': error_msg,
                    'error_field': 'start_time'
                }, status=400)

            saved_days = []
            for day in days:
                logger.debug("Creating slot for %s on %s", course_offering.course.code, day)
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=start_t,
                    end_time=end_t,
                    venue=venue
                )
                try:
                    slot.clean()
                    slot.save()
                    saved_days.append(dict(TimetableSlot.DAYS_OF_WEEK)[day])
                    logger.info("Saved slot for %s on %s", course_offering.course.code, day)
                except ValidationError as e:
                    logger.error("Validation error for slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"Failed to schedule slot on {dict(TimetableSlot.DAYS_OF_WEEK)[day]}: {str(e)}",
                        'error_field': 'day'
                    }, status=400)
                except IntegrityError as e:
                    logger.error("Integrity error for slot on %s: %s", day, str(e))
                    return JsonResponse({
                        'success': False,
                        'message': f"A timetable slot for {course_offering.course.code} on {dict(TimetableSlot.DAYS_OF_WEEK)[day]} at {start_t.strftime('%H:%M')}–{end_t.strftime('%H:%M')} in {venue.name} already exists.",
                        'error_field': 'day'
                    }, status=400)

            logger.info("Successfully scheduled %d timetable slots for %s: %s", 
                        len(saved_days), course_offering.course.code, ", ".join(saved_days))
            return JsonResponse({
                'success': True,
                'message': f'Timetable slot(s) scheduled for {course_offering.course.code} on {", ".join(saved_days)}.'
            }, status=200)

    except ValueError as e:
        logger.error("ValueError in save_timetable_slot for %s: %s", course_offering.course.code, str(e))
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error_field': 'general'
        }, status=400)
    except Exception as e:
        logger.exception("Unexpected error in save_timetable_slot for %s: %s", course_offering.course.code, str(e))
        return JsonResponse({
            'success': False,
            'message': 'An unexpected error occurred while scheduling the timetable. Please try again.',
            'error_field': 'general'
        }, status=500)   
        
        
@hod_required
def search_timetable_slots(request):
    course_offering_id = request.GET.get('course_offering_id')
    days = request.GET.getlist('day[]')  # Can be empty
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    venue_id = request.GET.get('venue_id')

    logger.debug("Searching timetable slots: course_offering_id=%s, days=%s, start_time=%s, end_time=%s, venue_id=%s",
                 course_offering_id, days, start_time, end_time, venue_id)

    # Validate required parameters, allowing days to be optional
    if not all([course_offering_id, start_time, end_time, venue_id]):
        logger.error("Missing required parameters: course_offering_id=%s, start_time=%s, end_time=%s, venue_id=%s",
                     course_offering_id, start_time, end_time, venue_id)
        return JsonResponse({
            'success': False,
            'message': 'Required parameters (course_offering_id, start_time, end_time, venue_id) are required.'
        }, status=400)

    # Retrieve course offering
    try:
        course_offering = CourseOffering.objects.get(
            id=course_offering_id,
            department=request.user.teacher_profile.department
        )
    except CourseOffering.DoesNotExist:
        logger.error("Course offering ID %s does not exist for department %s",
                     course_offering_id, request.user.teacher_profile.department)
        return JsonResponse({
            'success': False,
            'message': 'Selected course offering does not exist.'
        }, status=404)

    # Retrieve venue
    try:
        venue = Venue.objects.get(
            id=venue_id,
            department=request.user.teacher_profile.department,
            is_active=True
        )
    except Venue.DoesNotExist:
        logger.error("Venue ID %s does not exist or is not active", venue_id)
        return JsonResponse({
            'success': False,
            'message': 'Selected venue does not exist or is not active.'
        }, status=404)

    # Parse start and end times
    try:
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        start_t = time(start_h, start_m)
        end_t = time(end_h, end_m)
        if start_t >= end_t:
            logger.error("Invalid time range: start_time=%s, end_time=%s", start_time, end_time)
            return JsonResponse({
                'success': False,
                'message': 'End time must be after start time.'
            }, status=400)
    except (ValueError, IndexError):
        logger.error("Invalid time format: start_time=%s, end_time=%s", start_time, end_time)
        return JsonResponse({
            'success': False,
            'message': 'Invalid start or end time format.'
        }, status=400)

    # Check for overlapping slots
    query = TimetableSlot.objects.filter(
        course_offering=course_offering,
        venue=venue,
        start_time__lt=end_t,  # Existing slot starts before new slot ends
        end_time__gt=start_t   # Existing slot ends after new slot starts
    )
    if days:  # Only filter by days if provided
        query = query.filter(day__in=days)

    slots = query.values('day', 'start_time', 'end_time', 'venue__name')

    logger.debug("Found %d overlapping slots: %s", len(slots), list(slots))

    return JsonResponse({
        'success': True,
        'slots': list(slots)
    }, status=200)      
        
        
@hod_required
@require_GET
def get_course_offering(request):
    offering_id = request.GET.get('offering_id')
    try:
        offering = CourseOffering.objects.get(id=offering_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': offering.id,
                'course': {'id': offering.course.id, 'text': offering.course.name},
                'offering_type': {'id': offering.offering_type, 'text': offering.get_offering_type_display()},
                'teacher': {'id': offering.teacher.id, 'text': offering.teacher.user.get_full_name()} if offering.teacher else {'id': '', 'text': ''},
                'academic_session': {'id': offering.academic_session.id, 'text': offering.academic_session.name},
                'program': {'id': offering.program.id, 'text': offering.program.name},
                'semester': {'id': offering.semester.id, 'text': offering.semester.name},
                'shift': offering.shift,
                'is_active': offering.is_active
            }
        })
    except CourseOffering.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Course offering not found'})

@hod_required
@require_POST
def edit_course_offering(request):
    offering_id = request.POST.get('offering_id')
    try:
        offering = CourseOffering.objects.get(id=offering_id)
        offering.course = get_object_or_404(Course, id=request.POST.get('course_id'))
        offering.offering_type = request.POST.get('offering_type')
        offering.teacher = get_object_or_404(Teacher, id=request.POST.get('teacher_id')) if request.POST.get('teacher_id') else None
        offering.academic_session = get_object_or_404(AcademicSession, id=request.POST.get('academic_session_id'))
        offering.program = get_object_or_404(Program, id=request.POST.get('program_id'))
        offering.semester = get_object_or_404(Semester, id=request.POST.get('semester_id'))
        offering.shift = request.POST.get('shift')
        offering.is_active = request.POST.get('is_active') == 'on'
        offering.save()
        return JsonResponse({'success': True, 'message': 'Course offering updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_GET
def get_timetable_slot(request):
    slot_id = request.GET.get('slot_id')
    try:
        slot = TimetableSlot.objects.get(id=slot_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': slot.id,
                'course_offering': {'id': slot.course_offering.id, 'text': slot.course_offering.course.name},
                'day': slot.day,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'venue': {'id': slot.venue.id, 'text': slot.venue.name}
            }
        })
    except TimetableSlot.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Timetable slot not found'})

@hod_required
@require_POST
def edit_timetable_slot(request):
    slot_id = request.POST.get('slot_id')
    day = request.POST.get('day')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    venue_id = request.POST.get('venue_id')

    logger.debug("Editing timetable slot: slot_id=%s, day=%s, start_time=%s, end_time=%s, venue_id=%s",
                 slot_id, day, start_time, end_time, venue_id)

    # Validate required parameters
    if not all([slot_id, day, start_time, end_time, venue_id]):
        missing_params = [param for param, value in [
            ('slot_id', slot_id),
            ('day', day),
            ('start_time', start_time),
            ('end_time', end_time),
            ('venue_id', venue_id)
        ] if not value]
        logger.error("Missing required parameters: %s", ", ".join(missing_params))
        return JsonResponse({
            'success': False,
            'message': f'Missing required parameters: {", ".join(missing_params)}.'
        }, status=400)

    # Retrieve the slot
    try:
        slot = TimetableSlot.objects.get(
            id=slot_id,
            course_offering__department=request.user.teacher_profile.department
        )
    except TimetableSlot.DoesNotExist:
        logger.error("Timetable slot ID %s does not exist or is not accessible", slot_id)
        return JsonResponse({
            'success': False,
            'message': 'Timetable slot does not exist or is not accessible.'
        }, status=404)

    # Retrieve venue
    try:
        venue = Venue.objects.get(
            id=venue_id,
            department=request.user.teacher_profile.department,
            is_active=True
        )
    except Venue.DoesNotExist:
        logger.error("Venue ID %s does not exist or is not active", venue_id)
        return JsonResponse({
            'success': False,
            'message': 'Selected venue does not exist or is not active.'
        }, status=404)

    # Parse start and end times
    try:
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        start_t = time(start_h, start_m)
        end_t = time(end_h, end_m)
        if start_t >= end_t:
            logger.error("Invalid time range: start_time=%s, end_time=%s", start_time, end_time)
            return JsonResponse({
                'success': False,
                'message': 'End time must be after start time.'
            }, status=400)
    except (ValueError, IndexError):
        logger.error("Invalid time format: start_time=%s, end_time=%s", start_time, end_time)
        return JsonResponse({
            'success': False,
            'message': 'Invalid start or end time format.'
        }, status=400)

    # Check for overlapping slots (excluding the current slot)
    overlapping_slots = TimetableSlot.objects.filter(
        course_offering=slot.course_offering,
        venue=venue,
        day=day,
        start_time__lt=end_t,  # Existing slot starts before new slot ends
        end_time__gt=start_t   # Existing slot ends after new slot starts
    ).exclude(id=slot_id)

    if overlapping_slots.exists():
        conflicting_slots = overlapping_slots.values('day', 'start_time', 'end_time')
        conflict_details = ", ".join([
            f"{slot['day'].capitalize()} ({slot['start_time']}–{slot['end_time']})"
            for slot in conflicting_slots
        ])
        logger.error("Overlapping slots found: %s", conflict_details)
        return JsonResponse({
            'success': False,
            'message': f'Timetable slot already exists for {conflict_details}.'
        }, status=400)

    # Update the slot
    try:
        slot.day = day
        slot.start_time = start_t
        slot.end_time = end_t
        slot.venue = venue
        slot.save()
        logger.info("Timetable slot ID %s updated successfully", slot_id)
        return JsonResponse({
            'success': True,
            'message': 'Timetable slot updated successfully.'
        }, status=200)
    except Exception as e:
        logger.error("Error updating timetable slot ID %s: %s", slot_id, str(e))
        return JsonResponse({
            'success': False,
            'message': f'Error updating timetable slot: {str(e)}'
        }, status=500)

@hod_required
def delete_timetable_slot(request):
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method or insufficient permissions.'
        })

    slot_id = request.POST.get('slot_id')
    if not slot_id:
        return JsonResponse({
            'success': False,
            'message': 'Timetable slot ID is required.'
        })

    try:
        slot = get_object_or_404(TimetableSlot, id=slot_id, course_offering__department=request.user.teacher_profile.department)
        slot.delete()
        return JsonResponse({
            'success': True,
            'message': 'Timetable slot deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting timetable slot: {str(e)}'
        })



@hod_required
def weekly_timetable(request):
    department = request.user.teacher_profile.department
    academic_sessions = AcademicSession.objects.filter(is_active=True).order_by('-start_year')
    selected_session_id = request.GET.get('session_id')

    if selected_session_id:
        current_session = AcademicSession.objects.filter(id=selected_session_id, is_active=True).first()
    else:
        current_session = AcademicSession.objects.filter(is_active=True).order_by('-start_year').first()

    if not current_session:
        return render(request, 'faculty_staff/error.html', {
            'message': 'No active academic session found.'
        }, status=404)

    programs = Program.objects.filter(department=department).distinct()
    shift_filter = request.GET.get('shift', 'all').lower()
    valid_shifts = ['morning', 'evening', 'both', 'all']
    if shift_filter not in valid_shifts:
        shift_filter = 'all'

    queryset = TimetableSlot.objects.filter(
        course_offering__department=department,
        course_offering__academic_session=current_session,
        course_offering__semester__is_active=True
    ).select_related('course_offering__course', 'course_offering__teacher', 'course_offering__replacement_teacher', 'course_offering__program', 'venue')

    if shift_filter != 'all':
        if shift_filter == 'morning':
            queryset = queryset.filter(Q(course_offering__shift='morning') | 
                                     (Q(course_offering__shift='both') & Q(start_time__lt='12:00:00')))
        elif shift_filter == 'evening':
            queryset = queryset.filter(Q(course_offering__shift='evening') | 
                                     (Q(course_offering__shift='both') & Q(start_time__gte='12:00:00')))
        else:
            queryset = queryset.filter(course_offering__shift='both')

    timetable_data = []
    days_of_week = TimetableSlot.DAYS_OF_WEEK
    for day_value, day_label in days_of_week:
        day_slots = sorted(
            [
                {
                    'course_code': slot.course_offering.course.code,
                    'course_name': slot.course_offering.course.name,
                    'venue': slot.venue.name,
                    'room_no': slot.venue.capacity,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'shift': (
                        slot.course_offering.shift.capitalize() if slot.course_offering.shift != 'both'
                        else ('Morning' if slot.start_time.hour < 12 else 'Evening')
                    ),
                    'teacher': (
                        f"{slot.course_offering.replacement_teacher.user.get_full_name()}"
                        if slot.course_offering.replacement_teacher
                        else f"{slot.course_offering.teacher.user.get_full_name()}"
                    ),
                    'teacher_id': (
                        slot.course_offering.replacement_teacher.id
                        if slot.course_offering.replacement_teacher
                        else slot.course_offering.teacher.id
                    ),
                    'original_teacher_id': slot.course_offering.teacher.id,
                    'program': slot.course_offering.program.name if slot.course_offering.program else 'No Program',
                    'course_offering_id': slot.course_offering.id,
                }
                for slot in queryset.filter(day=day_value)
            ],
            key=lambda x: x['start_time']
        )
        timetable_data.append({
            'day_value': day_value,
            'day_label': day_label,
            'slots': day_slots
        })

    programs = TimetableSlot.objects.filter(
        course_offering__department=department,
        course_offering__academic_session=current_session,
        course_offering__semester__is_active=True
    ).values('course_offering__program__name').distinct()

    teachers = Teacher.objects.filter(department=department, is_active=True)

    return render(request, 'faculty_staff/weekly_timetable.html', {
        'timetable_data': timetable_data,
        'department': department,
        'academic_session': current_session,
        'shift_filter': shift_filter,
        'shift_options': [('all', 'All'), ('morning', 'Morning'), ('evening', 'Evening'), ('both', 'Both')],
        'academic_sessions': academic_sessions,
        'programs': programs,
        'teachers': teachers,
    })
    
    
    
@hod_required
def lecture_replacement_create(request):
    if request.method == 'POST':
        course_offering_id = request.POST.get('course_offering')
        original_teacher_id = request.POST.get('original_teacher')
        replacement_teacher_id = request.POST.get('replacement_teacher')
        replacement_type = request.POST.get('replacement_type')
        replacement_date = request.POST.get('replacement_date') or None

        try:
            course_offering = CourseOffering.objects.get(id=course_offering_id)
            original_teacher = Teacher.objects.get(id=original_teacher_id)
            replacement_teacher = Teacher.objects.get(id=replacement_teacher_id)

            # Create LectureReplacement instance
            replacement = LectureReplacement(
                course_offering=course_offering,
                original_teacher=original_teacher,
                replacement_teacher=replacement_teacher,
                replacement_type=replacement_type,
                replacement_date=replacement_date
            )
            replacement.full_clean()
            replacement.save()

            # Update CourseOffering.replacement_teacher and teacher
            if replacement_type == 'permanent':
                course_offering.replacement_teacher = replacement_teacher
                course_offering.teacher = replacement_teacher
                course_offering.save()
            elif replacement_type == 'temporary' and replacement_date:
                if date.today() >= date.fromisoformat(replacement_date):
                    course_offering.replacement_teacher = replacement_teacher
                    course_offering.teacher = replacement_teacher
                    course_offering.save()
                else:
                    course_offering.replacement_teacher = None  # Clear if not yet active
                    course_offering.teacher = None
                    course_offering.save()

            # Send email notification to the replacement teacher
            try:
                # Prepare email content
                subject = f'Lecture Replacement: {course_offering.course.code} - {replacement_type.capitalize()} Replacement'
                
                # Get replacement type display name
                replacement_type_display = 'Permanent' if replacement_type == 'permanent' else 'Temporary'
                
                # Format replacement date if exists
                formatted_replacement_date = None
                if replacement_date:
                    from django.utils.formats import date_format
                    from django.utils import timezone
                    formatted_replacement_date = timezone.make_naive(replacement.replacement_date)
                
                # Render the email template
                message = render_to_string('emails/lecture_replacement_notification.html', {
                    'course_offering': course_offering,
                    'original_teacher': original_teacher,
                    'replacement_teacher': replacement_teacher,
                    'replacement_type': replacement_type,
                    'replacement_type_display': replacement_type_display,
                    'replacement_date': formatted_replacement_date,
                    'site_name': 'Campus360'
                })
                
                # Send email to the replacement teacher
                if hasattr(replacement_teacher, 'user') and hasattr(replacement_teacher.user, 'email') and replacement_teacher.user.email:
                    send_mail(
                        subject=subject,
                        message='',  # Empty message since we're using html_message
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[replacement_teacher.user.email],
                        html_message=message,
                        fail_silently=True
                    )
                    logger.info(f"Sent lecture replacement notification to {replacement_teacher.user.email}")
                else:
                    logger.warning(f"Replacement teacher {replacement_teacher} has no valid email address")
            
            except Exception as e:
                logger.error(f"Error sending lecture replacement notification email: {str(e)}")
                # Don't fail the request if email sending fails
                pass

            messages.success(request, 'Lecture replacement created successfully.')
            return redirect('faculty_staff:weekly_timetable')
        except CourseOffering.DoesNotExist:
            messages.error(request, 'Invalid course offering selected.')
        except Teacher.DoesNotExist:
            messages.error(request, 'Invalid teacher selected.')
        except ValidationError as e:
            error_message = 'Error creating replacement: '
            if hasattr(e, 'message_dict') and '__all__' in e.message_dict:
                error_message += e.message_dict['__all__'][0]
            else:
                error_message += str(e)
            messages.error(request, error_message)
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')

    return redirect('faculty_staff:weekly_timetable')


@hod_or_professor_required
def my_timetable(request):
    teacher = request.user.teacher_profile   
    # department = teacher.department  # Removed department restriction
    # Get all active sessions (relaxed filter to include sessions with inactive semesters)
    academic_sessions = AcademicSession.objects.filter(is_active=True).distinct().order_by('-start_year')
    logger.debug(f"All active academic sessions: {academic_sessions}")
    selected_session_id = request.GET.get('session_id')

    # Determine the current session
    if selected_session_id:
        current_session = AcademicSession.objects.filter(
            id=selected_session_id,
            is_active=True
        ).first()  # Allow selection of any active session, even with inactive semesters
    else:
        current_session = AcademicSession.objects.filter(is_active=True).order_by('-start_year').first()
    
    if not current_session:
        return render(request, 'faculty_staff/error.html', {
            'message': 'No active academic session found.'
        }, status=404)
    logger.debug(f"Selected current session: {current_session}, Semesters: {current_session.semesters.all()}")

    # Debug: Log active and inactive semesters per program for the selected session
    programs = Program.objects.all().distinct()  # Changed to include all programs, not just department-specific
    for program in programs:
        semesters = Semester.objects.filter(program=program, session=current_session)
        active_semesters = semesters.filter(is_active=True).count()
        inactive_semesters = semesters.count() - active_semesters
        logger.debug(f"Program: {program.name}, Active Semesters: {active_semesters}, Inactive Semesters: {inactive_semesters}")
        for semester in semesters:
            logger.debug(f"  Semester: {semester.name}, Is Active: {semester.is_active}")

    # Get shift filter and include_inactive flag from GET parameters
    shift_filter = request.GET.get('shift', 'all').lower()
    include_inactive = request.GET.get('include_inactive', '0') == '1'  # True if ?include_inactive=1
    valid_shifts = ['morning', 'evening', 'both', 'all']
    if shift_filter not in valid_shifts:
        shift_filter = 'all'

    # Fetch timetable slots for the teacher's courses across all departments
    queryset = TimetableSlot.objects.filter(
        course_offering__teacher=teacher,
        course_offering__academic_session=current_session
    ).select_related('course_offering__course', 'course_offering__program', 'venue')

    # Filter by semester activity unless include_inactive is True
    if not include_inactive:
        queryset = queryset.filter(course_offering__semester__is_active=True)
        logger.debug(f"Filtering for active semesters only: {queryset}")
    else:
        logger.debug("Including slots from inactive semesters")
    logger.debug(f"Raw queryset for slots: {queryset.query}")
    logger.debug(f"Retrieved slots count: {queryset.count()}, Slots: {list(queryset)}")

    # Apply shift filter
    if shift_filter != 'all':
        if shift_filter == 'morning':
            queryset = queryset.filter(Q(course_offering__shift='morning') | 
                                      (Q(course_offering__shift='both') & Q(start_time__lt='12:00:00')))
        elif shift_filter == 'evening':
            queryset = queryset.filter(Q(course_offering__shift='evening') | 
                                      (Q(course_offering__shift='both') & Q(start_time__gte='12:00:00')))
        else:  # both
            queryset = queryset.filter(course_offering__shift='both')
    logger.debug(f"Filtered queryset by shift ({shift_filter}): {list(queryset)}")

    # Organize slots by day
    timetable_data = []
    days_of_week = TimetableSlot.DAYS_OF_WEEK  # [('monday', 'Monday'), ...]
    for day_value, day_label in days_of_week:
        day_slots = sorted(
            [
                {
                    'teacher': slot.course_offering.teacher.user.get_full_name(),
                    'course_code': slot.course_offering.course.code,
                    'course_name': slot.course_offering.course.name,
                    'venue': slot.venue.name,
                    'room_no': slot.venue.capacity,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'shift': (
                        slot.course_offering.shift.capitalize() if slot.course_offering.shift != 'both'
                        else ('Morning' if slot.start_time.hour < 12 else 'Evening')
                    ),
                    'program': slot.course_offering.program.name,
                }
                for slot in queryset.filter(day=day_value)
            ],
            key=lambda x: x['start_time']
        )
        timetable_data.append({
            'day_value': day_value,
            'day_label': day_label,
            'slots': day_slots
        })
    logger.debug(f"Final timetable data: {timetable_data}")

    # Debug: Check offerings and their semester status
    offerings = CourseOffering.objects.filter(
        academic_session=current_session,
        teacher=teacher
    )
    active_offerings = offerings.filter(semester__is_active=True)
    inactive_offerings = offerings.exclude(semester__is_active=True)
    logger.debug(f"Total Offerings: {offerings.count()}")
    logger.debug(f"Active Offerings: {active_offerings.count()}")
    logger.debug(f"Inactive Offerings: {inactive_offerings.count()}")
    for offering in offerings:
        logger.debug(f"Offering: {offering.course.code} - {offering.course.name}, Semester: {offering.semester}, Is Active: {offering.semester.is_active if offering.semester else 'None'}")

    return render(request, 'faculty_staff/my_timetable.html', {
        'timetable_data': timetable_data,
        # 'department': department,  # Removed since not used
        'academic_session': current_session,
        'shift_filter': shift_filter,
        'shift_options': [('all', 'All'), ('morning', 'Morning'), ('evening', 'Evening'), ('both', 'Both')],
        'teacher': teacher,
        'academic_sessions': academic_sessions,
        'include_inactive': include_inactive,  # Pass to template for UI feedback
    })
    
        

@hod_required
def search_course_offerings(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'})
    
    search_query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    per_page = 10
    hod_department = request.user.teacher_profile.department

    course_offerings = CourseOffering.objects.filter(
        department=hod_department
    ).select_related('course', 'program', 'semester', 'academic_session')

    if search_query:
        course_offerings = course_offerings.filter(
            Q(course__code__icontains=search_query) | 
            Q(course__name__icontains=search_query) |
            Q(program__name__icontains=search_query)
        )

    start = (page - 1) * per_page
    end = start + per_page
    paginated_offerings = course_offerings[start:end]

    return JsonResponse({
        'success': True,
        'results': [
            {
                'id': offering.id,
                'course_code': offering.course.code,
                'course_name': offering.course.name,
                'program_name': offering.program.name,
                'semester_name': offering.semester.name,
                'session_name': offering.academic_session.name
            } for offering in paginated_offerings
        ],
        'pagination': {'more': end < course_offerings.count()}
    })


@hod_required
def delete_course_offering(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        offering_id = request.POST.get('offering_id')
        if offering_id:
            offering = get_object_or_404(CourseOffering, id=offering_id)
            offering.delete()
            return JsonResponse({'success': True, 'message': 'Course offering deleted successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@hod_or_professor_required
def study_materials(request, offering_id):
    course_offering_id = offering_id
    course_shift = None
    materials = []

    if course_offering_id:
        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        course_shift = course_offering.shift
        materials = StudyMaterial.objects.filter(course_offering=course_offering).select_related('teacher')
        materials = [{
            'id': m.id,
            'topic': m.topic,
            'title': m.title,
            'description': m.description,
            'useful_links': m.useful_links.split('\n') if m.useful_links else [],
            'video_link': m.video_link,
            'image': m.image.url if m.image else None,
            'created_at': m.created_at.strftime('%b %d, %Y %I:%M %p'),
            'teacher': m.teacher.user.get_full_name() if m.teacher else 'Unknown'
        } for m in materials]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'materials': materials,
            'course_shift': course_shift
        })

    context = {
        'course_offering_id': course_offering_id,
        'course_shift': course_shift,
        'materials': materials,
        'today_date': timezone.now().date(),
    }
    return render(request, 'faculty_staff/study_materials.html', context)

@hod_or_professor_required
def create_study_material(request):
    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        topic = request.POST.get('topic')
        
        if not all([course_offering_id, topic]):
            return JsonResponse({'success': False, 'message': 'Course offering and topic are required.'})

        try:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
            teacher = get_object_or_404(Teacher, user=request.user)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error fetching course or teacher: {str(e)}'})

        materials_data = []
        
        with transaction.atomic():
            for key in request.POST:
                if key.startswith('materials['):
                    index = key.split('[')[1].split(']')[0]
                    field = key.split('[')[2].split(']')[0]
                    if not any(m.get('index') == index for m in materials_data):
                        materials_data.append({'index': index})
                    for material in materials_data:
                        if material['index'] == index:
                            material[field] = request.POST[key]
            
            for index in request.FILES:
                if index.startswith('materials['):
                    material_index = index.split('[')[1].split(']')[0]
                    field = index.split('[')[2].split(']')[0]
                    for material in materials_data:
                        if material['index'] == material_index:
                            material[field] = request.FILES[index]
            
            created_materials = []
            for material_data in materials_data:
                if not all([material_data.get('title'), material_data.get('description')]):
                    continue
                
                study_material = StudyMaterial(
                    course_offering=course_offering,
                    teacher=teacher,
                    topic=topic,
                    title=material_data.get('title'),
                    description=material_data.get('description'),
                    useful_links=material_data.get('useful_links', '').strip(),
                    video_link=material_data.get('video_link') or None
                )
                
                if 'image' in material_data:
                    study_material.image = material_data['image']
                
                study_material.save()
                created_materials.append({
                    'id': study_material.id,
                    'topic': study_material.topic,
                    'title': study_material.title,
                    'description': study_material.description,
                    'useful_links': study_material.useful_links.split('\n') if study_material.useful_links else [],
                    'video_link': study_material.video_link,
                    'image': study_material.image.url if study_material.image else None,
                    'created_at': study_material.created_at.strftime('%b %d, %Y %I:%M %p'),
                    'teacher': study_material.teacher.user.get_full_name() if study_material.teacher else 'Unknown'
                })
            
            if not created_materials:
                return JsonResponse({'success': False, 'message': 'At least one valid material is required.'})
            
            # Send email notifications to CR and GR for the first material only (to avoid multiple emails)
            if created_materials:
                try:
                    # Get all students enrolled in the course offering
                    from students.models import Student
                    enrolled_students = Student.objects.filter(
                        courses_enrolled__course_offering=course_offering,
                        courses_enrolled__status='enrolled'
                    ).distinct()
                    
                    # Find class representatives (CR) and girls' representatives (GR)
                    crs = enrolled_students.filter(role='CR')
                    grs = enrolled_students.filter(role='GR')
                    
                    # Combine and deduplicate recipients
                    recipients = list(crs) + list(grs)
                    
                    if recipients:
                        # Prepare email content
                        subject = f'New Study Material: {topic} - {course_offering.course.code}'
                        
                        # Get the course name and teacher name
                        teacher_name = request.user.get_full_name() or 'Your teacher'
                        
                        # Get the first material for the notification
                        first_material = created_materials[0]
                        
                        # Prepare useful_links as a list
                        useful_links = []
                        if first_material.get('useful_links'):
                            if isinstance(first_material['useful_links'], str):
                                useful_links = [link.strip() for link in first_material['useful_links'].split('\n') if link.strip()]
                            else:
                                useful_links = [link for link in first_material['useful_links'] if link.strip()]
                        
                        # Render the email template
                        message = render_to_string('emails/new_study_material_notification.html', {
                            'material': {
                                'topic': topic,
                                'title': first_material.get('title', ''),
                                'description': first_material.get('description', ''),
                                'useful_links': useful_links,
                                'video_link': first_material.get('video_link'),
                                'image': first_material.get('image')
                            },
                            'course_offering': course_offering,
                            'teacher_name': teacher_name,
                            'site_name': 'Campus360'
                        })
                        
                        # Send email to each recipient
                        for recipient in recipients:
                            if getattr(recipient, 'user', None) and recipient.user.email:
                                send_mail(
                                    subject=subject,
                                    message='',  # Empty message since we're using html_message
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[recipient.user.email],
                                    html_message=message,
                                    fail_silently=True
                                )
                                logger.info(f"Sent study material notification email to {recipient.user.email}")
                
                except Exception as e:
                    logger.error(f"Error sending study material notification emails: {str(e)}")
                    # Don't fail the request if email sending fails
                    pass
            
            return JsonResponse({
                'success': True,
                'message': 'Study materials created successfully.',
                'materials': created_materials
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@hod_or_professor_required
def edit_study_material(request):
    if request.method == "GET":
        material_id = request.GET.get('material_id')
        if not material_id:
            return JsonResponse({'success': False, 'message': 'Material ID is required.'})
        
        material = get_object_or_404(StudyMaterial, id=material_id)
        return JsonResponse({
            'success': True,
            'material': {
                'id': material.id,
                'course_offering_id': material.course_offering.id,
                'topic': material.topic,
                'title': material.title,
                'description': material.description,
                'useful_links': material.useful_links.split('\n') if material.useful_links else [],
                'video_link': material.video_link,
                'image': material.image.url if material.image else None
            }
        })
    
    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        topic = request.POST.get('topic')
        
        if not all([course_offering_id, topic]):
            return JsonResponse({'success': False, 'message': 'Course offering and topic are required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        teacher = get_object_or_404(Teacher, user=request.user)
        materials_data = []
        
        with transaction.atomic():
            for key in request.POST:
                if key.startswith('materials['):
                    index = key.split('[')[1].split(']')[0]
                    field = key.split('[')[2].split(']')[0]
                    if not any(m.get('index') == index for m in materials_data):
                        materials_data.append({'index': index})
                    for material in materials_data:
                        if material['index'] == index:
                            material[field] = request.POST[key]
            
            for index in request.FILES:
                if index.startswith('materials['):
                    material_index = index.split('[')[1].split(']')[0]
                    field = index.split('[')[2].split(']')[0]
                    for material in materials_data:
                        if material['index'] == material_index:
                            material[field] = request.FILES[index]
            
            updated_materials = []
            for material_data in materials_data:
                if not all([material_data.get('title'), material_data.get('description')]):
                    continue
                
                material_id = material_data.get('id')
                if material_id:
                    material = get_object_or_404(StudyMaterial, id=material_id)
                else:
                    material = StudyMaterial(
                        course_offering=course_offering,
                        teacher=teacher
                    )
                
                material.topic = topic
                material.title = material_data.get('title')
                material.description = material_data.get('description')
                material.useful_links = material_data.get('useful_links', '')
                material.video_link = material_data.get('video_link') or None
                
                if 'image' in material_data:
                    if material.image:
                        default_storage.delete(material.image.path)
                    material.image = material_data['image']
                
                material.save()
                updated_materials.append({
                    'id': material.id,
                    'topic': material.topic,
                    'title': material.title,
                    'description': material.description,
                    'useful_links': material.useful_links.split('\n') if material.useful_links else [],
                    'video_link': material.video_link,
                    'image': material.image.url if material.image else None,
                    'created_at': material.created_at.strftime('%b %d, %Y %I:%M %p'),
                    'teacher': material.teacher.user.get_full_name() if material.teacher else 'Unknown'
                })
            
            if not updated_materials:
                return JsonResponse({'success': False, 'message': 'At least one valid material is required.'})
            
            return JsonResponse({
                'success': True,
                'message': 'Study materials updated successfully.',
                'materials': updated_materials
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@hod_or_professor_required
def delete_study_material(request):
    if request.method == "POST":
        material_id = request.POST.get('material_id')
        if not material_id:
            return JsonResponse({'success': False, 'message': 'Material ID is required.'})
        
        try:
            material = get_object_or_404(StudyMaterial, id=material_id)
            teacher = get_object_or_404(Teacher, user=request.user)  
            
            if material.teacher != teacher:
                return JsonResponse({'success': False, 'message': 'You can only delete your own materials.'})
            
            if material.image:
                default_storage.delete(material.image.path)
            material.delete()
            return JsonResponse({'success': True, 'message': 'Study material deleted successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error deleting material: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def search_course_offerings(request):
    query = request.GET.get('q', '')
    course_offering_id = request.GET.get('id')
    page = int(request.GET.get('page', 1))
    results = []
     
    if course_offering_id:
        try:
            offering = CourseOffering.objects.get(id=course_offering_id, teacher__user=request.user)
            results.append({
                'id': offering.id,
                'course_code': offering.course.code,
                'course_name': offering.course.name,
                'program_name': offering.program.name,
                'semester_name': offering.semester.name,
                'session_name': offering.academic_session.name
            })
        except CourseOffering.DoesNotExist:
            pass
    else:
        offerings = CourseOffering.objects.filter(
            teacher__user=request.user,
            course__code__icontains=query
        ).select_related('course', 'program', 'semester', 'academic_session')[:10]
        results = [{
            'id': o.id,
            'course_code': o.course.code,
            'course_name': o.course.name,
            'program_name': o.program.name,
            'semester_name': o.semester.name,
            'session_name': o.academic_session.name
        } for o in offerings]
    
    return JsonResponse({
        'success': True,
        'results': results,
        'pagination': {'more': False}
    })


@hod_or_professor_required
def assignments(request, offering_id):    
    course_offering_id = offering_id
    if course_offering_id:
        try:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
            assignments = Assignment.objects.filter(
                course_offering_id=course_offering_id,
                course_offering__teacher=request.user.teacher_profile
            ).select_related('course_offering').order_by('-created_at')
            logger.info(f"Retrieved assignments for course offering {course_offering_id}: {list(assignments)}")
        except ValueError:
            logger.error(f"Invalid course offering ID: {course_offering_id}")
            return render(request, 'faculty_staff/assignments.html', {
                'assignments': [],
                'course_offering': None,
                'course_offering_id': None,
                'error': 'Invalid course offering ID.'
            })
    else:
        assignments = Assignment.objects.filter(
            course_offering__teacher=request.user.teacher_profile
        ).select_related('course_offering').order_by('-created_at')
        course_offering = None
        logger.info(f"Retrieved all assignments for teacher {request.user.teacher_profile}: {list(assignments)}")
    
    return render(request, 'faculty_staff/assignments.html', {
        'assignments': assignments,
        'course_offering': course_offering,
        'course_offering_id': course_offering_id
    })

@hod_or_professor_required
def create_assignment(request):
    if request.method != 'POST':
        logger.error(f"Invalid request method for create_assignment: {request.method}")
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    course_offering_id = request.POST.get('course_offering_id')
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    due_date = request.POST.get('due_date')
    max_points = request.POST.get('max_points')
    resource_file = request.FILES.get('resource_file')

    # Validate inputs
    if not course_offering_id:
        logger.error("Missing course offering ID")
        return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})
    
    try:
        course_offering_id = int(course_offering_id)
    except ValueError:
        logger.error(f"Invalid course offering ID: {course_offering_id}")
        return JsonResponse({'success': False, 'message': 'Invalid course offering ID.'})

    try:
        max_points = int(max_points)
        if max_points < 1:
            logger.error(f"Invalid max points: {max_points}")
            return JsonResponse({'success': False, 'message': 'Max points must be at least 1.'})
    except ValueError:
        logger.error(f"Invalid max points value: {max_points}")
        return JsonResponse({'success': False, 'message': 'Invalid max points value.'})

    if not title:
        logger.error("Missing title")
        return JsonResponse({'success': False, 'message': 'Title is required.'})
    if not due_date:
        logger.error("Missing due date")
        return JsonResponse({'success': False, 'message': 'Due date is required.'})

    course_offering = get_object_or_404(
        CourseOffering,
        id=course_offering_id,
        teacher=request.user.teacher_profile
    )
    assignment = Assignment.objects.create(
        course_offering=course_offering,
        teacher=request.user.teacher_profile,
        title=title,
        description=description,
        due_date=due_date,
        max_points=max_points,
        resource_file=resource_file  
    )
    logger.info(f"Assignment '{title}' created for course offering {course_offering_id} by {request.user}")
    
    # Send email notifications to CR and GR
    try:
        # Get all students enrolled in the course offering
        from students.models import Student
        enrolled_students = Student.objects.filter(
            courses_enrolled__course_offering=course_offering,
            courses_enrolled__status='enrolled'
        ).distinct()
        
        # Find class representatives (CR) and girls' representatives (GR)
        crs = enrolled_students.filter(role='CR')
        grs = enrolled_students.filter(role='GR')
        
        # Combine and deduplicate recipients
        recipients = list(crs) + list(grs)
        
        if recipients:
            # Prepare email content
            subject = f'New Assignment: {assignment.title} - {course_offering.course.code}'
            
            # Get the course name and teacher name
            course_name = course_offering.course.name
            teacher_name = request.user.get_full_name() or 'Your teacher'
            
            # Format the due date
            from django.utils import timezone
            from django.utils.formats import date_format
            due_date_formatted = date_format(timezone.make_naive(assignment.due_date)) if assignment.due_date else 'Not specified'
            
            # Render the email template
            message = render_to_string('emails/new_assignment_notification.html', {
                'assignment': assignment,
                'course_offering': course_offering,
                'teacher_name': teacher_name,
                'due_date': due_date_formatted,
                'max_points': assignment.max_points,
                'has_attachment': bool(assignment.resource_file)
            })
            
            # Send email to each recipient
            for recipient in recipients:
                if getattr(recipient, 'user', None) and recipient.user.email:
                    send_mail(
                        subject=subject,
                        message='',  # Empty message since we're using html_message
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient.user.email],
                        html_message=message,
                        fail_silently=True
                    )
                    logger.info(f"Sent assignment notification email to {recipient.user.email}")
    
    except Exception as e:
        logger.error(f"Error sending assignment notification emails: {str(e)}")
        # Don't fail the request if email sending fails
        pass
    
    return JsonResponse({'success': True, 'message': 'Assignment created successfully.'})

@hod_or_professor_required
def edit_assignment(request):
    if request.method != 'POST':
        logger.error(f"Invalid request method for edit_assignment: {request.method}")
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    assignment_id = request.POST.get('assignment_id')
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    due_date = request.POST.get('due_date')
    max_points = request.POST.get('max_points')
    resource_file = request.FILES.get('resource_file')

    # Validate inputs
    if not assignment_id:
        logger.error("Missing assignment ID")
        return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})

    try:
        assignment_id = int(assignment_id)
    except ValueError:
        logger.error(f"Invalid assignment ID: {assignment_id}")
        return JsonResponse({'success': False, 'message': 'Invalid assignment ID.'})

    try:
        max_points = int(max_points)
        if max_points < 1:
            logger.error(f"Invalid max points: {max_points}")
            return JsonResponse({'success': False, 'message': 'Max points must be at least 1.'})
    except ValueError:
        logger.error(f"Invalid max points value: {max_points}")
        return JsonResponse({'success': False, 'message': 'Invalid max points value.'})

    if not title:
        logger.error("Missing title")
        return JsonResponse({'success': False, 'message': 'Title is required.'})
    if not due_date:
        logger.error("Missing due date")
        return JsonResponse({'success': False, 'message': 'Due date is required.'})

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        course_offering__teacher=request.user.teacher_profile
    )

    # Update assignment fields
    assignment.title = title
    assignment.description = description
    assignment.due_date = due_date
    assignment.max_points = max_points
    if resource_file:
        # Delete old file if it exists
        if assignment.resource_file and os.path.isfile(assignment.resource_file.path):
            os.remove(assignment.resource_file.path)
        assignment.resource_file = resource_file
    assignment.save()
    logger.info(f"Assignment '{title}' (ID: {assignment_id}) updated by {request.user}")
    return JsonResponse({'success': True, 'message': 'Assignment updated successfully.'})

@hod_or_professor_required
def delete_assignment(request):
    assignment_id = request.POST.get('assignment_id')
    if assignment_id:
        assignment = get_object_or_404(
            Assignment,
            id=assignment_id,
            course_offering__teacher=request.user.teacher_profile
        )
        if assignment.resource_file and os.path.isfile(assignment.resource_file.path):
            os.remove(assignment.resource_file.path)
        assignment.delete()
        logger.info(f"Assignment ID {assignment_id} deleted by {request.user}")
        return JsonResponse({'success': True, 'message': 'Assignment deleted successfully.'})
    logger.error("Missing assignment ID for deletion")
    return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})

@hod_or_professor_required
def assignment_submissions(request, assignment_id):
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        course_offering__teacher=request.user.teacher_profile
    )
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('-submitted_at')
    logger.info(f"Retrieved submissions for assignment ID {assignment_id}: {list(submissions)}")
    return render(request, 'faculty_staff/assignment_submissions.html', {'assignment': assignment, 'submissions': submissions})

@hod_or_professor_required
def grade_submission(request):
    submission_id = request.POST.get('submission_id')
    marks_obtained = request.POST.get('marks_obtained')
    feedback = request.POST.get('feedback')

    if not submission_id or marks_obtained is None:
        logger.error(f"Missing submission ID or marks: submission_id={submission_id}, marks_obtained={marks_obtained}")
        return JsonResponse({'success': False, 'message': 'Submission ID and marks are required.'})

    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment__course_offering__teacher=request.user.teacher_profile
    )
    try:
        submission.marks_obtained = int(marks_obtained)
    except ValueError:
        logger.error(f"Invalid marks_obtained value: {marks_obtained}")
        return JsonResponse({'success': False, 'message': 'Invalid marks value.'})
    submission.feedback = feedback
    submission.graded_by = request.user.teacher_profile
    submission.graded_at = timezone.now()
    submission.save()
    logger.info(f"Submission ID {submission_id} graded by {request.user}")
    return JsonResponse({'success': True, 'message': 'Submission graded successfully.'})




@login_required
def notice_board(request):
    if request.user.teacher_profile and request.user.teacher_profile.designation == 'head_of_department':
        # HoD view: Manage all notices
        notices = Notice.objects.all().order_by('-created_at')
    elif request.user.teacher_profile:
        # Teacher view: View only notices relevant to their department's programs
        department = request.user.teacher_profile.department
        notices = Notice.objects.filter(
            Q(programs__department=department) | Q(sessions__semesters__program__department=department)
        ).distinct().order_by('-created_at')
    else:
        # Student view: Filter by enrolled program and session
        student = getattr(request.user, 'student_profile', None)
        if student:
            current_semester = StudentSemesterEnrollment.objects.filter(student=student).first()
            if current_semester:
                current_program = current_semester.student.program
                current_session = current_semester.semester.session
                notices = Notice.objects.filter(
                    Q(programs__in=[current_program]) | Q(programs__isnull=True),
                    Q(sessions__in=[current_session]) | Q(sessions__isnull=True),
                    Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True),
                    is_active=True,
                    valid_from__lte=timezone.now(),
                ).distinct().order_by('-created_at')
        else:
            notices = Notice.objects.none()

    if request.method == 'POST':
        if 'create_notice' in request.POST:
            if not request.user.teacher_profile:
                messages.error(request, "Only teachers can create notices.")
                return redirect('notice_board')

            title = request.POST.get('title')
            content = request.POST.get('content')
            notice_type = request.POST.get('notice_type', 'general')
            program_ids = request.POST.getlist('programs')
            session_ids = request.POST.getlist('sessions')
            valid_from = request.POST.get('valid_from') or timezone.now()
            valid_until = request.POST.get('valid_until')
            attachment = request.FILES.get('attachment')

            # First create the notice without the many-to-many relationships
            notice = Notice.objects.create(
                title=title,
                content=content,
                notice_type=notice_type,
                priority=priority,
                valid_from=valid_from,
                valid_until=valid_until if valid_until else None,
                attachment=attachment,
                created_by=request.user.teacher_profile
            )
            # Now that the notice has an ID, we can set the many-to-many relationships
            if program_ids:
                notice.programs.set(program_ids)
            if session_ids:
                notice.sessions.set(session_ids)
            messages.success(request, "Notice created successfully.")
        elif 'toggle_active' in request.POST:
            notice_id = request.POST.get('notice_id')
            notice = get_object_or_404(Notice, id=notice_id)
            if request.user.teacher_profile:
                notice.is_active = not notice.is_active
                notice.save()
                messages.success(request, f"Notice '{notice.title}' {'activated' if notice.is_active else 'deactivated'} successfully.")
        elif 'edit_notice' in request.POST:
            notice_id = request.POST.get('notice_id')
            notice = get_object_or_404(Notice, id=notice_id)
            if request.user.teacher_profile and (request.user.teacher_profile.designation == 'head_of_department' or 
                                              notice.created_by == request.user.teacher_profile):
                notice.title = request.POST.get('title')
                notice.content = request.POST.get('content')
                notice.notice_type = request.POST.get('notice_type')
                notice.priority = request.POST.get('priority')
                notice.programs.set(request.POST.getlist('programs'))
                notice.sessions.set(request.POST.getlist('sessions'))
                notice.valid_from = request.POST.get('valid_from') or timezone.now()
                notice.valid_until = request.POST.get('valid_until')
                if request.FILES.get('attachment'):
                    notice.attachment = request.FILES.get('attachment')
                notice.is_pinned = request.POST.get('is_pinned') == 'on'
                notice.save()
                messages.success(request, "Notice updated successfully.")
        elif 'delete_notice' in request.POST:
            notice_id = request.POST.get('notice_id')
            notice = get_object_or_404(Notice, id=notice_id)
            if request.user.teacher_profile and (request.user.teacher_profile.designation == 'head_of_department' or 
                                              notice.created_by == request.user.teacher_profile):
                notice.delete()
                messages.success(request, "Notice deleted successfully.")

    # Pagination
    paginator = Paginator(notices, 10)  # 10 notices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get programs based on user type
    if request.user.teacher_profile:
        if request.user.teacher_profile.designation == 'head_of_department':
            # HoD can see all programs in their department
            programs = Program.objects.filter(department=request.user.teacher_profile.department)
        else:
            # Regular teachers can see programs they're associated with
            programs = Program.objects.filter(
                Q(department=request.user.teacher_profile.department) |
                Q(courses__assigned_teachers=request.user.teacher_profile)
            ).distinct()
    else:
        # For students, show only their enrolled program
        student = getattr(request.user, 'student_profile', None)
        if student and hasattr(student, 'program'):
            programs = Program.objects.filter(id=student.program.id)
        else:
            programs = Program.objects.none()

    sessions = AcademicSession.objects.filter(is_active=True) 

    return render(request, 'faculty_staff/notice_board.html', {
        'notices': page_obj,
        'programs': programs,
        'sessions': sessions,
        'notice_types': dict(Notice.NOTICE_TYPES),
        'priorities': dict(Notice.PRIORITY_LEVELS)
    })


@login_required
def search_students(request):  
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        students = Student.objects.filter(
            Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query)
        ).values('id', 'user__first_name', 'user__last_name')[:10]
        return JsonResponse({
            'results': [{'id': student['id'], 'text': f"{student['user__first_name']} {student['user__last_name']}"} for student in students],
            'more': False
        })
    return JsonResponse({'results': [], 'more': False})






@hod_or_professor_required
def exam_results(request, course_offering_id):
    course_offerings = CourseOffering.objects.filter(
        teacher=request.user.teacher_profile
    ).select_related('course', 'semester', 'academic_session').order_by('-academic_session__start_year', 'semester__number')
    
    # Check if we're in edit mode
    edit_mode = request.GET.get('edit') == '1'
    
    context = {
        'course_offerings': course_offerings,
        'course_offering_id': course_offering_id,
        'edit_mode': edit_mode,
    }
    
    if course_offering_id:
        try:
            course_offering = get_object_or_404(
                CourseOffering,
                id=course_offering_id,
                teacher=request.user.teacher_profile
            )
            print(f'[DEBUG] Offering shift: {course_offering.shift}')
            print(f'[DEBUG] Course: {course_offering.course.code} - {course_offering.course.name}')
            print(f'[DEBUG] Semester: {course_offering.semester.name}')
            midterm_max = course_offering.course.credits * 4
            sessional_max = course_offering.course.credits * 2
            final_max = course_offering.course.credits * 14
            practical_max = course_offering.course.lab_work * 20
            total_max = midterm_max + sessional_max + final_max + (practical_max if course_offering.course.lab_work > 0 else 0)
            
            exam_results = ExamResult.objects.filter(
                course_offering_id=course_offering_id
            ).select_related('student__applicant')
            
            existing_results = {
                result.student_id: {
                    'midterm': result.midterm_obtained,
                    'sessional': result.sessional_obtained,
                    'final': result.final_obtained,
                    'practical': result.practical_obtained,
                    'total_marks': result.total_marks,
                    'percentage': result.percentage,
                    'remarks': result.remarks,
                    'id': result.id
                }
                for result in exam_results
            }
            
            # Include both enrolled and completed enrollments for viewing/editing
            enrollments = CourseEnrollment.objects.filter(
                course_offering=course_offering,
                status__in=['enrolled', 'completed']
            ).select_related(
                'student_semester_enrollment__student__applicant',
                'student_semester_enrollment__semester'
            ).order_by(
                'student_semester_enrollment__student__university_roll_no'
            )
            
            students = []
            print(f'[DEBUG] Total enrollments found: {enrollments.count()}')
            student_count = 0
            for enrollment in enrollments:
                student = enrollment.student_semester_enrollment.student
                applicant = student.applicant
                student_shift = getattr(applicant, 'shift', 'N/A')
                
                # Debug print for each enrollment
                print(f'[DEBUG] Processing enrollment - Student: {student}, Shift: {student_shift}, Semester: {enrollment.student_semester_enrollment.semester}')
                
                # Filter by matching shift
                semester_match = enrollment.student_semester_enrollment.semester == course_offering.semester
                shift_match = course_offering.shift == 'both' or str(student_shift).lower() == str(course_offering.shift).lower()
                
                print(f'[DEBUG] Semester match: {semester_match}, Shift match: {shift_match}')
                
                if semester_match and shift_match:
                    student_id = applicant.id
                    student_data = {
                        'id': student_id,
                        'name': str(student),
                        'university_roll_no': student.university_roll_no or 'N/A',
                        'college_roll_no': student.college_roll_no or 'N/A',
                        'midterm': None,
                        'sessional': None,
                        'final': None,
                        'practical': None,
                        'total_marks': None,
                        'percentage': None,
                        'remarks': '',
                        'result_id': None
                    }
                    
                    if student_id in existing_results:
                        result = existing_results[student_id]
                        student_data.update({
                            'midterm': result['midterm'],
                            'sessional': result['sessional'],
                            'final': result['final'],
                            'practical': result['practical'],
                            'total_marks': result['total_marks'],
                            'percentage': result['percentage'],
                            'remarks': result['remarks'] or '',
                            'result_id': result['id']
                        })
                    
                    students.append(student_data)
                    student_count += 1
            
            print(f'[DEBUG] Total students after filtering: {student_count}')
            
            aggregated_results = [
                {
                    'student': {
                        'applicant': {
                            'full_name': s['name'],
                            'id': s['id']
                        },
                        'university_roll_no': s['university_roll_no'],
                        'college_roll_no': s['college_roll_no']
                    },
                    'course_offering': {
                        'id': course_offering.id,
                        'course': {
                            'code': course_offering.course.code,
                            'title': course_offering.course.name,
                            'credits': course_offering.course.credits,
                            'lab_work': course_offering.course.lab_work
                        }
                    },
                    'midterm_obtained': s['midterm'],
                    'sessional_obtained': s['sessional'],
                    'final_obtained': s['final'],
                    'practical_obtained': s['practical'],
                    'total_marks': s['total_marks'],
                    'percentage': s['percentage'],
                    'midterm_total': midterm_max,
                    'sessional_total': sessional_max,
                    'final_total': final_max,
                    'practical_total': practical_max,
                    'academic_session': f"{course_offering.academic_session.name}",
                    'remarks': s['remarks'] or 'No Remarks',
                    'id': s['result_id']
                }
                for s in students
                if s['result_id']  # Only include students with existing results
            ]
            
            # Always show students, but filter results based on edit mode
            show_form = not aggregated_results or edit_mode
            
            context.update({
                'course_offering': course_offering,
                'students': students,
                'exam_results': aggregated_results,
                'midterm_max': midterm_max,
                'sessional_max': sessional_max,
                'final_max': final_max,
                'practical_max': practical_max,
                'totalMax': total_max,
                'show_form': show_form,
            })
            
        except CourseOffering.DoesNotExist:
            messages.error(request, 'Course offering not found or you do not have permission to access it.')
    
    return render(request, 'faculty_staff/exam_results.html', context)





def is_course_repeated(student, course_offering):
    """
    Check if a student has previously taken and failed this course
    Returns tuple of (is_repeated, previous_results)
    """
    # Get all previous exam results for this student and course
    previous_results = ExamResult.objects.filter(
        student=student,
        course_offering__course=course_offering.course,
        is_fail=True  # Only count previous failures as repeats
    ).exclude(  # Exclude the current course offering
        course_offering__id=course_offering.id
    ).select_related('course_offering')
    
    return previous_results.exists(), previous_results

@login_required    
def record_exam_results(request):  
    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        student_ids = request.POST.getlist('student_ids[]')  # Get list of student IDs
        
        if not course_offering_id:
            messages.error(request, 'Course offering ID is required.')
            return redirect('faculty_staff:exam_results', course_offering_id=course_offering_id)

        try:
            course_offering = get_object_or_404(
                CourseOffering, 
                id=course_offering_id, 
                teacher=request.user.teacher_profile
            )
            
            if 'result_id' in request.POST:
                # Update existing record
                try:
                    result_id = request.POST.get('result_id')
                    result = get_object_or_404(ExamResult, pk=result_id, course_offering=course_offering)

                    midterm = request.POST.get('midterm')
                    sessional = request.POST.get('sessional')
                    final = request.POST.get('final')
                    practical = request.POST.get('practical') if course_offering.course.lab_work > 0 else 0
                    remarks = request.POST.get('remarks')
                    total_obtained = request.POST.get('total_obtained')
                    percentage = request.POST.get('percentage')
                    
                    # Check if student is repeating this course
                    is_repeat, previous_results = is_course_repeated(result.student, course_offering)
                    if is_repeat:
                        remarks = 'Repeat' + (f' - {remarks}' if remarks else '')
                        
                        # Update the current enrollment to mark as repeat
                        try:
                            enrollment = CourseEnrollment.objects.get(
                                student_semester_enrollment__student=result.student,
                                course_offering=course_offering
                            )
                            enrollment.is_repeat = True
                            enrollment.save()
                        except CourseEnrollment.DoesNotExist:
                            pass
                            
                        # Update previous failed attempts to mark them as replaced
                        for prev_result in previous_results:
                            if 'Repeated in' not in (prev_result.remarks or ''):
                                prev_result.remarks = f"Repeated in {course_offering.semester.name} {course_offering.academic_session.name}"
                                prev_result.save()

                    print(f"Updating result for student {result.student.applicant.full_name} with marks: {midterm}, {sessional}, {final}, {practical}, {remarks}, {total_obtained}, {percentage}")

                    result.total_marks = total_obtained
                    if percentage and isinstance(percentage, str) and '%' in percentage:
                        percentage = percentage.replace('%', '').strip()
                        result.percentage = float(percentage) if percentage else 0.0
                    result.remarks = remarks or None
                    result.graded_by = request.user.teacher_profile
                    result.graded_at = timezone.now()
                    result.save()
                    
                    # Mark the course enrollment as completed
                    try:
                        enrollment = CourseEnrollment.objects.get(
                            student_semester_enrollment__student=result.student,
                            course_offering=course_offering,
                            status='enrolled'
                        )
                        enrollment.status = 'completed'
                        enrollment.completed_at = timezone.now()
                        enrollment.save()
                    except CourseEnrollment.DoesNotExist:
                        pass  # Handle case where enrollment doesn't exist

                    messages.success(request, 'Result updated successfully and course enrollment marked as completed.')
                    return redirect('faculty_staff:exam_results', course_offering_id)
                
                except ExamResult.DoesNotExist:
                    messages.error(request, 'Exam result not found for update.')
                    return redirect('faculty_staff:exam_results', course_offering_id)

            
            if not student_ids:
                messages.error(request, 'No students selected for this course offering.')
                return redirect('faculty_staff:exam_results', course_offering_id)
                
            midterm_max = course_offering.course.credits * 4
            sessional_max = course_offering.course.credits * 2
            final_max = course_offering.course.credits * 14
            practical_max = course_offering.course.lab_work * 20
            total_max = midterm_max + sessional_max + final_max + (practical_max if course_offering.course.lab_work > 0 else 0)
            
            success_count = 0
            error_messages = []
            
            for student_id in student_ids:
                try:
                    student = Student.objects.get(applicant_id=student_id)
                    
                    midterm = request.POST.get(f'midterm_{student_id}')
                    sessional = request.POST.get(f'sessional_{student_id}')
                    final = request.POST.get(f'final_{student_id}')
                    practical = request.POST.get(f'practical_{student_id}') if course_offering.course.lab_work > 0 else None
                    remarks = request.POST.get(f'remarks_{student_id}')
                    
                    # Validate marks
                    defaults = {
                        'graded_by': request.user.teacher_profile,
                        'graded_at': timezone.now(),
                        'remarks': remarks or None,
                        'midterm_total': midterm_max,
                        'sessional_total': sessional_max,
                        'final_total': final_max,
                        'practical_total': practical_max if course_offering.course.lab_work > 0 else 0
                    }
                    
                    total_obtained = 0
                    if midterm and midterm.strip():
                        midterm_value = float(midterm)
                        if not (0 <= midterm_value <= midterm_max):
                            error_messages.append(f"{student.applicant.full_name}: Midterm marks must be between 0 and {midterm_max}.")
                            continue
                        defaults['midterm_obtained'] = midterm_value
                        total_obtained += midterm_value
                    
                    if sessional and sessional.strip():
                        sessional_value = float(sessional)
                        if not (0 <= sessional_value <= sessional_max):
                            error_messages.append(f"{student.applicant.full_name}: Sessional marks must be between 0 and {sessional_max}.")
                            continue
                        defaults['sessional_obtained'] = sessional_value
                        total_obtained += sessional_value
                    
                    if final and final.strip():
                        final_value = float(final)
                        if not (0 <= final_value <= final_max):
                            error_messages.append(f"{student.applicant.full_name}: Final marks must be between 0 and {final_max}.")
                            continue
                        defaults['final_obtained'] = final_value
                        total_obtained += final_value
                    
                    if practical and practical.strip() and course_offering.course.lab_work > 0:
                        practical_value = float(practical)
                        if not (0 <= practical_value <= practical_max):
                            error_messages.append(f"{student.applicant.full_name}: Practical marks must be between 0 and {practical_max}.")
                            continue
                        defaults['practical_obtained'] = practical_value
                        total_obtained += practical_value
                    
                    # Calculate total and percentage
                    defaults['total_marks'] = total_obtained
                    defaults['percentage'] = (total_obtained / total_max * 100) if total_max > 0 else 0.0
                    
                    # Check if student is repeating this course
                    is_repeat, previous_results = is_course_repeated(student, course_offering)
                    
                    if is_repeat and previous_results.exists():
                        # Get the most recent failed attempt
                        prev_result = previous_results.latest('graded_at')
                        
                        # Update the previous failed attempt with new marks
                        prev_result.midterm_obtained = defaults.get('midterm_obtained')
                        prev_result.sessional_obtained = defaults.get('sessional_obtained')
                        prev_result.final_obtained = defaults.get('final_obtained')
                        prev_result.practical_obtained = defaults.get('practical_obtained')
                        prev_result.total_marks = defaults.get('total_marks')
                        prev_result.percentage = defaults.get('percentage')
                        prev_result.graded_by = request.user.teacher_profile
                        prev_result.graded_at = timezone.now()
                        prev_result.remarks = f"Retake passed in {course_offering.semester.name} {course_offering.academic_session.name}"
                        prev_result.save()
                        
                        # Update the current enrollment to mark as retake
                        try:
                            enrollment = CourseEnrollment.objects.get(
                                student_semester_enrollment__student=student,
                                course_offering=course_offering
                            )
                            enrollment.is_repeat = True
                            enrollment.status = 'retake'
                            enrollment.save()
                        except CourseEnrollment.DoesNotExist:
                            pass
                            
                        # Skip creating a new result record
                        success_count += 1
                        continue
                    
                    # Only save if at least one mark is provided and it's not a retake case (handled above)
                    if any(key in defaults for key in ['midterm_obtained', 'sessional_obtained', 'final_obtained', 'practical_obtained']):
                        # For new attempts (not retakes)
                        exam_result, created = ExamResult.objects.update_or_create(
                            course_offering=course_offering,
                            student=student,
                            defaults=defaults
                        )
                        exam_result.save()
                        
                        # Mark the course enrollment as completed
                        try:
                            enrollment = CourseEnrollment.objects.get(
                                student_semester_enrollment__student=student,
                                course_offering=course_offering,
                                status='enrolled'
                            )
                            enrollment.status = 'completed'
                            enrollment.completed_at = timezone.now()
                            enrollment.save()
                        except CourseEnrollment.DoesNotExist:
                            pass  # Handle case where enrollment doesn't exist
                            
                        success_count += 1
                
                except Student.DoesNotExist:
                    error_messages.append(f"Student with ID {student_id} not found.")
                except ValueError as e:
                    error_messages.append(f"Invalid marks format for student ID {student_id}: {str(e)}")
                except Exception as e:
                    error_messages.append(f"Error processing marks for student ID {student_id}: {str(e)}")
            
            if success_count > 0:
                messages.success(request, f'Successfully saved results for {success_count} student(s).')
            if error_messages:
                for error in error_messages:
                    messages.error(request, error)  
            
            return redirect ('faculty_staff:exam_results', course_offering_id)
            
        except CourseOffering.DoesNotExist:
            messages.error(request, 'Course offering not found or you do not have permission to access it.')
            return redirect('faculty_staff:exam_results', course_offering_id)
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('faculty_staff:exam_results', course_offering_id)
    
    return redirect('faculty_staff:exam_results', course_offering_id)




def teacher_course_list(request):
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug: Log the current user
    logger.info(f"Current user: {request.user} (ID: {request.user.id})")
    
    try:
        # Filter course offerings where the current teacher is either the original or replacement teacher
        course_offerings = CourseOffering.objects.filter(
            Q(teacher__user_id=request.user.id) | Q(replacement_teacher__user_id=request.user.id),
            semester__is_active=True
        ).select_related('course', 'semester', 'academic_session', 'teacher__user', 'replacement_teacher__user', 'program', 'department')
        
        # Debug: Log the number of course offerings found
        logger.info(f"Found {len(course_offerings)} course offerings for user {request.user.id}")
        
        if not course_offerings.exists():
            logger.warning("No course offerings found for the current user")
        else:
            # Debug: Log first few course offerings
            for i, offering in enumerate(course_offerings[:3], 1):
                logger.info(f"Offering {i}: {offering.course.code} - {offering.course.name} (Teacher: {getattr(offering.teacher, 'user', None)}, Replacement: {getattr(offering.replacement_teacher, 'user', None)})")
        
        # Get active replacements for these course offerings
        replacements = LectureReplacement.objects.filter(
            course_offering__in=course_offerings,
            replacement_teacher__user=request.user,
            replacement_date__isnull=False
        ).select_related('course_offering', 'original_teacher__user', 'replacement_teacher__user')
        
        # Debug: Log replacements found
        logger.info(f"Found {len(replacements)} replacements for user {request.user.id}")
        
        # Create a dictionary of replacement info keyed by course_offering_id
        replacement_info = {}
        for replacement in replacements:
            replacement_info[replacement.course_offering_id] = {
                'is_replacement': True,
                'replacement_type': replacement.replacement_type,
                'replacement_end_date': replacement.replacement_end_date,
                'original_teacher': replacement.original_teacher,
            }
            logger.info(f"Replacement found: {replacement} (Type: {replacement.replacement_type}, End: {replacement.replacement_end_date})")

        # Add replacement info to each course offering
        for offering in course_offerings:
            info = replacement_info.get(offering.id, {})
            offering.is_replacement = info.get('is_replacement', False)
            offering.replacement_type = info.get('replacement_type')
            offering.replacement_end_date = info.get('replacement_end_date')
            
            # Debug: Log offering details
            logger.info(f"Processing offering {offering.id}: {offering.course.code} - {offering.course.name}")
            logger.info(f"  - Teacher: {getattr(offering.teacher, 'user', None)}")
            logger.info(f"  - Replacement Teacher: {getattr(offering.replacement_teacher, 'user', None)}")
            logger.info(f"  - Is replacement: {offering.is_replacement}")
            
            if not offering.is_replacement and offering.replacement_teacher_id and offering.replacement_teacher.user_id == request.user.id:
                # This is a permanent replacement
                logger.info("  - Marked as permanent replacement")
                offering.is_replacement = True
                offering.replacement_type = 'permanent'
                offering.original_teacher = offering.teacher
            
            # Ensure we have the original teacher set for display
            if not hasattr(offering, 'original_teacher') and offering.is_replacement:
                offering.original_teacher = offering.teacher
                
        context = {
            'course_offerings': course_offerings,
            'debug_info': {
                'offerings_count': len(course_offerings),
                'replacements_count': len(replacements),
            }
        }
        
    except Exception as e:
        logger.error(f"Error in teacher_course_list: {str(e)}", exc_info=True)
        context = {
            'course_offerings': [],
            'error': str(e)
        }
    return render(request, 'faculty_staff/teacher_course_list.html', context)    

@login_required
def logout_view(request):
    logout(request)   
    return redirect('faculty_staff:login')




@hod_required
def semester_management(request):
    """
    View to display, search, and manage semesters for the Head of Department's department.
    """
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        logger.warning(f'Unauthorized access attempt by user: {request.user} (ID: {request.user.id})')
        return render(request, 'faculty_staff/semester_management.html', {
            'error': 'You do not have permission to manage semesters.',
            'programs': [],
            'semesters': [],
            'academic_sessions': [],
        })
    
    hod_department = request.user.teacher_profile.department
    logger.info(f'Semester management page loaded for user: {request.user} (ID: {request.user.id}), department: {hod_department}')

    # Get search and filter parameters
    search_query = request.GET.get('q', '')
    program_id = request.GET.get('program_id', '')
    session_id = request.GET.get('session_id', '')
    print(f'Semester management search query: {search_query}, program_id: {program_id}, session_id: {session_id}')

    # Filter semesters by department
    semesters = Semester.objects.filter(program__department=hod_department).order_by('program', 'number')
    
    # Apply filters
    if search_query:
        semesters = semesters.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(program__name__icontains=search_query)
        )
    if program_id:
        semesters = semesters.filter(program__id=program_id, program__department=hod_department)
    if session_id:
        semesters = semesters.filter(session__id=session_id)

    # Debug: Log total semesters and active/inactive breakdown
    total_semesters = semesters.count()
    active_semesters = semesters.filter(is_active=True).count()
    inactive_semesters = total_semesters - active_semesters
    logger.debug(f'Total semesters: {total_semesters}, Active: {active_semesters}, Inactive: {inactive_semesters}')
    for semester in semesters:
        logger.debug(f'Semester: {semester.name}, Program: {semester.program.name}, Is Active: {semester.is_active}')

    # Pagination
    paginator = Paginator(semesters, 20)  # 20 semesters per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Debug: Log programs and their active status
    programs = Program.objects.filter(department=hod_department)
    logger.debug(f'Total programs: {programs.count()}')
    for program in programs:
        active_semesters_in_program = Semester.objects.filter(program=program, is_active=True).count()
        logger.debug(f'Program: {program.name}, Active Semesters: {active_semesters_in_program}, Total Semesters: {Semester.objects.filter(program=program).count()}')

    context = {
        'programs': programs,   
        'semesters': page_obj,
        'search_query': search_query,
        'selected_program': program_id,
        'selected_session': session_id,
        'academic_sessions': AcademicSession.objects.filter(is_active=True).order_by('-start_year'),
    }
    return render(request, 'faculty_staff/semester_management.html', context)




@hod_required
def get_programs(request):
    """
    AJAX view to fetch programs for the Head of Department's department.
    """
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'message': 'User has no teacher profile.'}, status=403)
    
    hod_department = request.user.teacher_profile.department
    programs = Program.objects.filter(department=hod_department).order_by('name')
    results = [{'id': program.id, 'text': program.name} for program in programs]
    return JsonResponse({'results': results})

@hod_required
def add_semester(request):
    """
    AJAX view to add a new semester for the Head of Department's department.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to add semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    hod_department = request.user.teacher_profile.department
    program_id = request.POST.get('program_id')
    session_id = request.POST.get('session_id')  # New field for session
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'
    
    print(f'Add semester attempt: program_id={program_id}, session_id={session_id}, number={number}, name={name}, user={request.user}, department={hod_department}')
    
    # Validate required fields
    required_fields = {'program_id': 'Program', 'session_id': 'Session', 'number': 'Semester Number', 'name': 'Name'}
    missing_fields = [field_label for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        print(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})
    
    try:
        program = Program.objects.get(id=program_id, department=hod_department)
        session = get_object_or_404(AcademicSession, id=session_id)  # Validate session
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")
        
        # Create semester with session
        semester = Semester(
            program=program,
            session=session,  # Assign the session object
            number=number,
            name=name,
            description=description,
            start_time=start_time or None,
            end_time=end_time or None,
            is_active=is_active
        )
        semester.save()  # Validation in model will check sequential numbers
        print(f'Semester created: {semester} by user: {request.user} for session: {session}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} added successfully for session {session.name}!',
            'semester_id': semester.id
        })
    except Program.DoesNotExist:
        print(f'Program not found or not in department: program_id={program_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Selected program is invalid or not in your department.'})
    except AcademicSession.DoesNotExist:
        print(f'Session not found: session_id={session_id}')
        return JsonResponse({'success': False, 'message': 'Selected session is invalid.'})
    except ValueError as e:
        print(f'Invalid data: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Invalid data: {str(e)}'})
    except ValidationError as e:
        print(f'Validation error: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Validation error: {str(e)}'})
    except Exception as e:
        print(f'Error adding semester: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error adding semester: {str(e)}'})    
    


@login_required   
def edit_semester(request):
    """
    AJAX view to edit an existing semester in the Head of Department's department.
    Updates associated StudentSemesterEnrollment records to 'completed' if semester is set to inactive.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        logger.warning(f'Unauthorized or invalid request to edit semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})

    hod_department = request.user.teacher_profile.department
    semester_id = request.POST.get('semester_id')
    program_id = request.POST.get('program_id')
    session_id = request.POST.get('session_id')
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'

    logger.info(
        f'Edit semester attempt by {request.user} - '
        f'semester_id={semester_id}, program_id={program_id}, session_id={session_id}, '
        f'number={number}, name={name}, department={hod_department}'
    )

    required_fields = {
        'semester_id': 'Semester',
        'program_id': 'Program',
        'session_id': 'Session',
        'number': 'Semester Number',
        'name': 'Name'
    }
    missing_fields = [
        field_label for field_name, field_label in required_fields.items()
        if not request.POST.get(field_name)
    ]
    if missing_fields:
        logger.error(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})

    try:
        semester = get_object_or_404(Semester, id=semester_id, program__department=hod_department)
        program = Program.objects.get(id=program_id, department=hod_department)
        session = get_object_or_404(AcademicSession, id=session_id)
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")

        # Log semester state before update
        logger.info(
            f"Semester BEFORE update -> ID: {semester.id}, Name: {semester.name}, "
            f"Number: {semester.number}, Active: {semester.is_active}"
        )

        # If being set inactive, mark enrollments as completed
        enrollments_updated = False
        if semester.is_active and not is_active:
            enrollments = semester.semester_enrollments.filter(status='enrolled')
            enrollment_count = enrollments.count()
            for enrollment in enrollments:
                enrollment.status = 'completed'
                enrollment.save()
            enrollments_updated = enrollment_count > 0
            logger.info(f'Marked {enrollment_count} enrollments as completed for semester: {semester.name}')

        # Apply updates
        semester.program = program
        semester.session = session
        semester.number = number
        semester.name = name
        semester.description = description
        semester.start_time = start_time or None
        semester.end_time = end_time or None
        semester.is_active = is_active
        semester.save()

        # Log semester state after update
        logger.info(
            f"Semester AFTER update -> ID: {semester.id}, Name: {semester.name}, "
            f"Number: {semester.number}, Now Active: {semester.is_active}"
        )

        message = f'Semester "{semester.name}" updated successfully!'
        if enrollments_updated:
            message += f' {enrollment_count} student enrollments marked as completed.'

        return JsonResponse({
            'success': True,
            'message': message,
            'semester_id': semester.id
        })

    except Semester.DoesNotExist:
        logger.error(f'Semester not found: semester_id={semester_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Semester is invalid or not in your department.'})
    except Program.DoesNotExist:
        logger.error(f'Program not found: program_id={program_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Program is invalid or not in your department.'})
    except AcademicSession.DoesNotExist:
        logger.error(f'Session not found: session_id={session_id}')
        return JsonResponse({'success': False, 'message': 'Session is invalid.'})
    except ValueError as e:
        logger.error(f'Invalid data: {e}')
        return JsonResponse({'success': False, 'message': f'Invalid data: {e}'})
    except ValidationError as e:
        logger.error(f'Validation error: {e}')
        return JsonResponse({'success': False, 'message': f'Validation error: {e}'})
    except Exception as e:
        logger.error(f'Unexpected error while editing semester: {e}')
        return JsonResponse({'success': False, 'message': f'Error: {e}'})

    
@login_required
def delete_semester(request):
    """
    AJAX view to delete a semester in the Head of Department's department.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to delete semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    hod_department = request.user.teacher_profile.department
    semester_id = request.POST.get('semester_id')
    print(f'Delete semester attempt: semester_id={semester_id}, user={request.user}, department={hod_department}')
    
    if not semester_id:
        print('Missing semester_id for deletion')
        return JsonResponse({'success': False, 'message': 'Missing semester ID.'})
    
    try:
        semester = get_object_or_404(Semester, id=semester_id, program__department=hod_department)
        semester_name = semester.name
        semester.delete()
        print(f'Semester deleted: {semester_name} by user: {request.user}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester_name} deleted successfully!'
        })
    except Semester.DoesNotExist:
        print(f'Semester not found or not in department: semester_id={semester_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Semester is invalid or not in your department.'})
    except Exception as e:
        print(f'Error deleting semester: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error deleting semester: {str(e)}'})

    
    
    
    


@hod_or_professor_required
def attendance(request, offering_id=None):
    students = []
    course_offering_id = offering_id
    course_shift = None
    is_active_slot = False
    today_date = timezone.now().astimezone(pytz.timezone('Asia/Karachi')).date()
    current_datetime = timezone.now().astimezone(pytz.timezone('Asia/Karachi'))
    current_time = current_datetime.time()
    current_day = today_date.strftime('%A').lower()
    selected_shift = request.GET.get('shift')  # Get shift from query parameters (if provided)

    logger.info(
        f"Processing attendance request. "
        f"UTC: {timezone.now()}, PKT: {current_datetime}, "
        f"Current time (PKT): {current_time}, Day: {current_day}, "
        f"Course Offering ID: {course_offering_id}, Selected Shift: {selected_shift}"
    )

    if course_offering_id:
        try:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
            course_shift = course_offering.shift
            logger.info(f"Course offering found: {course_offering.course.code}, Shift: {course_shift}, Semester: {course_offering.semester}")

            # Check for active timetable slot
            timetable_slots = TimetableSlot.objects.filter(
                course_offering=course_offering,
                day=current_day,
                start_time__lte=current_time,
                end_time__gte=current_time
            )
            is_active_slot = timetable_slots.exists()

            if is_active_slot:
                for slot in timetable_slots:
                    logger.info(
                        f"Active timetable slot: Course: {course_offering.course.code}, "
                        f"Day: {slot.day}, Start: {slot.start_time}, End: {slot.end_time}"
                    )
            else:
                all_slots = TimetableSlot.objects.filter(course_offering=course_offering)
                if all_slots.exists():
                    logger.warning(
                        f"No active timetable slot for Course Offering ID: {course_offering_id} "
                        f"on {current_day} at {current_time}. Available slots:"
                    )
                    for slot in all_slots:
                        logger.warning(
                            f"Slot: Day: {slot.day}, Start: {slot.start_time}, End: {slot.end_time}"
                        )
                else:
                    logger.warning(f"No timetable slots defined for Course Offering ID: {course_offering_id}")

            # Determine effective shift for filtering
            effective_shift = selected_shift if selected_shift in ['morning', 'evening'] else course_shift
            if course_shift == 'both' and selected_shift in ['morning', 'evening']:
                effective_shift = selected_shift
            elif course_shift == 'both':
                effective_shift = None  # No shift filter for 'both' unless specified

            # Fetch students with shift filtering
            enrollments = CourseEnrollment.objects.filter(
                course_offering=course_offering,
                status='enrolled'
            ).select_related('student_semester_enrollment__student__applicant')
            logger.info(f"Initial enrollment query returned {enrollments.count()} records")

            students = []
            for enrollment in enrollments:
                student = enrollment.student_semester_enrollment.student
                student_shift = getattr(student.applicant, 'shift', None)
                # Skip if semester does not match
                if enrollment.student_semester_enrollment.semester != course_offering.semester:
                    logger.warning(
                        f"Enrollment skipped: Student {student.applicant.full_name}, "
                        f"Enrollment semester {enrollment.student_semester_enrollment.semester} "
                        f"does not match course offering semester {course_offering.semester}"
                    )
                    continue
                # Apply shift filter if course shift is not 'both' or a specific shift is selected
                if effective_shift in ['morning', 'evening'] and student_shift != effective_shift:
                    logger.warning(
                        f"Student {student.applicant.full_name} skipped: "
                        f"Student shift {student_shift} does not match effective shift {effective_shift}"
                    )
                    continue
                students.append({
                    'id': student.applicant.id,
                    'name': student.applicant.full_name,
                    'college_roll_no': student.college_roll_no or 'N/A',
                    'university_roll_no': student.university_roll_no or 'N/A',
                    'role': student.applicant.role if hasattr(student.applicant, 'role') else None,
                    'shift': student_shift
                })
            logger.info(f"Fetched {len(students)} students for course offering: {course_offering_id}, effective shift: {effective_shift}")

        except Exception as e:
            logger.error(f"Error processing course offering ID {course_offering_id}: {str(e)}", exc_info=True)
            return render(request, 'faculty_staff/attendance.html', {
                'students': [],
                'course_offering_id': course_offering_id,
                'course_shift': None,
                'selected_shift': selected_shift,
                'today_date': today_date,
                'is_active_slot': is_active_slot,
                'error_message': f"Error loading course offering: {str(e)}"
            })

    print(f'slot is: {is_active_slot}, course shift is {course_shift}, selected shift is {selected_shift}')
    context = {
        'students': students,
        'course_offering_id': course_offering_id,
        'course_shift': course_shift,
        'selected_shift': selected_shift,
        'today_date': today_date,
        'is_active_slot': is_active_slot,
    }
    return render(request, 'faculty_staff/attendance.html', context)




@hod_or_professor_required
def record_attendance(request):
    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        shift = request.POST.get('shift')
        logger.info(f"Recording attendance for course_offering_id: {course_offering_id}, shift: {shift}")

        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering is required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        if course_offering.shift == 'both' and shift not in ['morning', 'evening']:
            logger.warning(f"Shift required for course with 'both' shifts, received: {shift}")
            return JsonResponse({'success': False, 'message': 'Shift is required for this course.'})

        today = timezone.now().date()
        # Check if attendance already exists
        effective_shift = shift if shift in ['morning', 'evening'] else None
        if Attendance.objects.filter(
            course_offering=course_offering,
            date=today,
            shift=effective_shift if course_offering.shift == 'both' else None
        ).exists():
            return JsonResponse({'success': False, 'message': f'Attendance already recorded for {effective_shift or "this course"} on this date.'})

        enrollments = CourseEnrollment.objects.filter(
            course_offering=course_offering,
            status='enrolled'
        ).select_related('student_semester_enrollment__student__applicant')
        if effective_shift in ['morning', 'evening']:
            enrollments = enrollments.filter(student_semester_enrollment__student__applicant__shift=effective_shift)

        teacher = get_object_or_404(Teacher, user=request.user)
        for enrollment in enrollments:
            student = enrollment.student_semester_enrollment.student
            student_id = student.applicant.id
            status = request.POST.get(f'status_{student_id}')
            if status in ['present', 'absent', 'leave']:
                Attendance.objects.update_or_create(
                    student=student,
                    course_offering=course_offering,
                    date=today,
                    shift=effective_shift if course_offering.shift == 'both' else None,
                    defaults={
                        'status': status,
                        'recorded_by': teacher,
                        'recorded_at': timezone.now()
                    }
                )

        logger.info(f"Attendance recorded successfully for course_offering_id: {course_offering_id}, shift: {effective_shift}")
        return JsonResponse({'success': True, 'message': 'Attendance recorded successfully.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@login_required
def load_students_for_course(request):
    if request.method == "GET":
        course_offering_id = request.GET.get('course_offering_id')
        shift = request.GET.get('shift')
        logger.info(f"Loading students for course_offering_id: {course_offering_id}, shift: {shift}")

        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})

        try:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
            effective_shift = shift if shift in ['morning', 'evening'] else course_offering.shift
            logger.info(f"Effective shift: {effective_shift} (course_shift: {course_offering.shift}, requested shift: {shift})")

            enrollments = CourseEnrollment.objects.filter(
                course_offering=course_offering,
                status='enrolled'
            ).select_related(
                'student_semester_enrollment__student__applicant',
                'student_semester_enrollment__semester'
            )

            students = []
            for enrollment in enrollments:
                student = enrollment.student_semester_enrollment.student
                student_shift = getattr(student.applicant, 'shift', None)
                if enrollment.student_semester_enrollment.semester != course_offering.semester:
                    logger.warning(
                        f"Enrollment skipped: Student {student.applicant.full_name}, "
                        f"Enrollment semester {enrollment.student_semester_enrollment.semester} "
                        f"does not match course offering semester {course_offering.semester}"
                    )
                    continue
                if effective_shift in ['morning', 'evening'] and student_shift != effective_shift:
                    logger.warning(
                        f"Student {student.applicant.full_name} skipped: "
                        f"Student shift {student_shift} does not match effective shift {effective_shift}"
                    )
                    continue
                students.append({
                    'id': student.applicant.id,
                    'name': student.applicant.full_name,
                    'college_roll_no': student.college_roll_no or 'N/A',
                    'university_roll_no': student.university_roll_no or 'N/A',
                    'role': student.role if hasattr(student, 'role') else None,
                    'shift': student_shift
                })

            logger.info(f"Fetched {len(students)} students for course offering: {course_offering_id}, effective shift: {effective_shift}")
            return JsonResponse({
                'success': True,
                'students': students
            })

        except Exception as e:
            logger.error(f"Error loading students for course offering {course_offering_id}: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f"Error loading students: {str(e)}"
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@login_required
def load_attendance(request):
    if request.method == "GET":
        course_offering_id = request.GET.get('course_offering_id')
        date_str = request.GET.get('date')
        shift = request.GET.get('shift')
        if course_offering_id and date_str:
            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
                attendances = Attendance.objects.filter(
                    course_offering=course_offering,
                    date=date
                ).select_related('student__applicant', 'recorded_by')
                if shift == 'both':
                    pass  # Include all shifts
                elif shift in ['morning', 'evening'] and course_offering.shift == 'both':
                    attendances = attendances.filter(shift=shift)
                elif course_offering.shift != 'both':
                    attendances = attendances.filter(shift__isnull=True)
                
                results = [{
                    'id': a.id,
                    'student_id': a.student.applicant.id,
                    'student_name': a.student.applicant.full_name,
                    'college_roll_no': a.student.college_roll_no,
                    'university_roll_no': a.student.university_roll_no,
                    'course_code': a.course_offering.course.code,
                    'status': a.status,
                    'shift': a.shift,
                    'recorded_by': a.recorded_by.user.get_full_name() if a.recorded_by else 'Unknown'
                } for a in attendances]
                
                return JsonResponse({
                    'success': True,
                    'attendances': results
                })
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format.'})
        return JsonResponse({'success': False, 'message': 'Course offering ID and date are required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@login_required   
def edit_attendance(request):
    if request.method == "POST":
        attendance_id = request.POST.get('attendance_id')
        student_id = request.POST.get('student_id')
        status = request.POST.get('status')
        shift = request.POST.get('shift') or None
        if attendance_id and student_id and status in ['present', 'absent', 'leave']:
            attendance = get_object_or_404(Attendance, id=attendance_id, student__applicant_id=student_id)
            if attendance.date != timezone.now().date():
                return JsonResponse({'success': False, 'message': "Can only edit today's attendance."})
            teacher = get_object_or_404(Teacher, user=request.user)
            attendance.status = status
            attendance.shift = shift
            attendance.recorded_by = teacher
            attendance.recorded_at = timezone.now()
            attendance.save()
            return JsonResponse({'success': True, 'message': 'Attendance updated successfully.'})
        return JsonResponse({'success': False, 'message': 'Invalid data provided.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@hod_or_professor_required
def view_students(request , offering_id):
    course_offering_id = offering_id
    if not course_offering_id:
        return render(request, 'faculty_staff/error.html', {
            'message': 'No course offering selected.',
        }, status=400)

    try:
        course_offering = CourseOffering.objects.get(id=course_offering_id, teacher=request.user.teacher_profile)
    except CourseOffering.DoesNotExist:
        return render(request, 'faculty_staff/error.html', {
            'message': 'Course offering not found or you do not have permission to view it.',
        }, status=404)

    # Fetch enrolled students via CourseEnrollment
    enrollments = CourseEnrollment.objects.filter(course_offering=course_offering, status='enrolled')
    students = []
    for enrollment in enrollments:
        student = enrollment.student_semester_enrollment.student
        # Count assignment submissions
        assignment_submissions = AssignmentSubmission.objects.filter(
            assignment__course_offering=course_offering,
            student=student
        ).count()
        # Count attendance (assuming Attendance model tracks presence)
        attendance_count = Attendance.objects.filter(
            course_offering=course_offering,
            student=student
        ).count()  # Adjust if attendance has a 'present' field
        students.append({
            'id': student.applicant.id,  # Use applicant.id as the primary key
            'full_name': f"{student.applicant.full_name}",  # Assuming Applicant has full_name
            'uni_roll_number': student.university_roll_no,
            'clg_roll_number': student.college_roll_no,
            'email': student.user.email if student.user else 'N/A',
            'assignment_submissions': assignment_submissions,
            'attendance_count': attendance_count,
        })

    return render(request, 'faculty_staff/view_students.html', {
        'course_offering': course_offering,
        'students': students,
    })

@hod_or_professor_required    
def student_performance(request, course_offering_id, student_id):
    course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
    enrollment = get_object_or_404(CourseEnrollment, course_offering=course_offering, student_semester_enrollment__student_id=student_id)
    student = enrollment.student_semester_enrollment.student

    # Fetch detailed attendance data
    attendance_records = Attendance.objects.filter(student=student, course_offering=course_offering)
    attendance_summary = attendance_records.values('status').annotate(count=Count('status'))
    attendance_data = {item['status']: item['count'] for item in attendance_summary}
    attendance_total = attendance_records.count()
    attendance_present = attendance_data.get('present', 0)
    attendance_absent = attendance_data.get('absent', 0)
    attendance_leave = attendance_data.get('leave', 0)

    # Fetch assignment submissions
    assignments = AssignmentSubmission.objects.filter(
        student=student,
        assignment__course_offering=course_offering
    ).values('assignment__title').annotate(
        score=Sum('marks_obtained'),
        max_score=Max('assignment__max_points')
    ).order_by('assignment__title')

    # Fetch quiz submissions, ensuring one row per quiz
    quizzes = QuizSubmission.objects.filter(
        student=student,
        quiz__course_offering=course_offering,
        quiz__publish_flag=True
    ).values('quiz__id', 'quiz__title').annotate(
        score=Max('score'),  # Use Max to handle multiple submissions, if any
        max_score=Subquery(
            Question.objects.filter(quiz=OuterRef('quiz')).values('quiz').annotate(
                total=Sum('marks')
            ).values('total')[:1]
        )
    ).order_by('quiz__title')

    context = {
        'course_offering': course_offering,
        'student': student,
        'attendance_total': attendance_total,    
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'attendance_leave': attendance_leave,
        'attendance_percentage': (attendance_present / attendance_total * 100) if attendance_total > 0 else 0,
        'assignments': assignments,
        'quizzes': quizzes,
    }
    logger.info(f"Fetched performance data for student {student.applicant.full_name} in course offering {course_offering_id}")
    return render(request, 'faculty_staff/student_performance.html', context)
    
@hod_or_professor_required
def student_semester_performance(request, student_id):
    student = get_object_or_404(Student, pk=student_id)

    # Get all semester enrollments for the student
    semester_enrollments = StudentSemesterEnrollment.objects.filter(
        student=student,
    ).select_related('semester').order_by('semester__number')

    logger.info(f"Found {semester_enrollments.count()} semester enrollments for student {student_id}")

    # Aggregate performance stats for all semesters
    stats_by_semester = []
    for sem_enrollment in semester_enrollments:
        semester = sem_enrollment.semester
        logger.info(f"Processing Semester {semester.number} (ID: {semester.id})")

        # Fetch all course enrollments for the semester
        course_enrollments = CourseEnrollment.objects.filter(
            student_semester_enrollment=sem_enrollment
        ).select_related('course_offering__course')
        course_offerings = [enrollment.course_offering for enrollment in course_enrollments]

        # Get exam results for all courses in this semester
        exam_results = ExamResult.objects.filter(
            student=student,
            course_offering__in=course_offerings
        ).select_related('course_offering__course')

        # Calculate GPA for the semester
        total_credit_hours = 0
        total_quality_points = 0
        semester_gpa = None
        
        exam_stats = []
        for result in exam_results:
            # Calculate grade points based on percentage
            percentage = float(result.percentage) if result.percentage else 0
            if percentage >= 85:
                grade = 'A+'
                grade_points = 4.0
            elif percentage >= 80:
                grade = 'A'
                grade_points = 4.0
            elif percentage >= 75:
                grade = 'B+'
                grade_points = 3.5
            elif percentage >= 70:
                grade = 'B'
                grade_points = 3.0
            elif percentage >= 65:
                grade = 'B-'
                grade_points = 2.7
            elif percentage >= 60:
                grade = 'C+'
                grade_points = 2.3
            elif percentage >= 55:
                grade = 'C'
                grade_points = 2.0
            elif percentage >= 50:
                grade = 'C-'
                grade_points = 1.7
            elif percentage >= 40:
                grade = 'D'
                grade_points = 1.0
            else:
                grade = 'F'
                grade_points = 0.0

            credit_hours = result.course_offering.course.credits or 3  # Default to 3 if not set
            quality_points = credit_hours * grade_points
            
            exam_stats.append({
                'course_code': result.course_offering.course.code,
                'course_name': result.course_offering.course.name,
                'percentage': percentage,
                'grade': grade,
                'credit_hours': credit_hours,
                'grade_points': grade_points,
                'quality_points': quality_points,
                'status': 'Pass' if percentage >= 40 else 'Fail',
                'remarks': result.remarks or ''
            })
            
            # Update GPA calculation
            total_credit_hours += credit_hours
            total_quality_points += quality_points

        # Calculate semester GPA if we have results
        if total_credit_hours > 0:
            semester_gpa = round(total_quality_points / total_credit_hours, 2)

        # Aggregate attendance data
        attendance_records = Attendance.objects.filter(student=student, course_offering__in=course_offerings)
        attendance_summary = attendance_records.values('status').annotate(count=Count('status'))
        attendance_data = {item['status']: item['count'] for item in attendance_summary}
        attendance_total = attendance_records.count()
        attendance_present = attendance_data.get('present', 0)
        attendance_absent = attendance_data.get('absent', 0)
        attendance_leave = attendance_data.get('leave', 0)

        # Aggregate assignment submissions
        assignments = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course_offering__in=course_offerings
        ).values('assignment__title', 'assignment__course_offering__course__code', 'assignment__course_offering__course__name').annotate(
            score=Sum('marks_obtained'),
            max_score=Max('assignment__max_points')
        ).order_by('assignment__course_offering__course__code', 'assignment__title')

        # Aggregate quiz submissions
        quizzes = QuizSubmission.objects.filter(
            student=student,
            quiz__course_offering__in=course_offerings,
            quiz__publish_flag=True
        ).values('quiz__title', 'quiz__course_offering__course__code', 'quiz__course_offering__course__name').annotate(
            score=Max('score'),
            max_score=Subquery(
                Question.objects.filter(quiz=OuterRef('quiz')).values('quiz').annotate(
                    total=Sum('marks')
                ).values('total')[:1]
            )
        ).order_by('quiz__course_offering__course__code', 'quiz__title')

        stats_by_semester.append({
            'semester': semester,
            'attendance_total': attendance_total,
            'attendance_present': attendance_present,
            'attendance_absent': attendance_absent,
            'attendance_leave': attendance_leave,
            'attendance_percentage': (attendance_present / attendance_total * 100) if attendance_total > 0 else 0,
            'assignments': assignments,
            'quizzes': quizzes,
            'exam_results': exam_stats,
            'semester_gpa': semester_gpa,
            'total_credit_hours': total_credit_hours,
            'total_quality_points': total_quality_points,
        })

    # Pagination (1 semester per page)
    paginator = Paginator(stats_by_semester, 1)
    page = request.GET.get('page')
    try:
        stats_by_page = paginator.page(page)
    except PageNotAnInteger:
        stats_by_page = paginator.page(1)
    except EmptyPage:
        stats_by_page = paginator.page(paginator.num_pages)

    context = {
        'student': student,
        'stats_by_semester': stats_by_page,
    }
    logger.info(f"Fetched semester performance data for student {student.applicant.full_name}")
    return render(request, 'faculty_staff/student_semester_performance.html', context)    
    
    
    
    
@hod_or_professor_required
def settings(request):
    print(f'status values -- {TeacherDetails.STATUS_CHOICES}')
    teacher_profile = request.user.teacher_profile
    teacher_details = teacher_profile.details if hasattr(teacher_profile, 'details') else None
    print(f'Teacher profile: {teacher_profile.contact_no}, Details: {teacher_details}')
    user_form = UserUpdateForm(instance=request.user)
    teacher_form = TeacherUpdateForm(instance=teacher_profile)
    password_form = PasswordChangeForm(request.user)
    status_form = TeacherStatusForm(instance=teacher_details) if teacher_details else TeacherStatusForm()
    contact = teacher_profile.contact_no
    print(f'this is contact -- {contact}')
    return render(request, 'faculty_staff/settings.html', {
        'active_tab': request.GET.get('tab', 'account'),
        'user_form': user_form,
        'teacher_form': teacher_form,
        'password_form': password_form,
        'status_form': status_form,
        'contact_no': contact,
        'status': TeacherDetails.STATUS_CHOICES,
        'form_errors': {
            'first_name': user_form.errors.get('first_name'),
            'last_name': user_form.errors.get('last_name'),
            'email': user_form.errors.get('email'),
            'profile_picture': user_form.errors.get('profile_picture'),
            'info': user_form.errors.get('info'),
            'contact_no': teacher_form.errors.get('contact_no'),
            'qualification': teacher_form.errors.get('qualification'),
            'hire_date': teacher_form.errors.get('hire_date'),
            'status': status_form.errors.get('status') if teacher_details else None,
        }
    })

@hod_or_professor_required
def update_account(request):
    if request.method == 'POST':
        teacher_profile = request.user.teacher_profile
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        teacher_form = TeacherUpdateForm(request.POST, instance=teacher_profile)
        if user_form.is_valid() and teacher_form.is_valid():
            user_form.save()
            teacher_form.save()
            messages.success(request, 'Account updated successfully.')
            return redirect('faculty_staff:settings')
        else:
            messages.error(request, 'Error updating account. Please check the form.')
    return redirect('faculty_staff:settings')

@hod_or_professor_required
def change_password(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('faculty_staff:settings')
        else:
            messages.error(request, 'Error changing password. Please check the form.')
    return redirect('faculty_staff:settings')

@hod_or_professor_required
def update_status(request):
    if request.method == 'POST':
        teacher_profile = request.user.teacher_profile
        teacher_details = teacher_profile.details if hasattr(teacher_profile, 'details') else None
        if teacher_details:
            status_form = TeacherStatusForm(request.POST, instance=teacher_details)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Status updated successfully.')
                return redirect('faculty_staff:settings')
            else:
                messages.error(request, 'Error updating status. Please check the form.')
        else:
            messages.error(request, 'Teacher details not found.')
    return redirect('faculty_staff:settings')




@hod_or_professor_required
def create_quiz(request, course_offering_id):
    course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
    quizzes = Quiz.objects.filter(course_offering=course_offering)

    if request.method == 'POST':
        logger.debug("Received POST request: %s", request.POST)

        quiz_id = request.POST.get('quiz_id')
        title = request.POST.get('title')
        publish_flag = request.POST.get('publish_flag') == 'on'
        timer_seconds = int(request.POST.get('timer_seconds', 30))

        # Validate title
        if not title:
            logger.error("Validation failed: Quiz title is required.")
            return JsonResponse({'success': False, 'message': 'Quiz title is required.', 'errors': {'title': 'This field is required.'}})

        # Create or update quiz
        if quiz_id:
            quiz = get_object_or_404(Quiz, id=quiz_id, course_offering=course_offering)
            quiz.title = title
            quiz.publish_flag = publish_flag
            quiz.timer_seconds = timer_seconds
            quiz.questions.all().delete()  # Clear existing questions
            logger.info("Editing quiz ID %s: %s", quiz_id, title)
        else:
            quiz = Quiz.objects.create(
                course_offering=course_offering,
                title=title,
                publish_flag=publish_flag,
                timer_seconds=timer_seconds
            )
            logger.info("Created new quiz: %s", title)

        # Process questions
        question_indices = [key.split('[')[1].split(']')[0] for key in request.POST if key.startswith('questions[') and '[text]' in key]
        question_indices = sorted(set(question_indices), key=int)

        if not question_indices:
            logger.error("Validation failed: At least one question is required.")
            return JsonResponse({
                'success': False,
                'message': 'At least one question is required.',
                'errors': {'questions': 'At least one question is required.'}
            })

        for i in question_indices:
            text = request.POST.get(f'questions[{i}][text]')
            marks = request.POST.get(f'questions[{i}][marks]', '1')

            if not text:
                logger.error("Validation failed: Question %s text is missing.", i)
                return JsonResponse({
                    'success': False,
                    'message': 'All questions must have text.',
                    'errors': {f'questions[{i}][text]': 'This field is required.'}
                })

            try:
                marks = int(marks)
                if marks < 1:
                    raise ValueError
            except ValueError:
                logger.error("Validation failed: Invalid marks for question %s: %s", i, marks)
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid marks value.',
                    'errors': {f'questions[{i}][marks]': 'Marks must be a positive integer.'}
                })

            question = Question.objects.create(quiz=quiz, text=text, marks=marks)
            logger.debug("Created question %s for quiz %s", text, quiz.id)

            # Process options
            option_indices = [key.split('[')[3].split(']')[0] for key in request.POST if key.startswith(f'questions[{i}][options][') and '[text]' in key]
            option_indices = sorted(set(option_indices), key=int)

            if not option_indices:
                question.delete()
                logger.error("Validation failed: Question %s has no options.", i)
                return JsonResponse({
                    'success': False,
                    'message': 'Each question must have at least one option.',
                    'errors': {f'questions[{i}][options]': 'At least one option is required.'}
                })

            has_correct_option = False
            for j in option_indices:
                option_text = request.POST.get(f'questions[{i}][options][{j}][text]')
                is_correct = request.POST.get(f'questions[{i}][options][{j}][is_correct]') == 'on'

                if not option_text:
                    question.delete()
                    logger.error("Validation failed: Option %s for question %s is missing text.", j, i)
                    return JsonResponse({
                        'success': False,
                        'message': 'All options must have text.',
                        'errors': {f'questions[{i}][options][${j}][text]': 'This field is required.'}
                    })

                Option.objects.create(question=question, text=option_text, is_correct=is_correct)
                logger.debug("Created option %s for question %s", option_text, question.id)
                if is_correct:
                    has_correct_option = True

            if not has_correct_option:
                question.delete()
                logger.error("Validation failed: Question %s has no correct option.", i)
                return JsonResponse({
                    'success': False,
                    'message': 'Each question must have at least one correct option.',
                    'errors': {f'questions[{i}][options]': 'At least one option must be marked as correct.'}
                })

        if 'publish' in request.POST:
            quiz.publish_flag = True
            quiz.save()
            logger.info("Published quiz %s", quiz.id)
            
            # Send email notifications to CR and GR
            try:
                # Get all students enrolled in the course offering
                enrolled_students = Student.objects.filter(
                    courses_enrolled__course_offering=course_offering,
                    courses_enrolled__status='enrolled'
                ).distinct()
                
                # Find class representatives (CR) and girls' representatives (GR)
                crs = enrolled_students.filter(role='CR')
                grs = enrolled_students.filter(role='GR')
                
                # Combine and deduplicate recipients
                recipients = list(crs) + list(grs)
                
                if recipients:
                    # Prepare email content
                    subject = f'New Quiz Published: {quiz.title} - {course_offering.course.code}'
                    
                    # Get the course name and teacher name
                    course_name = course_offering.course.name
                    teacher_name = course_offering.teacher.user.get_full_name() or 'Your teacher'
                    
                    # Get the number of questions and total marks
                    question_count = quiz.questions.count()
                    total_marks = quiz.questions.aggregate(total=Sum('marks'))['total'] or 0
                    
                    # Render the email template
                    message = render_to_string('emails/new_quiz_notification.html', {
                        'quiz': quiz,
                        'course_offering': course_offering,
                        'teacher_name': teacher_name,
                        'question_count': question_count,
                        'total_marks': total_marks,
                        'timer_minutes': quiz.timer_seconds // 60,
                    })
                    
                    # Send email to each recipient
                    for recipient in recipients:
                        if getattr(recipient, 'user', None) and recipient.user.email:
                            send_mail(
                                subject=subject,
                                message='',  # Empty message since we're using html_message
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[recipient.user.email],
                                html_message=message,
                                fail_silently=True
                            )
                            logger.info(f"Sent quiz notification email to {recipient.user.email}")
                
            except Exception as e:
                logger.error(f"Error sending quiz notification emails: {str(e)}")
                # Don't fail the request if email sending fails
                pass

        logger.info("Quiz %s saved successfully.", quiz.id)
        return JsonResponse({'success': True, 'message': 'Quiz saved successfully.'})

    context = {
        'course_offering': course_offering,
        'quizzes': quizzes,
        'today_date': timezone.now()
    }
    return render(request, 'faculty_staff/create_quiz.html', context)

@hod_or_professor_required
def get_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = [
        {
            'text': question.text,
            'marks': question.marks,
            'options': [
                {'text': option.text, 'is_correct': option.is_correct}
                for option in question.options.all()
            ]
        }
        for question in quiz.questions.all()
    ]

    # Validate quiz data
    for i, question in enumerate(questions):
        if not question['options']:
            logger.error("Invalid quiz %s: Question %s has no options.", quiz_id, i)
            return JsonResponse({
                'success': False,
                'message': 'Each question must have at least one option.',
                'errors': {f'questions[{i}][options]': 'At least one option is required.'}
            })
        if not any(option['is_correct'] for option in question['options']):
            logger.error("Invalid quiz %s: Question %s has no correct option.", quiz_id, i)
            return JsonResponse({
                'success': False,
                'message': 'Each question must have at least one correct option.',
                'errors': {f'questions[{i}][options]': 'At least one option must be marked as correct.'}
            })

    logger.info("Fetched quiz %s successfully.", quiz_id)
    return JsonResponse({
        'id': quiz.id,
        'title': quiz.title,
        'publish_flag': quiz.publish_flag,
        'timer_seconds': quiz.timer_seconds,
        'questions': questions
    })
    
@hod_required
@require_POST
def set_student_role(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    role = request.POST.get('role')
    if role not in ['CR', 'GR', '']:
        role = None
    student.role = role if role else None
    student.save()
    messages.success(request, 'Student role updated successfully.')
    return redirect('faculty_staff:student_detail', student_id=student.pk)
    
    
    
    
    
    
# In faculty_staff/views.py

@login_required
def department_funds_management(request):
    if request.user.teacher_profile.designation != 'head_of_department':
        return redirect('faculty_staff:hod_dashboard')

    hod = request.user.teacher_profile
    active_funds = DepartmentFund.objects.filter(hod=hod, is_active=True)
    inactive_funds = DepartmentFund.objects.filter(hod=hod, is_active=False)
    
    # Get all academic sessions, programs, semesters, and fund types for the HOD's department
    academic_sessions = AcademicSession.objects.all()
    programs = Program.objects.filter(department=hod.department)
    semesters = Semester.objects.filter(program__in=programs)
    fund_types = DepartmentFund.objects.filter(hod=hod).values_list('fundtype', flat=True).distinct()

    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'fund':
            return handle_fund_form(request, hod)
        elif form_type == 'delete_fund':
            return handle_delete_fund(request)

    # Handle student submissions filtering
    enrollments = StudentSemesterEnrollment.objects.none()  # Start with empty queryset
    if any(request.GET.get(param) for param in ['academic_session', 'program', 'semester', 'fundtype']):
        enrollments = StudentSemesterEnrollment.objects.filter(
            student__program__department=hod.department,
        )
        
        # Apply filters if they exist  
        if request.GET.get('academic_session'):
            enrollments = enrollments.filter(semester__session_id=request.GET.get('academic_session'))
        if request.GET.get('program'):
            enrollments = enrollments.filter(student__program_id=request.GET.get('program'))
        if request.GET.get('semester'):
            enrollments = enrollments.filter(semester_id=request.GET.get('semester'))
      
    
        # Apply fund type filter if it exists
        fundtype = request.GET.get('fundtype')
        if fundtype:
            # Get enrollments that match the fund's programs and semesters
            fund_filters = {
                'fundtype': fundtype,
                'hod': hod,
                'is_active': True
            }
            
            # If we have program/semester filters, apply them to the fund query
            if request.GET.get('program'):
                fund_filters['programs__id'] = request.GET.get('program')
            if request.GET.get('semester'):
                fund_filters['semesters__id'] = request.GET.get('semester')
            
            # Get matching funds
            funds = DepartmentFund.objects.filter(**fund_filters).distinct()
            
            if funds.exists():
                # Get programs and semesters from matching funds
                program_ids = funds.values_list('programs__id', flat=True).distinct()
                semester_ids = funds.values_list('semesters__id', flat=True).distinct()
                
                # Filter enrollments by these programs and semesters
                enrollments = enrollments.filter(
                    student__program_id__in=program_ids,
                    semester_id__in=semester_ids
                )

    # Handle edit fund
    fund = None
    if 'edit' in request.GET:
        fund_id = request.GET.get('edit')
        fund = get_object_or_404(DepartmentFund, id=fund_id, hod=hod)

    context = {
        'hod': hod,
        'active_funds': active_funds,
        'inactive_funds': inactive_funds,
        'academic_sessions': academic_sessions,
        'programs': programs,
        'semesters': semesters,
        'fund_types': fund_types,  # List of distinct fund types
        'enrollments': enrollments,
        'fund': fund,
    }
    return render(request, 'faculty_staff/department_fund_management.html', context)

def handle_fund_form(request, hod):
    fund_id = request.POST.get('fund_id')
    department = request.POST.get('department')
    academic_sessions = request.POST.getlist('academic_sessions')
    programs = request.POST.getlist('programs')
    semesters = request.POST.getlist('semesters')
    amount = request.POST.get('amount')
    fundtype = request.POST.get('fundtype')
    description = request.POST.get('description')
    due_date = request.POST.get('due_date')
    is_active = request.POST.get('is_active') == 'on'

    if not all([department, amount, fundtype, description, due_date]):
        messages.error(request, 'All fields are required')
        return redirect('faculty_staff:department_funds_management')

    try:
        if fund_id:  # Edit existing fund
            fund = get_object_or_404(DepartmentFund, id=fund_id, hod=hod)
            fund.department_id = department
            fund.amount = amount
            fund.fundtype = fundtype
            fund.description = description
            fund.due_date = due_date
            fund.is_active = is_active
            fund.save()
            messages.success(request, 'Department fund updated successfully')
        else:  # Create new fund
            fund = DepartmentFund.objects.create(
                hod=hod,
                department_id=department,
                amount=amount,
                fundtype=fundtype,
                description=description,
                due_date=due_date,
                is_active=is_active
            )
            messages.success(request, 'Department fund created successfully')
            
            # Get all students in the selected programs and semesters
            from students.models import Student, StudentSemesterEnrollment, StudentFundPayment
            
            # Get active enrollments that match the fund's programs and semesters
            enrollments = StudentSemesterEnrollment.objects.filter(
                student__program__in=programs,
                semester__in=semesters,
                status='enrolled'
            ).select_related('student')
            
            # Create pending payment records for each student
            created_count = 0
            for enrollment in enrollments.distinct('student'):
                # Create or update payment record
                _, created = StudentFundPayment.objects.get_or_create(
                    student=enrollment.student,
                    fund=fund,
                    defaults={
                        'status': 'pending',
                        'amount_paid': 0,
                        'notes': 'Auto-created pending payment'
                    }
                )
                if created:
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Created pending payment records for {created_count} students')

        fund.academic_sessions.set(academic_sessions)
        fund.programs.set(programs)
        fund.semesters.set(semesters)
        return redirect('faculty_staff:department_funds_management')

    except Exception as e:
        messages.error(request, f'Error processing fund: {str(e)}')
        return redirect('faculty_staff:department_funds_management')

def handle_delete_fund(request):
    fund_id = request.POST.get('fund_id')
    fund = get_object_or_404(DepartmentFund, id=fund_id, hod=request.user.teacher_profile)
    try:
        fund.delete()
        messages.success(request, 'Department fund deleted successfully')
    except Exception as e:
        messages.error(request, f'Error deleting fund: {str(e)}')
    return redirect('faculty_staff:department_funds_management')

@login_required
def view_department_fund(request, fund_id):
    if request.user.teacher_profile.designation != 'head_of_department':
        return redirect('faculty_staff:hod_dashboard')

    fund = get_object_or_404(DepartmentFund, id=fund_id, hod=request.user.teacher_profile)
    enrollments = StudentSemesterEnrollment.objects.filter(
        semester__in=fund.semesters.all(),
        semester__session__in=fund.academic_sessions.all(),
        student__program__in=fund.programs.all(),
        status='enrolled'
    )
    students = Student.objects.filter(
        semester_enrollments__in=enrollments
    ).distinct()

    return render(request, 'faculty_staff/fund_details.html', {
        'fund': fund,
        'students': students
    })

@login_required
def get_programs_fund(request):
    if request.method == 'POST':
        hod = request.user.teacher_profile
        programs = Program.objects.filter(department=hod.department).values('id', 'name')
        preselected_programs = []
        if 'edit' in request.GET:
            fund_id = request.GET.get('edit')
            fund = get_object_or_404(DepartmentFund, id=fund_id, hod=hod)
            preselected_programs = list(fund.programs.values_list('id', flat=True))
        return JsonResponse({
            'programs': list(programs),
            'preselected_programs': preselected_programs
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_semesters_fund(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            program_ids = data.get('programs', [])
            session_ids = data.get('academic_sessions', [])
            semesters = Semester.objects.filter(
                program__id__in=program_ids,
                session__id__in=session_ids
            ).values('id', 'name', 'program__name')
            semesters = [{'id': s['id'], 'name': s['name'], 'program_name': s['program__name']} for s in semesters]
            preselected_semesters = []
            if 'edit' in request.GET:
                fund_id = request.GET.get('edit')
                fund = get_object_or_404(DepartmentFund, id=fund_id, hod=request.user.teacher_profile)
                preselected_semesters = list(fund.semesters.values_list('id', flat=True))
            return JsonResponse({
                'semesters': semesters,
                'preselected_semesters': preselected_semesters
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Error in get_semesters_fund: {str(e)}")
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

# Assuming @hod_required is a custom decorator defined elsewhere
from .decorators import hod_required

@hod_required
@hod_required
def exam_datesheet(request):
    academic_sessions = AcademicSession.objects.filter(is_active=True)
    
    if request.method == 'POST':
        try:
            total_courses = int(request.POST.get('total_courses', 0))
            saved_count = 0
            for i in range(total_courses):
                course_offering_id = request.POST.get(f'course_offering_{i}')
                exam_date = request.POST.get(f'exam_date_{i}')
                start_time = request.POST.get(f'start_time_{i}')
                end_time = request.POST.get(f'end_time_{i}')
                exam_center = request.POST.get(f'exam_center_{i}', '')
                academic_session_id = request.POST.get(f'academic_session_{i}')
                program_id = request.POST.get(f'program_{i}')
                semester_id = request.POST.get(f'semester_{i}')
                exam_type = request.POST.get(f'exam_type_{i}')
                
                if not all([course_offering_id, exam_date, start_time, end_time, 
                           academic_session_id, program_id, semester_id, exam_type]):
                    print(f"[WARNING] Skipping incomplete form data for index {i}")
                    continue
                
                try:
                    exam_schedule, created = ExamDateSheet.objects.update_or_create(
                        course_offering_id=course_offering_id,
                        academic_session_id=academic_session_id,
                        program_id=program_id,
                        semester_id=semester_id,
                        exam_type=exam_type,
                        defaults={
                            'exam_date': exam_date,
                            'start_time': start_time,
                            'end_time': end_time,
                            'exam_center': exam_center
                        }
                    )
                    saved_count += 1
                    print(f"[INFO] {'Created' if created else 'Updated'} exam schedule for course {course_offering_id}")
                except Exception as e:
                    print(f"[ERROR] Error saving exam schedule for course {course_offering_id}: {str(e)}")
                    messages.error(request, f"Error saving schedule for course {course_offering_id}: {str(e)}")
            
            if saved_count > 0:
                messages.success(request, f'Successfully saved exam schedule for {saved_count} course(s).')
            else:
                messages.warning(request, 'No exam schedules were saved. Please check your input.')
            return redirect('faculty_staff:exam_datesheet')
        except Exception as e:
            print(f"[ERROR] Error in exam_datesheet view: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred while processing the form: {str(e)}")
            return redirect('faculty_staff:exam_datesheet')
    
    context = {'academic_sessions': academic_sessions, 'title': 'Exam Datesheet Management'}
    return render(request, 'faculty_staff/exam_datesheet.html', context)

@hod_required
def get_programs_exam_ds(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'programs': []})
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        return JsonResponse({'programs': [], 'error': 'No teacher profile found'}, status=403)
    programs = Program.objects.filter(
        department=teacher.department,
        course_offerings__academic_session_id=session_id,
        is_active=True
    ).distinct().values('id', 'name')
    return JsonResponse({'programs': list(programs)})

@hod_required
def get_semesters_exam_ds(request):
    session_id = request.GET.get('session_id')
    program_id = request.GET.get('program_id')
    if not (session_id and program_id):
        return JsonResponse({'semesters': []})
    semesters = Semester.objects.filter(
        session_id=session_id,
        program_id=program_id,
        is_active=True
    ).distinct().values('id', 'name')
    return JsonResponse({'semesters': list(semesters)})

@hod_required
def get_courses_exam_ds(request):
    try:
        print(f"[DEBUG] get_courses_exam_ds called at {datetime.datetime.now()} with params: {request.GET}")
        
        session_id = request.GET.get('session_id')
        program_id = request.GET.get('program_id')
        semester_id = request.GET.get('semester_id')
        exam_type = request.GET.get('exam_type', '').lower()
        
        if not all([session_id, program_id, semester_id]):
            print("[ERROR] Missing required parameters")
            return JsonResponse({'error': 'Missing required parameters', 'courses': []}, status=400)
            
        try:
            session_id = int(session_id)
            program_id = int(program_id)
            semester_id = int(semester_id)
        except (ValueError, TypeError) as e:
            print(f"[ERROR] Invalid parameter format: {e}")
            return JsonResponse({'error': 'Invalid parameter format', 'courses': []}, status=400)
        
        print(f"[DEBUG] Querying courses for session_id={session_id}, program_id={program_id}, semester_id={semester_id}, exam_type={exam_type}")
        
        courses_query = CourseOffering.objects.filter(
            academic_session_id=session_id,
            program_id=program_id,
            semester_id=semester_id,
            is_active=True
        ).select_related('course').values('id', 'course__code', 'course__name', 'course__lab_work')
        
        if exam_type == 'practical':
            print("[DEBUG] Filtering for practical courses (course__lab_work > 0)")
            courses_query = courses_query.filter(course__lab_work__gt=0)
            print(f"[DEBUG] After filter, query: {courses_query.query}")
        
        courses_list = list(courses_query)
        print(f"[DEBUG] Found {len(courses_list)} courses: {courses_list}")
        
        return JsonResponse({
            'success': True,
            'courses': courses_list
        })
    except Exception as e:
        print(f"[ERROR] Error in get_courses_exam_ds: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching courses',
            'courses': []
        }, status=500)

@hod_required
def view_exam_schedules(request):
    """
    View to fetch exam schedules based on session and program filters.
    """
    try:
        session_id = request.GET.get('session_id')
        program_id = request.GET.get('program_id')
        
        if not all([session_id, program_id]):
            return JsonResponse({
                'success': False,
                'error': 'Both session_id and program_id are required',
                'schedules': []
            }, status=400)
        
        # Get the teacher's department
        teacher = getattr(request.user, 'teacher_profile', None)
        if not teacher or not hasattr(teacher, 'department'):
            return JsonResponse({
                'success': False,
                'error': 'Teacher profile or department not found',
                'schedules': []
            }, status=403)
        
        # Query exam schedules
        schedules = ExamDateSheet.objects.filter(
            academic_session_id=session_id,
            program_id=program_id,
            program__department=teacher.department
        ).select_related(
            'course_offering__course',
            'academic_session',
            'program',
            'semester'
        ).order_by('exam_type', 'exam_date', 'start_time')
        
        # Prepare the response data
        schedules_data = []
        for schedule in schedules:
            schedules_data.append({
                'id': schedule.id,
                'course_code': schedule.course_offering.course.code if schedule.course_offering and schedule.course_offering.course else 'N/A',
                'course_name': schedule.course_offering.course.name if schedule.course_offering and schedule.course_offering.course else 'N/A',
                'semester_name': schedule.semester.name if schedule.semester else 'N/A',
                'exam_type': schedule.exam_type,
                'exam_date': schedule.exam_date.strftime('%Y-%m-%d') if schedule.exam_date else None,
                'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else None,
                'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else None,
                'exam_center': schedule.exam_center
            })
        
        return JsonResponse({
            'success': True,
            'schedules': schedules_data
        })
        
    except Exception as e:
        logger.error(f"Error in view_exam_schedules: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'schedules': []
        }, status=500)