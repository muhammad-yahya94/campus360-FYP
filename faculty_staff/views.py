# Standard library imports
import os

# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login, logout
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
from faculty_staff.models import Teacher
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
import datetime
# Custom user model

from datetime import time
CustomUser = get_user_model()


def login_view(request):
    # if request.user.is_authenticated:
    #     return redirect('faculty_staff:hod_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if hasattr(user, 'teacher_profile'):
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('faculty_staff:hod_dashboard')
            else:
                messages.error(request, 'You do not have faculty staff access.')   
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'faculty_staff/login.html')


@login_required
def hod_dashboard(request):
    # if not request.user.is_staff:
    #     messages.error(request, 'You do not have permission to access this page.')
    #     return redirect('home')

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


@login_required
def staff_management(request):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to access this page.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    staff_list = Teacher.objects.filter(department=hod_department)

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


    context = {
        'staff_members': staff_members,
        'department': hod_department,
        'designation_choices': Teacher.DESIGNATION_CHOICES,
    }
    return render(request, 'faculty_staff/staff_management.html', context)


@login_required
def add_staff(request):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to perform this action.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation = request.POST.get('designation')   
        contact_no = request.POST.get('contact_no', '')
        qualification = request.POST.get('qualification', '')
        hire_date = request.POST.get('hire_date', None)
        is_active = request.POST.get('is_active') == 'on'
        linkedin_url = request.POST.get('linkedin_url', '')
        twitter_url = request.POST.get('twitter_url', '')
        personal_website = request.POST.get('personal_website', '')
        experience = request.POST.get('experience', '')

        if not all([first_name, last_name, email, designation]):
            messages.error(request, 'Please fill in all required fields (First Name, Last Name, Email, Designation).')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {
                    'first_name': not first_name,
                    'last_name': not last_name,
                    'email': not email,
                    'designation': not designation,
                },
            })

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'designation': True},
            })

        try:
            user = CustomUser.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=True
            )
            user.set_password('defaultpassword123')
            user.save()

            teacher = Teacher.objects.create(
                user=user,
                department=hod_department,
                designation=designation,
                contact_no=contact_no,
                qualification=qualification,
                hire_date=hire_date if hire_date else None,
                is_active=is_active,
                linkedin_url=linkedin_url,
                twitter_url=twitter_url,
                personal_website=personal_website,
                experience=experience
            )

            messages.success(request, f'Teacher {user.get_full_name()} has been added successfully.')
            return redirect('faculty_staff:staff_management')

        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {},
            })

    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
    })


@login_required
def edit_staff(request, staff_id):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to perform this action.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=staff_id, department=hod_department)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        designation = request.POST.get('designation')
        contact_no = request.POST.get('contact_no', '')
        qualification = request.POST.get('qualification', '')
        hire_date = request.POST.get('hire_date', None)
        is_active = request.POST.get('is_active') == 'on'
        linkedin_url = request.POST.get('linkedin_url', '')
        twitter_url = request.POST.get('twitter_url', '')
        personal_website = request.POST.get('personal_website', '')
        experience = request.POST.get('experience', '')

        if not all([first_name, last_name, email, designation]):
            messages.error(request, 'Please fill in all required fields (First Name, Last Name, Email, Designation).')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {
                    'first_name': not first_name,
                    'last_name': not last_name,
                    'email': not email,
                    'designation': not designation,
                },
            })

        if CustomUser.objects.filter(email=email).exclude(id=teacher.user.id).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'designation': True},
            })

        try:
            teacher.user.first_name = first_name
            teacher.user.last_name = last_name
            teacher.user.email = email
            teacher.user.save()

            teacher.designation = designation
            teacher.contact_no = contact_no
            teacher.qualification = qualification
            teacher.hire_date = hire_date if hire_date else None
            teacher.is_active = is_active
            teacher.linkedin_url = linkedin_url
            teacher.twitter_url = twitter_url
            teacher.personal_website = personal_website
            teacher.experience = experience
            teacher.save()

            messages.success(request, f'Teacher {teacher.user.get_full_name()} has been updated successfully.')
            return redirect('faculty_staff:staff_management')

        except Exception as e:  
            messages.error(request, f'Error updating teacher: {str(e)}')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {},
            })


    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
    })


@login_required
def delete_staff(request, staff_id):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to perform this action.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=staff_id, department=hod_department)

    if request.method == 'POST':
        teacher_name = teacher.user.get_full_name()
        teacher.delete()
        messages.success(request, f'Teacher {teacher_name} has been deleted successfully.')
        return redirect('faculty_staff:staff_management')

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,
    })


@login_required
def session_students(request, session_id):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to access this page.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    session = get_object_or_404(AcademicSession, id=session_id)
    programs = Program.objects.filter(department=hod_department)
    applicants = Applicant.objects.filter(program__in=programs)
    students = Student.objects.filter(
        applicant__in=applicants,
        program__in=programs,
        enrollment_date__year=session.start_year
    ).select_related('applicant', 'program', 'current_semester')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        students = students.filter(
            Q(university_roll_no__icontains=search_query) |
            Q(applicant__full_name__icontains=search_query) |
            Q(college_roll_no__icontains=search_query)
        )

    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_students = paginator.get_page(page_number)

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'session': session,
        'students': page_students,
        'department': hod_department,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'faculty_staff/session_students.html', context)


