# Standard library imports
import os

# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
from courses.models import Course, CourseOffering, ExamResult, StudyMaterial, Assignment, AssignmentSubmission, Notice, Attendance
from faculty_staff.models import Teacher
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
import datetime
# Custom user model
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

    # Fetch academic sessions for the sidebar
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'active_students': active_students,
        'current_sessions': current_sessions,
        'department_programs': department_programs,
        'working_semesters': working_semesters,
        'department': hod_department,
        'academic_sessions': academic_sessions,
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

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'staff_members': staff_members,
        'department': hod_department,
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,
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
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'designation': True},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
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
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,
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
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        if CustomUser.objects.filter(email=email).exclude(id=teacher.user.id).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        if designation not in dict(Teacher.DESIGNATION_CHOICES).keys():
            messages.error(request, 'Invalid designation selected.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'designation': True},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
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
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    return render(request, 'faculty_staff/staff_management.html', {
        'department': hod_department,
        'staff_members': Teacher.objects.filter(department=hod_department),
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,
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
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     messages.error(request, 'You do not have permission to access this page.')
    #     return redirect('home')

    hod_department = request.user.teacher_profile.department
    if not hod_department:
        messages.error(request, 'HOD must be associated with a department.')
        return redirect('home')

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    programs = Program.objects.filter(department=hod_department)
    teachers = Teacher.objects.filter(is_active=True, department=hod_department)
    semesters = Semester.objects.filter(program__in=programs).distinct()
    course_offerings = CourseOffering.objects.filter(
        department=hod_department
    ).select_related('course', 'teacher', 'program', 'department', 'academic_session', 'semester')

    context = {
        'academic_sessions': academic_sessions,
        'semesters': semesters,
        'programs': programs,
        'teachers': teachers,
        'course_offerings': course_offerings,
        'department': hod_department,
        'session_id': None,
    }
    return render(request, 'faculty_staff/course_offerings.html', context)


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
            is_active=True 
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


def get_offering_type_choices(request):
    choices = [{'id': value, 'text': label} for value, label in CourseOffering.OFFERING_TYPES]
    return JsonResponse({'results': choices})




@login_required
@transaction.atomic
def save_course_offering(request):
    print(f'Request method: {request.method}, User: {request.user}')
    
    if request.method == "POST" and hasattr(request.user, 'teacher_profile') and request.user.teacher_profile.designation == 'head_of_department':
        course_id = request.POST.get('course_id')
        teacher_id = request.POST.get('teacher_id')
        program_id = request.POST.get('program_id')
        semester_id = request.POST.get('semester_id')
        academic_session_id = request.POST.get('academic_session_id')
        offering_type = request.POST.get('offering_type')
        shift = request.POST.get('shift')
        
        print(f'course_id: {course_id}, teacher_id: {teacher_id}, program_id: {program_id}, '
              f'semester_id: {semester_id}, academic_session_id: {academic_session_id}, '
              f'offering_type: {offering_type}, shift: {shift}')

        # Check for missing fields
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
            print(f'Missing fields: {", ".join([required_fields[field] for field in missing_fields])}')
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join([required_fields[field] for field in missing_fields])}'
            })

        # Validate offering type
        valid_offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
        if offering_type not in valid_offering_types:
            print(f'Invalid offering type: {offering_type}')
            return JsonResponse({
                'success': False,
                'message': 'Invalid offering type selected.'
            })

        # Validate shift
        valid_shifts = ['morning', 'evening', 'both']
        if shift not in valid_shifts:
            print(f'Invalid shift: {shift}')
            return JsonResponse({
                'success': False,
                'message': 'Invalid shift selected.'
            })

        # Retrieve objects
        try:
            course = Course.objects.get(id=course_id)
            teacher = Teacher.objects.get(id=teacher_id, is_active=True)
            program = Program.objects.get(id=program_id)
            semester = Semester.objects.get(id=semester_id)
            academic_session = AcademicSession.objects.get(id=academic_session_id)
        except (Course.DoesNotExist, Teacher.DoesNotExist, Program.DoesNotExist, 
                Semester.DoesNotExist, AcademicSession.DoesNotExist) as e:
            print(f'Object retrieval failed: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': 'One or more selected items no longer exist.'
            })

        # Check for existing offerings
        existing_offerings = CourseOffering.objects.filter(
            course=course,
            program=program,
            academic_session=academic_session,
            semester=semester,
            offering_type=offering_type,
            shift=shift
        )
        if existing_offerings.exists():
            print('Course offering already exists')
            return JsonResponse({
                'success': False,
                'message': 'This exact course offering already exists.'
            })

        # Get active students with compatible shift
        active_students = Student.objects.filter(
            program=program,
            current_semester=semester,
            current_status='active'
        )
        if not active_students.exists():
            print('No active students found')
            return JsonResponse({
                'success': False,
                'message': 'No active students found for this program and semester.'
            })

        # Filter students by shift compatibility
        compatible_students = []
        for student in active_students:
            applicant_shift = student.applicant.shift
            if shift == 'both' or applicant_shift == shift:
                compatible_students.append(student)
            else:
                print(f'Skipping student {student.applicant.full_name}: Applicant shift {applicant_shift}, Course shift {shift}')

        if not compatible_students:
            print('No students with compatible shifts')
            return JsonResponse({
                'success': False,
                'message': 'No students have a compatible shift preference for this course offering.'
            })

        # Create course offering and enroll compatible students
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
                if created:
                    enrolled_count += 1
                    enrolled_student_names.append(student.applicant.full_name)
                elif course_enrollment.status != 'enrolled':
                    course_enrollment.status = 'enrolled'
                    course_enrollment.save()
                    enrolled_count += 1
                    enrolled_student_names.append(student.applicant.full_name)

            offering.current_enrollment = enrolled_count
            offering.save()
            print(f'Course offering created: {course.code}, Shift: {shift}, Enrolled: {enrolled_count}, Students: {", ".join(enrolled_student_names)}')
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully created course offering for {course.code} ({shift.capitalize()} shift) with {enrolled_count} students enrolled.',
                'offering_id': offering.id
            })
        except Exception as e:
            print(f'Error saving course offering: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Error saving course offering: {str(e)}'
            })

    print('Failed: Invalid method or permissions')
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method or insufficient permissions.'
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
    if request.user.teacher_profile.designation == 'head_of_department':
        assignments = Assignment.objects.filter(
            course_offering__teacher=request.user.teacher_profile
        ).order_by('-created_at')
        return render(request, 'faculty_staff/assignments.html', {'assignments': assignments})
    return JsonResponse({'success': False, 'message': 'Unauthorized access.'})