# Course Form Definition
class CourseForm(forms.Form):
    code = forms.CharField(max_length=10, required=True, help_text="Enter the unique course code (e.g., CS101).")
    name = forms.CharField(max_length=200, required=True, help_text="Enter the full name of the course.")
    credits = forms.IntegerField(min_value=1, required=True, help_text="Enter the number of credit hours.")
    is_active = forms.BooleanField(required=False, initial=True, help_text="Check this if the course is active.")
    description = forms.CharField(widget=forms.Textarea, required=False, help_text="Provide a description.")


@login_required
def add_course(request):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to access this page.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    form = CourseForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        if Course.objects.filter(code=code).exists():
            form.add_error('code', 'This course code already exists.')
        else:
            Course.objects.create(
                code=code,
                name=form.cleaned_data['name'],
                credits=form.cleaned_data['credits'],
                is_active=form.cleaned_data['is_active'],
                description=form.cleaned_data['description']
            )
            messages.success(request, f'Course {code} added successfully.')
            return redirect('faculty_staff:course_offerings')

    context = {
        'form': form,
        'department': hod_department,
        'session_id': None,
    }
    return render(request, 'faculty_staff/add_course.html', context)


@login_required
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

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    programs = Program.objects.filter(department=hod_department)
    teachers = Teacher.objects.filter(is_active=True, department=hod_department)
    semesters = Semester.objects.filter(program__in=programs).distinct()
    course_offerings = CourseOffering.objects.filter(
        department=hod_department
    ).select_related('course', 'teacher', 'program', 'department', 'academic_session', 'semester')
    timetable_slots = TimetableSlot.objects.filter(
        course_offering__department=hod_department
    ).select_related('course_offering__course', 'course_offering__teacher', 'course_offering__program', 'course_offering__semester', 'venue')

    context = {
        'academic_sessions': academic_sessions,
        'semesters': semesters,
        'programs': programs,
        'teachers': teachers,
        'course_offerings': course_offerings,
        'timetable_slots': timetable_slots,
        'department': hod_department,
        'session_id': None,
    }
    return render(request, 'faculty_staff/course_offerings.html', context)

@login_required
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

@login_required
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

@login_required
def search_teachers(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        teachers = Teacher.objects.filter(
            Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query),
            is_active=True,
            department=request.user.teacher_profile.department
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

@login_required
def get_academic_sessions(request):
    sessions = AcademicSession.objects.all()
    results = [{'id': session.id, 'text': session.name} for session in sessions]
    return JsonResponse({'results': results})

@login_required
def search_programs(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        academic_session_id = request.GET.get('academic_session_id', '')
        page = int(request.GET.get('page', 1))
        per_page = 10
        hod_department = request.user.teacher_profile.department
        if not hod_department:
            return JsonResponse({'results': [], 'pagination': {'more': False}})

        programs = Program.objects.filter(department=hod_department)

        if academic_session_id:
            try:
                academic_session = AcademicSession.objects.get(id=academic_session_id)
                filtered_programs = programs.filter(
                    course_offerings__academic_session=academic_session
                ).distinct()
                if filtered_programs.exists():
                    programs = filtered_programs
            except AcademicSession.DoesNotExist:
                return JsonResponse({
                    'results': [],
                    'pagination': {'more': False}
                })

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

@login_required
def search_semesters(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        program_id = request.GET.get('program_id')

        filters = Q(name__icontains=search_query) | Q(program__name__icontains=search_query)

        if program_id:
            filters &= Q(program_id=program_id)

        semesters = Semester.objects.filter(filters).values(
            'id', 'name', 'program__name'
        )[:10]

        return JsonResponse({
            'results': [
                {
                    'id': semester['id'],
                    'text': f"{semester['name']} ({semester['program__name']})"
                } for semester in semesters
            ],
            'more': False
        })
    return JsonResponse({'results': [], 'more': False})

@login_required
def get_offering_type_choices(request):
    choices = [{'id': value, 'text': label} for value, label in CourseOffering.OFFERING_TYPES]
    return JsonResponse({'results': choices})

@login_required
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
            {'id': venue.id, 'text': f"{venue.name} (Capacity: {venue.capacity})"}
            for venue in paginated_venues
        ]
        return JsonResponse({
            'results': results,
            'pagination': {'more': end < venues.count()}
        })
    return JsonResponse({'results': [], 'pagination': {'more': False}})

@login_required
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

    active_students = Student.objects.filter(
        program=program,
        current_semester=semester,
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
@login_required
def save_venue(request):
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method or insufficient permissions.'
        })

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
        
@login_required
@transaction.atomic
def save_timetable_slot(request):
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method or insufficient permissions.'
        })

    course_offering_id = request.POST.get('course_offering_id')
    if not course_offering_id:
        return JsonResponse({
            'success': False,
            'message': 'Course Offering ID is required.'
        })

    try:
        course_offering = CourseOffering.objects.get(id=course_offering_id, department=request.user.teacher_profile.department)
    except CourseOffering.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Selected course offering does not exist.'
        })

    shift = course_offering.shift

    def validate_and_convert_time(start_time_str, end_time_str, shift_type):
        if not start_time_str or not end_time_str:
            return False, None, None, f"{shift_type.capitalize()} start and end times are required."
        try:
            start_h, start_m = map(int, start_time_str.split(':'))
            end_h, end_m = map(int, end_time_str.split(':'))
            start_t = time(start_h, start_m)
            end_t = time(end_h, end_m)
            if start_t >= end_t:
                return False, None, None, f"{shift_type.capitalize()} end time must be after start time."
            return True, start_t, end_t, None
        except (ValueError, IndexError):
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
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                })

            morning_valid, morning_start_t, morning_end_t, morning_error = validate_and_convert_time(morning_start_time, morning_end_time, 'morning')
            evening_valid, evening_start_t, evening_end_t, evening_error = validate_and_convert_time(evening_start_time, evening_end_time, 'evening')
            if not morning_valid:
                return JsonResponse({'success': False, 'message': morning_error})
            if not evening_valid:
                return JsonResponse({'success': False, 'message': evening_error})

            morning_venue = Venue.objects.get(id=morning_venue_id, department=request.user.teacher_profile.department, is_active=True)
            evening_venue = Venue.objects.get(id=evening_venue_id, department=request.user.teacher_profile.department, is_active=True)

            saved_slots = []
            for day in morning_days:
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=morning_start_t,  # datetime.time object
                    end_time=morning_end_t,      # datetime.time object
                    venue=morning_venue
                )
                slot.clean()
                slot.save()
                saved_slots.append(f"{dict(TimetableSlot.DAYS_OF_WEEK)[day]} (Morning)")
            for day in evening_days:
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=evening_start_t,  # datetime.time object
                    end_time=evening_end_t,      # datetime.time object
                    venue=evening_venue
                )
                slot.clean()
                slot.save()
                saved_slots.append(f"{dict(TimetableSlot.DAYS_OF_WEEK)[day]} (Evening)")

            return JsonResponse({
                'success': True,
                'message': f'Timetable slots scheduled for {course_offering.course.code} on {", ".join(saved_slots)}.'
            })
        else:
            days = request.POST.getlist('day[]')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            venue_id = request.POST.get('venue_id')

            required_fields = {
                'day': days,
                'start_time': start_time,
                'end_time': end_time,
                'venue_id': venue_id
            }
            missing_fields = [field_name for field_name, field_label in required_fields.items() if not field_label]
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required fields: {", ".join([field_name for field_name in missing_fields])}'
                })

            venue = Venue.objects.get(id=venue_id, department=request.user.teacher_profile.department, is_active=True)

            valid_time, start_t, end_t, error_msg = validate_and_convert_time(start_time, end_time, shift)
            if not valid_time:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })

            saved_days = []
            for day in days:
                slot = TimetableSlot(
                    course_offering=course_offering,
                    day=day,
                    start_time=start_t,  # datetime.time object
                    end_time=end_t,      # datetime.time object
                    venue=venue
                )
                slot.clean()
                slot.save()
                saved_days.append(dict(TimetableSlot.DAYS_OF_WEEK)[day])

            return JsonResponse({
                'success': True,
                'message': f'Timetable slot(s) scheduled for {course_offering.course.code} on {", ".join(saved_days)}.'
            })
    except (Venue.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'success': False,
            'message': f'Error scheduling timetable: {str(e)}'
        })
        
        
        
@login_required
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

@login_required
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