@login_required
def create_assignment(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        course_offering_id = request.POST.get('course_offering_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        total_marks = request.POST.get('total_marks')
        file = request.FILES.get('file')

        if not all([course_offering_id, title, due_date, total_marks]):
            return JsonResponse({'success': False, 'message': 'All required fields must be filled.'})

        course_offering = get_object_or_404(
            CourseOffering,
            id=course_offering_id,
            teacher=request.user.teacher_profile
        )
        Assignment.objects.create(
            course_offering=course_offering,
            title=title,
            description=description,
            due_date=due_date,
            total_marks=total_marks,
            file=file,
            created_by=request.user.teacher_profile
        )
        return JsonResponse({'success': True, 'message': 'Assignment created successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@login_required
def delete_assignment(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        assignment_id = request.POST.get('assignment_id')
        if assignment_id:
            assignment = get_object_or_404(
                Assignment,
                id=assignment_id,
                course_offering__teacher=request.user.teacher_profile
            )
            if assignment.file and os.path.isfile(assignment.file.path):
                os.remove(assignment.file.path)
            assignment.delete()
            return JsonResponse({'success': True, 'message': 'Assignment deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


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
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     return render(request, 'faculty_staff/unauthorized.html', {'message': 'You do not have permission to access this page.'})

    exam_results = ExamResult.objects.values('student', 'course_offering').annotate(
        mid_marks=Sum('marks_obtained', filter=Q(exam_type='midterm')),
        sessional_marks=Sum('marks_obtained', filter=Q(exam_type='sessional')),
        practical_marks=Sum('marks_obtained', filter=Q(exam_type='practical')),
        project_marks=Sum('marks_obtained', filter=Q(exam_type='project')),
    ).order_by('student', 'course_offering')

    aggregated_results = []
    for result in exam_results:
        try:
            student = Student.objects.get(applicant_id=result['student'])
            course_offering = CourseOffering.objects.get(id=result['course_offering'])
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

    students = []
    if request.GET.get('course_offering_id'):
        course_offering = get_object_or_404(CourseOffering, id=request.GET.get('course_offering_id'))
        enrollments = StudentSemesterEnrollment.objects.filter(semester=course_offering.semester).select_related('student')
        students = [{'id': enrollment.student.applicant.id, 'name': str(enrollment.student)} for enrollment in enrollments]

    context = {
        'exam_results': aggregated_results,
        'students': students,
    }
    return render(request, 'faculty_staff/exam_results.html', context)


@login_required
def record_exam_results(request):
    # if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
    #     return JsonResponse({'success': False, 'message': 'You do not have permission to access this page.'})

    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering is required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        enrollments = StudentSemesterEnrollment.objects.filter(semester=course_offering.semester).select_related('student')

        for enrollment in enrollments:
            student = enrollment.student
            student_id = student.applicant.id
            mid = request.POST.get(f'mid_{student_id}')
            sessional = request.POST.get(f'sessional_{student_id}')
            project = request.POST.get(f'project_{student_id}')
            practical = request.POST.get(f'practical_{student_id}')

            for exam_type, marks in [('midterm', mid), ('sessional', sessional), ('project', project), ('practical', practical)]:
                if marks is not None and marks != '':
                    try:
                        marks_value = int(marks)
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
                            return JsonResponse({'success': False, 'message': f'Invalid marks for {student}: must be between 0 and 100.'})
                    except ValueError:
                        return JsonResponse({'success': False, 'message': f'Invalid marks format for {student}.'})

        return JsonResponse({'success': True, 'message': 'Exam results recorded successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def load_students_for_course(request):
    if request.method == "GET":
        course_offering_id = request.GET.get('course_offering_id')
        if course_offering_id:
            course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
            course_enrollments = CourseEnrollment.objects.filter(
                course_offering=course_offering,
                status='enrolled'
            ).select_related(
                'student_semester_enrollment__student__applicant',
                'student_semester_enrollment__semester'
            )
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
        return JsonResponse({'success': False, 'message': 'Course offering ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def delete_exam_result(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        result_id = request.POST.get('result_id')
        if result_id:
            result = get_object_or_404(
                ExamResult,
                id=result_id,
                course_offering__teacher=request.user.teacher_profile
            )
            result.delete()
            return JsonResponse({'success': True, 'message': 'Exam result deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Result ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})



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