@login_required
@require_POST
def edit_timetable_slot(request):
    slot_id = request.POST.get('slot_id')
    try:
        slot = TimetableSlot.objects.get(id=slot_id)
        slot.day = request.POST.get('day')
        slot.start_time = request.POST.get('start_time')
        slot.end_time = request.POST.get('end_time')
        slot.venue = get_object_or_404(Venue, id=request.POST.get('venue_id'))
        slot.save()
        return JsonResponse({'success': True, 'message': 'Timetable slot updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
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


@login_required
def weekly_timetable(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/error.html', {
            'message': 'You do not have permission to view the weekly timetable.'
        }, status=403)

    department = request.user.teacher_profile.department
    try:
        current_session = AcademicSession.objects.get(is_active=True)
    except AcademicSession.DoesNotExist:
        return render(request, 'faculty_staff/error.html', {
            'message': 'No active academic session found.'
        }, status=404)

    # Get shift filter from GET parameter (default: all)
    shift_filter = request.GET.get('shift', 'all').lower()
    valid_shifts = ['morning', 'evening', 'both', 'all']
    if shift_filter not in valid_shifts:
        shift_filter = 'all'

    # Fetch timetable slots
    queryset = TimetableSlot.objects.filter(
        course_offering__department=department,
        course_offering__academic_session=current_session
    ).select_related('course_offering__course', 'course_offering__teacher', 'course_offering__program', 'venue')

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

    # Organize slots by day
    timetable_data = []
    days_of_week = TimetableSlot.DAYS_OF_WEEK  # [('monday', 'Monday'), ...]
    for day_value, day_label in days_of_week:
        day_slots = sorted(
            [
                {
                    'course_code': slot.course_offering.course.code,
                    'venue': slot.venue.name,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'shift': (
                        slot.course_offering.shift.capitalize() if slot.course_offering.shift != 'both'
                        else ('Morning' if slot.start_time.hour < 12 else 'Evening')
                    ),
                    'teacher': f"{slot.course_offering.teacher.user.first_name} {slot.course_offering.teacher.user.last_name}",
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

    return render(request, 'faculty_staff/weekly_timetable.html', {
        'timetable_data': timetable_data,
        'department': department,
        'academic_session': current_session,
        'shift_filter': shift_filter,
        'shift_options': [('all', 'All'), ('morning', 'Morning'), ('evening', 'Evening'), ('both', 'Both')],
    })
    
    
    

@login_required
def my_timetable(request):
    if not hasattr(request.user, 'teacher_profile'):
        return render(request, 'faculty_staff/error.html', {
            'message': 'You do not have a teaching profile.'
        }, status=403)

    teacher = request.user.teacher_profile
    department = teacher.department
    try:
        current_session = AcademicSession.objects.get(is_active=True)
    except AcademicSession.DoesNotExist:
        return render(request, 'faculty_staff/error.html', {
            'message': 'No active academic session found.'
        }, status=404)

    # Get shift filter from GET parameter
    shift_filter = request.GET.get('shift', 'all').lower()
    valid_shifts = ['morning', 'evening', 'both', 'all']
    if shift_filter not in valid_shifts:
        shift_filter = 'all'

    # Fetch timetable slots for the teacher's courses
    queryset = TimetableSlot.objects.filter(
        course_offering__teacher=teacher,
        course_offering__department=department,
        course_offering__academic_session=current_session
    ).select_related('course_offering__course', 'course_offering__program', 'venue')

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

    # Organize slots by day
    timetable_data = []
    days_of_week = TimetableSlot.DAYS_OF_WEEK  # [('monday', 'Monday'), ...]
    for day_value, day_label in days_of_week:
        day_slots = sorted(
            [
                {
                    'course_code': slot.course_offering.course.code,
                    'venue': slot.venue.name,
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

    return render(request, 'faculty_staff/my_timetable.html', {
        'timetable_data': timetable_data,
        'department': department,
        'academic_session': current_session,
        'shift_filter': shift_filter,
        'shift_options': [('all', 'All'), ('morning', 'Morning'), ('evening', 'Evening'), ('both', 'Both')],
        'teacher': teacher,
    })
    
    
    
    

@login_required
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
                'program_name': offering.program.name,
                'semester_name': offering.semester.name,
                'session_name': offering.academic_session.name
            } for offering in paginated_offerings
        ],
        'pagination': {'more': end < course_offerings.count()}
    })


@login_required
def delete_course_offering(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        offering_id = request.POST.get('offering_id')
        if offering_id:
            offering = get_object_or_404(CourseOffering, id=offering_id)
            offering.delete()
            return JsonResponse({'success': True, 'message': 'Course offering deleted successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@login_required
def study_materials(request):
    course_offering_id = request.GET.get('course_offering_id')
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

@login_required
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
            
            return JsonResponse({
                'success': True,
                'message': 'Study materials created successfully.',
                'materials': created_materials
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
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

@login_required
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
            'program_name': o.program.name,
            'semester_name': o.semester.name,
            'session_name': o.academic_session.name
        } for o in offerings]
    
    return JsonResponse({
        'success': True,
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def assignments(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/assignments.html', {'error': 'Unauthorized access.'})
    
    course_offering_id = request.GET.get('course_offering_id')
    if course_offering_id:
        assignments = Assignment.objects.filter(
            course_offering_id=course_offering_id,
            course_offering__teacher=request.user.teacher_profile
        ).select_related('course_offering').order_by('-created_at')
        course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
    else:
        assignments = Assignment.objects.filter(
            course_offering__teacher=request.user.teacher_profile
        ).select_related('course_offering').order_by('-created_at')
        course_offering = None
    
    return render(request, 'faculty_staff/assignments.html', {
        'assignments': assignments,
        'course_offering': course_offering,
        'course_offering_id': course_offering_id
    })

@login_required
def create_assignment(request):
    if request.method == "POST" and hasattr(request.user, 'teacher_profile') and request.user.teacher_profile.designation == 'head_of_department':
        course_offering_id = request.POST.get('course_offering_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date')
        max_points = request.POST.get('max_points')
        resource_file = request.FILES.get('resource_file')

        if not all([course_offering_id, title, due_date, max_points]):
            return JsonResponse({'success': False, 'message': 'All required fields must be filled.'})

        try:
            max_points = int(max_points)
            if max_points < 1:
                return JsonResponse({'success': False, 'message': 'Max points must be at least 1.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid max points value.'})

        course_offering = get_object_or_404(
            CourseOffering,
            id=course_offering_id,
            teacher=request.user.teacher_profile
        )
        Assignment.objects.create(
            course_offering=course_offering,
            teacher=request.user.teacher_profile,
            title=title,
            description=description,
            due_date=due_date,
            max_points=max_points,
            resource_file=resource_file
        )
        return JsonResponse({'success': True, 'message': 'Assignment created successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request or unauthorized access.'})

@login_required
def delete_assignment(request):
    if request.method == "POST" and hasattr(request.user, 'teacher_profile') and request.user.teacher_profile.designation == 'head_of_department':
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
            return JsonResponse({'success': True, 'message': 'Assignment deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request or unauthorized access.'})


@login_required
def assignment_submissions(request, assignment_id):
    if request.user.teacher_profile.designation == 'head_of_department':
        assignment = get_object_or_404(
            Assignment,
            id=assignment_id,
            course_offering__teacher=request.user.teacher_profile
        )
        submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('-submitted_at')
        return render(request, 'faculty_staff/assignment_submissions.html', {'assignment': assignment, 'submissions': submissions})
    return JsonResponse({'success': False, 'message': 'Unauthorized access.'})


@login_required
def grade_submission(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        submission_id = request.POST.get('submission_id')
        marks_obtained = request.POST.get('marks_obtained')
        feedback = request.POST.get('feedback')

        if not submission_id or marks_obtained is None:
            return JsonResponse({'success': False, 'message': 'Submission ID and marks are required.'})

        submission = get_object_or_404(
            AssignmentSubmission,
            id=submission_id,
            assignment__course_offering__teacher=request.user.teacher_profile
        )
        submission.marks_obtained = int(marks_obtained)
        submission.feedback = feedback
        submission.graded_by = request.user.teacher_profile
        submission.graded_at = timezone.now()
        submission.save()
        return JsonResponse({'success': True, 'message': 'Submission graded successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


def notices(request):
    return render(request, 'faculty_staff/notices.html')


@login_required
def post_notice(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        course_offering_id = request.POST.get('course_offering_id')
        title = request.POST.get('title')
        content = request.POST.get('content')

        if not all([course_offering_id, title, content]):
            return JsonResponse({'success': False, 'message': 'All required fields must be filled.'})

        course_offering = get_object_or_404(
            CourseOffering,
            id=course_offering_id,
            teacher=request.user.teacher_profile
        )
        Notice.objects.create(
            course_offering=course_offering,
            title=title,
            content=content,
            created_by=request.user.teacher_profile
        )
        return JsonResponse({'success': True, 'message': 'Notice posted successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@login_required
def delete_notice(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        notice_id = request.POST.get('notice_id')
        if notice_id:
            notice = get_object_or_404(
                Notice,
                id=notice_id,
                course_offering__teacher=request.user.teacher_profile
            )
            notice.delete()
            return JsonResponse({'success': True, 'message': 'Notice deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Notice ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


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


@login_required
def exam_results(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/exam_results.html', {
            'error': 'Unauthorized access. Only Heads of Department can access this page.'
        })

    course_offering_id = request.GET.get('course_offering_id')
    if not course_offering_id:
        return render(request, 'faculty_staff/exam_results.html', {
            'error': 'Course offering ID is required.'
        })

    try:
        course_offering = get_object_or_404(
            CourseOffering,
            id=course_offering_id,
            teacher=request.user.teacher_profile
        )

        # Filter exam results by course_offering_id
        exam_results = ExamResult.objects.filter(
            course_offering_id=course_offering_id
        ).values('student', 'course_offering').annotate(
            mid_marks=Sum('marks_obtained', filter=Q(exam_type='midterm')),
            sessional_marks=Sum('marks_obtained', filter=Q(exam_type='sessional')),
            practical_marks=Sum('marks_obtained', filter=Q(exam_type='practical')),
            project_marks=Sum('marks_obtained', filter=Q(exam_type='project')),
        ).order_by('student')

        aggregated_results = []
        for result in exam_results:
            try:
                student = Student.objects.get(applicant_id=result['student'])
                aggregated_results.append({
                    'student': student,
                    'course': course_offering.course,
                    'mid': result['mid_marks'] or 0,
                    'sessional': result['sessional_marks'] or 0,
                    'practical': result['practical_marks'] or 0,
                    'project': result['project_marks'] or 0,
                    'final_year': f"{course_offering.academic_session.start_year}-{course_offering.academic_session.end_year}",
                    'remarks': ExamResult.objects.filter(student=student, course_offering=course_offering).first().remarks if ExamResult.objects.filter(student=student, course_offering=course_offering).exists() else "None",
                    'id': ExamResult.objects.filter(student=student, course_offering=course_offering).first().id if ExamResult.objects.filter(student=student, course_offering=course_offering).exists() else None,
                })
            except (Student.DoesNotExist, CourseOffering.DoesNotExist):
                continue

        # Load students for the course offering
        enrollments = StudentSemesterEnrollment.objects.filter(
            semester=course_offering.semester
        ).select_related('student__applicant')
        students = [{'id': enrollment.student.applicant.id, 'name': str(enrollment.student)} for enrollment in enrollments]

        return render(request, 'faculty_staff/exam_results.html', {
            'course_offering': course_offering,
            'course_offering_id': course_offering_id,
            'students': students,
            'exam_results': aggregated_results
        })
    except CourseOffering.DoesNotExist:
        return render(request, 'faculty_staff/exam_results.html', {
            'error': 'Invalid course offering or you are not authorized to access it.'
        })


@login_required
def load_students_for_course(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'})
    
    course_offering_id = request.GET.get('course_offering_id')
    if not course_offering_id:
        return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})
    
    try:
        course_offering = CourseOffering.objects.get(
            id=course_offering_id,
            teacher=request.user.teacher_profile
        )
        course_enrollments = CourseEnrollment.objects.filter(
            course_offering=course_offering,
            status='enrolled'
        ).select_related('student_semester_enrollment__student__applicant')
        students = [
            {
                'id': course_enrollment.student_semester_enrollment.student.applicant.pk,
                'name': f"{course_enrollment.student_semester_enrollment.student.applicant.full_name}"
            }
            for course_enrollment in course_enrollments
            if course_enrollment.student_semester_enrollment.semester == course_offering.semester
        ]
        return JsonResponse({
            'success': True,
            'students': students
        })
    except CourseOffering.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Course offering not found or unauthorized.'})

@login_required
def record_exam_results(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'})

    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
        enrollments = CourseEnrollment.objects.filter(
            course_offering=course_offering,
            status='enrolled'
        ).select_related('student_semester_enrollment__student__applicant')

        try:
            for enrollment in enrollments:
                student = enrollment.student_semester_enrollment.student
                student_id = student.applicant.id
                mid = request.POST.get(f'mid_{student_id}')
                sessional = request.POST.get(f'sessional_{student_id}')
                project = request.POST.get(f'project_{student_id}')
                practical = request.POST.get(f'practical_{student_id}')

                for exam_type, marks in [('midterm', mid), ('sessional', sessional), ('project', project), ('practical', practical)]:
                    if marks is not None and marks != '':
                        try:
                            marks_value = float(marks)
                            if 0 <= marks_value <= 100:
                                ExamResult.objects.update_or_create(
                                    course_offering=course_offering,
                                    student=student,
                                    exam_type=exam_type,
                                    defaults={
                                        'total_marks': 100,
                                        'marks_obtained': marks_value,
                                        'graded_by': request.user.teacher_profile,
                                        'graded_at': timezone.now()
                                    }
                                )
                            else:
                                return JsonResponse({'success': False, 'message': f'Invalid marks for {student.applicant.full_name}: must be between 0 and 100.'})
                        except ValueError:
                            return JsonResponse({'success': False, 'message': f'Invalid marks format for {student.applicant.full_name}.'})
            return JsonResponse({'success': True, 'message': 'Exam results recorded successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def delete_exam_result(request):
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'})

    if request.method == "POST":
        result_id = request.POST.get('result_id')
        if not result_id:
            return JsonResponse({'success': False, 'message': 'Result ID is required.'})
        
        try:
            result = get_object_or_404(
                ExamResult,
                id=result_id,
                course_offering__teacher=request.user.teacher_profile
            )
            result.delete()
            return JsonResponse({'success': True, 'message': 'Exam result deleted successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from courses.models import CourseOffering

@login_required
def teacher_course_list(request):
    # if not request.user.is_staff or not hasattr(request.user, 'teacher_profile'):
    #     return render(request, 'faculty_staff/unauthorized.html', {'message': 'You do not have permission to access this page.'})

    # Fetch all course offerings assigned to the logged-in teacher
    course_offerings = CourseOffering.objects.filter(
        teacher__user_id=request.user.id
    ).select_related('course', 'semester', 'academic_session')

    context = {
        'course_offerings': course_offerings,
    }
    return render(request, 'faculty_staff/teacher_course_list.html', context)

@login_required
def logout_view(request):
    logout(request)   
    return redirect('faculty_staff:login')















@login_required
def semester_management(request):
    """
    View to display, search, and manage semesters for the Head of Department's department.
    """
    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized access attempt by user: {request.user}')
        return render(request, 'faculty_staff/semester_management.html', {
            'error': 'You do not have permission to manage semesters.',
            'programs': [],
            'semesters': [],
        })
    
    hod_department = request.user.teacher_profile.department
    print(f'Semester management page loaded for user: {request.user}, department: {hod_department}')
    
    # Get search and filter parameters
    search_query = request.GET.get('q', '')
    program_id = request.GET.get('program_id', '')
    
    # Filter semesters by department
    semesters = Semester.objects.filter(program__department=hod_department).order_by('program', 'number')
    if search_query:
        semesters = semesters.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(program__name__icontains=search_query)
        )
    if program_id:
        semesters = semesters.filter(program__id=program_id, program__department=hod_department)
    
    # Pagination
    paginator = Paginator(semesters, 10)  # 10 semesters per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'programs': Program.objects.filter(department=hod_department),
        'semesters': page_obj,
        'search_query': search_query,
        'selected_program': program_id,
    }
    return render(request, 'faculty_staff/semester_management.html', context)

@login_required
def add_semester(request):
    """
    AJAX view to add a new semester for the Head of Department's department.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to add semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    hod_department = request.user.teacher_profile.department
    program_id = request.POST.get('program_id')
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'
    
    print(f'Add semester attempt: program_id={program_id}, number={number}, name={name}, user={request.user}, department={hod_department}')
    
    # Validate required fields
    required_fields = {'program_id': 'Program', 'number': 'Semester Number', 'name': 'Name'}
    missing_fields = [field_label for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        print(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})
    
    try:
        program = Program.objects.get(id=program_id, department=hod_department)
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")
        
        # Create semester
        semester = Semester(
            program=program,
            number=number,
            name=name,
            description=description,
            start_time=start_time or None,
            end_time=end_time or None,
            is_active=is_active
        )
        semester.save()  # Validation in model will check sequential numbers
        print(f'Semester created: {semester} by user: {request.user}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} added successfully!',
            'semester_id': semester.id
        })
    except Program.DoesNotExist:
        print(f'Program not found or not in department: program_id={program_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Selected program is invalid or not in your department.'})
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
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to edit semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    hod_department = request.user.teacher_profile.department
    semester_id = request.POST.get('semester_id')
    program_id = request.POST.get('program_id')
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'
    
    print(f'Edit semester attempt: semester_id={semester_id}, program_id={program_id}, number={number}, name={name}, user={request.user}, department={hod_department}')
    
    # Validate required fields
    required_fields = {'semester_id': 'Semester', 'program_id': 'Program', 'number': 'Semester Number', 'name': 'Name'}
    missing_fields = [field_label for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        print(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})
    
    try:
        semester = get_object_or_404(Semester, id=semester_id, program__department=hod_department)
        program = Program.objects.get(id=program_id, department=hod_department)
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")
        
        # Update fields
        semester.program = program
        semester.number = number
        semester.name = name
        semester.description = description
        semester.start_time = start_time or None
        semester.end_time = end_time or None
        semester.is_active = is_active
        semester.save()  # Validation in model will check sequential numbers
        print(f'Semester updated: {semester} by user: {request.user}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} updated successfully!',
            'semester_id': semester.id
        })
    except Semester.DoesNotExist:
        print(f'Semester not found or not in department: semester_id={semester_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Semester is invalid or not in your department.'})
    except Program.DoesNotExist:
        print(f'Program not found or not in department: program_id={program_id}, department={hod_department}')
        return JsonResponse({'success': False, 'message': 'Selected program is invalid or not in your department.'})
    except ValueError as e:
        print(f'Invalid data: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Invalid data: {str(e)}'})
    except ValidationError as e:
        print(f'Validation error: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Validation error: {str(e)}'})
    except Exception as e:
        print(f'Error editing semester: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error editing semester: {str(e)}'})

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

@login_required
def add_semester(request):
    """
    AJAX view to add a new semester.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to add semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    program_id = request.POST.get('program_id')
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'
    
    print(f'Add semester attempt: program_id={program_id}, number={number}, name={name}, user={request.user}')
    
    # Validate required fields
    required_fields = {'program_id': 'Program', 'number': 'Semester Number', 'name': 'Name'}
    missing_fields = [field_label for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        print(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})
    
    try:
        program = Program.objects.get(id=program_id)
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")
        
        # Create semester
        semester = Semester(
            program=program,
            number=number,
            name=name,
            description=description,
            start_time=start_time or None,
            end_time=end_time or None,
            is_active=is_active
        )
        semester.save()  # Validation in model will check sequential numbers
        print(f'Semester created: {semester} by user: {request.user}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} added successfully!',
            'semester_id': semester.id
        })
    except Program.DoesNotExist:
        print(f'Program not found: program_id={program_id}')
        return JsonResponse({'success': False, 'message': 'Selected program no longer exists.'})
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
    AJAX view to edit an existing semester.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to edit semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    semester_id = request.POST.get('semester_id')
    program_id = request.POST.get('program_id')
    number = request.POST.get('number')
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    is_active = request.POST.get('is_active', 'false') == 'true'
    
    print(f'Edit semester attempt: semester_id={semester_id}, program_id={program_id}, number={number}, name={name}, user={request.user}')
    
    # Validate required fields
    required_fields = {'semester_id': 'Semester', 'program_id': 'Program', 'number': 'Semester Number', 'name': 'Name'}
    missing_fields = [field_label for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
    if missing_fields:
        print(f'Missing fields: {", ".join(missing_fields)}')
        return JsonResponse({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'})
    
    try:
        semester = get_object_or_404(Semester, id=semester_id)
        program = Program.objects.get(id=program_id)
        number = int(number)
        if number < 1:
            raise ValueError("Semester number must be a positive integer.")
        
        # Update fields
        semester.program = program
        semester.number = number
        semester.name = name
        semester.description = description
        semester.start_time = start_time or None
        semester.end_time = end_time or None
        semester.is_active = is_active
        semester.save()  # Validation in model will check sequential numbers
        print(f'Semester updated: {semester} by user: {request.user}')
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester.name} updated successfully!',
            'semester_id': semester.id
        })
    except Program.DoesNotExist:
        print(f'Program not found: program_id={program_id}')
        return JsonResponse({'success': False, 'message': 'Selected program no longer exists.'})
    except ValueError as e:
        print(f'Invalid data: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Invalid data: {str(e)}'})
    except ValidationError as e:
        print(f'Validation error: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Validation error: {str(e)}'})
    except Exception as e:
        print(f'Error editing semester: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error editing semester: {str(e)}'})

@login_required
def delete_semester(request):
    """
    AJAX view to delete a semester.
    """
    if request.method != "POST" or not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.designation != 'head_of_department':
        print(f'Unauthorized or invalid request to delete semester by user: {request.user}')
        return JsonResponse({'success': False, 'message': 'Invalid request or insufficient permissions.'})
    
    semester_id = request.POST.get('semester_id')
    print(f'Delete semester attempt: semester_id={semester_id}, user={request.user}')
    
    if not semester_id:
        print('Missing semester_id for deletion')
        return JsonResponse({'success': False, 'message': 'Missing semester ID.'})
    
    try:
        semester = get_object_or_404(Semester, id=semester_id)
        semester_name = semester.name
        semester.delete()
        print(f'Semester deleted: {semester_name} by user: {request.user}')    
        return JsonResponse({
            'success': True,
            'message': f'Semester {semester_name} deleted successfully!'
        })
    except Exception as e:
        print(f'Error deleting semester: {str(e)}')
        return JsonResponse({'success': False, 'message': f'Error deleting semester: {str(e)}'})
    
    
    
    
    
    
@login_required
def attendance(request):
    students = []
    course_offering_id = request.GET.get('course_offering_id')
    course_shift = None
    if course_offering_id:
        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        course_shift = course_offering.shift
        enrollments = StudentSemesterEnrollment.objects.filter(semester=course_offering.semester).select_related('student')
        students = [
            {
                'id': enrollment.student.applicant.id,
                'name': str(enrollment.student),
                'college_roll_no': enrollment.student.college_roll_no,
                'university_roll_no': enrollment.student.university_roll_no
            } for enrollment in enrollments
        ]

    context = {
        'students': students,
        'course_offering_id': course_offering_id,
        'course_shift': course_shift,
        'today_date': timezone.now().date(),
    }
    return render(request, 'faculty_staff/attendance.html', context)

@login_required
def record_attendance(request):
    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        shift = request.POST.get('shift')
        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering is required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        if course_offering.shift == 'both' and not shift:
            return JsonResponse({'success': False, 'message': 'Shift is required for this course.'})

        today = timezone.now().date()
        # Check if attendance already exists
        shifts_to_check = ['morning', 'evening'] if shift == 'both' else [shift if shift in ['morning', 'evening'] else None]
        for check_shift in shifts_to_check:
            if Attendance.objects.filter(
                course_offering=course_offering,
                date=today,
                shift=check_shift if course_offering.shift == 'both' else None
            ).exists():
                return JsonResponse({'success': False, 'message': f'Attendance already recorded for {check_shift or "this course"} on this date.'})

        enrollments = CourseEnrollment.objects.filter(
            course_offering=course_offering,
            status='enrolled'
        ).select_related('student_semester_enrollment__student__applicant')
        if shift in ['morning', 'evening']:
            enrollments = enrollments.filter(student_semester_enrollment__student__applicant__shift=shift)
        
        teacher = get_object_or_404(Teacher, user=request.user)
        shifts_to_record = ['morning', 'evening'] if shift == 'both' else [shift if shift in ['morning', 'evening'] else None]

        for enrollment in enrollments:
            student = enrollment.student_semester_enrollment.student
            student_id = student.applicant.id
            status = request.POST.get(f'status_{student_id}')
            if status in ['present', 'absent', 'leave']:
                for record_shift in shifts_to_record:
                    Attendance.objects.update_or_create(
                        student=student,
                        course_offering=course_offering,
                        date=today,
                        shift=record_shift if course_offering.shift == 'both' else None,
                        defaults={
                            'status': status,
                            'recorded_by': teacher,
                            'recorded_at': timezone.now()
                        }
                    )

        return JsonResponse({'success': True, 'message': 'Attendance recorded successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def load_students_for_course(request):
    if request.method == "GET":
        course_offering_id = request.GET.get('course_offering_id')
        shift = request.GET.get('shift')
        if course_offering_id:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
            enrollments = CourseEnrollment.objects.filter(
                course_offering=course_offering,
                status='enrolled'
            ).select_related(
                'student_semester_enrollment__student__applicant',
                'student_semester_enrollment__semester'
            )
            if shift in ['morning', 'evening'] and course_offering.shift == 'both':
                enrollments = enrollments.filter(student_semester_enrollment__student__applicant__shift=shift)
            
            students = [
                {
                    'id': course_enrollment.student_semester_enrollment.student.applicant.pk,
                    'name': f"{course_enrollment.student_semester_enrollment.student.applicant.full_name}",
                    'college_roll_no': course_enrollment.student_semester_enrollment.student.college_roll_no,
                    'university_roll_no': course_enrollment.student_semester_enrollment.student.university_roll_no
                }
                for course_enrollment in enrollments
                if course_enrollment.student_semester_enrollment.semester == course_offering.semester
            ]
            return JsonResponse({
                'success': True,
                'students': students
            })
        return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})
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
                return JsonResponse({'success': False, 'message': 'Can only edit today’s attendance.'})
            teacher = get_object_or_404(Teacher, user=request.user)
            attendance.status = status
            attendance.shift = shift
            attendance.recorded_by = teacher
            attendance.recorded_at = timezone.now()
            attendance.save()
            return JsonResponse({'success': True, 'message': 'Attendance updated successfully.'})
        return JsonResponse({'success': False, 'message': 'Invalid data provided.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})