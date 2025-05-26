from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from academics.models import Department, Program , Semester
from admissions.models import AcademicSession
from courses.models import Course , CourseOffering , ExamResult, StudyMaterial , Assignment , AssignmentSubmission , Notice
from .models import Teacher
from admissions.models import AdmissionCycle , Applicant
from students.models import Student , StudentSemesterEnrollment , CourseEnrollment
from django.http import JsonResponse
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone  
from django.db import transaction
CustomUser = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect('faculty_staff:hod_dashboard')

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
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
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
    
    # Number of active students in the HOD's department
    active_students = Student.objects.filter(
        program__department=hod_department,
        current_status='active'
    ).count()
    
    # Number of active academic sessions
    current_sessions = AcademicSession.objects.filter(is_active=True).count()
    
    # Number of programs in the HOD's department
    department_programs = Program.objects.filter(department=hod_department).count()
    
    # Number of active semesters in the HOD's department programs
    working_semesters = Semester.objects.filter(
        program__department=hod_department,
        is_active=True
    ).count()

    # Fetch academic sessions for the sidebar
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'total_staff': total_staff,
        'active_staff': active_staff,
        'active_students': active_students,  # Replacing pending_tasks
        'current_sessions': current_sessions,  # Replacing total_departments
        'department_programs': department_programs,  # New card
        'working_semesters': working_semesters,  # New card
        'department': hod_department,
        'academic_sessions': academic_sessions,  # For sidebar dropdown
    }
    return render(request, 'faculty_staff/hod_dashboard.html', context)

@login_required
def staff_management(request):
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

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

    # Fetch academic sessions for the sidebar
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'staff_members': staff_members,
        'department': hod_department,
        'designation_choices': Teacher.DESIGNATION_CHOICES,
        'academic_sessions': academic_sessions,  # For sidebar dropdown
    }
    return render(request, 'faculty_staff/staff_management.html', context)

@login_required
def add_staff(request):
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')

    hod_department = request.user.teacher_profile.department

    if request.method == 'POST':
        # Extract form data
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

        # Validate required fields
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

        # Validate email uniqueness
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        # Validate designation
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
            # Create CustomUser
            user = CustomUser.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=True
            )
            # Set a default password (consider sending a reset link in production)
            user.set_password('defaultpassword123')
            user.save()

            # Create Teacher
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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')

    hod_department = request.user.teacher_profile.department
    teacher = get_object_or_404(Teacher, id=staff_id, department=hod_department)

    if request.method == 'POST':
        # Extract form data
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

        # Validate required fields
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

        # Validate email uniqueness (exclude current user)
        if CustomUser.objects.filter(email=email).exclude(id=teacher.user.id).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'faculty_staff/staff_management.html', {
                'department': hod_department,
                'staff_members': Teacher.objects.filter(department=hod_department),
                'designation_choices': Teacher.DESIGNATION_CHOICES,
                'form_errors': {'email': 'exists'},
                'academic_sessions': AcademicSession.objects.all().order_by('-start_year'),
            })

        # Validate designation
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
            # Update CustomUser
            teacher.user.first_name = first_name
            teacher.user.last_name = last_name
            teacher.user.email = email
            teacher.user.save()

            # Update Teacher
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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')

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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    # Get the HOD's department
    hod_department = request.user.teacher_profile.department

    # Fetch the academic session
    session = get_object_or_404(AcademicSession, id=session_id)

    # Fetch the programs under the HOD's department
    programs = Program.objects.filter(department=hod_department)

    # Fetch applicants linked to these programs
    applicants = Applicant.objects.filter(program__in=programs)

    # Initialize base queryset
    students = Student.objects.filter(
        applicant__in=applicants,
        program__in=programs,
        enrollment_date__year=session.start_year  # Exact match for the session's start year
    ).select_related('applicant', 'program', 'current_semester')

    # Handle search parameter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        students = students.filter(
            Q(university_roll_no__icontains=search_query) | 
            Q(applicant__full_name__icontains=search_query) |
            Q(college_roll_no__icontains=search_query)        
        )

    # Pagination
    paginator = Paginator(students, 10)  # 10 students per page
    page_number = request.GET.get('page')
    page_students = paginator.get_page(page_number)

    # Fetch academic sessions for the sidebar
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'session': session,
        'students': page_students,
        'department': hod_department,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'faculty_staff/session_students.html', context)




from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse


class CourseForm(forms.Form):
    code = forms.CharField(max_length=10, required=True, help_text="Enter the unique course code (e.g., CS101).")
    name = forms.CharField(max_length=200, required=True, help_text="Enter the full name of the course.")
    credits = forms.IntegerField(min_value=1, required=True, help_text="Enter the number of credit hours.")
    is_active = forms.BooleanField(required=False, initial=True, help_text="Check this if the course is active.")
    description = forms.CharField(widget=forms.Textarea, required=False, help_text="Provide a description.")

@login_required
def add_course(request):
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    hod_department = request.user.teacher_profile.department
    if not hod_department:
        messages.error(request, 'HOD must be associated with a department.')
        return redirect('home')

    academic_sessions = AcademicSession.objects.all().order_by('-start_year')
    programs = Program.objects.filter(department=hod_department)  # Filter programs by HOD's department
    teachers = Teacher.objects.filter(is_active=True, department=hod_department)
    semesters = Semester.objects.filter(program__in=programs).distinct()
    # Filter teachers by HOD's department

    # Fetch existing course offerings for display, filtered by HOD's department
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
        ).values('id', 'code', 'name')[:10]  # Limit to 10 results for performance
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
            Q(user__first_name__icontains=search_query) | Q(user__last_name__icontains=search_query)
        ).values('id', 'user__first_name', 'user__last_name', 'department__name')[:10]
        return JsonResponse({
            'results': [{'id': teacher['id'], 'text': f"{teacher['user__first_name']} {teacher['user__last_name']} ({teacher['department__name']})"} for teacher in teachers],
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
                # Else, keep all programs (optional fallback)
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
        program_id = request.GET.get('program_id')  # Get program ID from the query string

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





# @login_required
# @transaction.atomic
# def save_course_offering(request):
#     if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
#         # Get all form data
#         course_id = request.POST.get('course_id')
#         teacher_id = request.POST.get('teacher_id')
#         program_id = request.POST.get('program_id')
#         semester_id = request.POST.get('semester_id')
#         academic_session_id = request.POST.get('academic_session_id')
#         offering_type = request.POST.get('offering_type')

#         # Validate all required fields
#         required_fields = {
#             'course_id': 'Course',
#             'teacher_id': 'Teacher',
#             'program_id': 'Program',
#             'semester_id': 'Semester',
#             'academic_session_id': 'Academic Session',
#             'offering_type': 'Offering Type'
#         }
        
#         missing_fields = [field_name for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
#         if missing_fields:
#             return JsonResponse({
#                 'success': False,
#                 'message': f'Missing required fields: {", ".join([required_fields[field] for field in missing_fields])}'
#             })

#         # Validate offering type
#         valid_offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
#         if offering_type not in valid_offering_types:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'Invalid offering type selected.'
#             })

#         # Get all related objects
#         try:
#             course = Course.objects.get(id=course_id)
#             teacher = Teacher.objects.get(id=teacher_id, is_active=True)
#             program = Program.objects.get(id=program_id)
#             semester = Semester.objects.get(id=semester_id)
#             academic_session = AcademicSession.objects.get(id=academic_session_id)
#         except (Course.DoesNotExist, Teacher.DoesNotExist, 
#                 Program.DoesNotExist, Semester.DoesNotExist, 
#                 AcademicSession.DoesNotExist) as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'One or more selected items no longer exist.'
#             })

#         # Check for existing offering with the exact same combination
#         existing_offerings = CourseOffering.objects.filter(
#             course=course,
#             program=program,
#             academic_session=academic_session,
#             semester=semester,
#             offering_type=offering_type
#         )
        
#         if existing_offerings.exists():
#             return JsonResponse({
#                 'success': False,
#                 'message': 'This exact course offering already exists.'
#             })

#         # Calculate capacity and enrollment
#         active_students = Student.objects.filter(
#             program=program,
#             current_semester=semester,
#             current_status='active'
#         )

#         print("Creating CourseOffering with:")
#         print({
#             "course": course,
#             "teacher": teacher,
#             "department": program.department,
#             "program": program,
#             "academic_session": academic_session,
#             "semester": semester,
#             "is_active": True,
#             "offering_type": offering_type,
#         })

#         # Create the offering
#         offering = CourseOffering.objects.create(
#             course=course,
#             teacher=teacher,
#             department=program.department,
#             program=program,
#             academic_session=academic_session,
#             semester=semester,
#             is_active=True,
#             offering_type=offering_type
#         )
        
#         return JsonResponse({
#             'success': True,
#             'message': f'Successfully created course offering for {course.code}',
#             'offering_id': offering.id
#         })
    
#     return JsonResponse({
#         'success': False,
#         'message': 'Invalid request method or insufficient permissions.'
#     })



@login_required
@transaction.atomic
def save_course_offering(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        # Get all form data
        course_id = request.POST.get('course_id')
        teacher_id = request.POST.get('teacher_id')
        program_id = request.POST.get('program_id')
        semester_id = request.POST.get('semester_id')
        academic_session_id = request.POST.get('academic_session_id')
        offering_type = request.POST.get('offering_type')

        # Validate all required fields
        required_fields = {
            'course_id': 'Course',
            'teacher_id': 'Teacher',
            'program_id': 'Program',
            'semester_id': 'Semester',
            'academic_session_id': 'Academic Session',
            'offering_type': 'Offering Type'
        }
        
        missing_fields = [field_name for field_name, field_label in required_fields.items() if not request.POST.get(field_name)]
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join([required_fields[field] for field in missing_fields])}'
            })

        # Validate offering type
        valid_offering_types = [choice[0] for choice in CourseOffering.OFFERING_TYPES]
        if offering_type not in valid_offering_types:
            return JsonResponse({
                'success': False,
                'message': 'Invalid offering type selected.'
            })

        # Get all related objects
        try:
            course = Course.objects.get(id=course_id)
            teacher = Teacher.objects.get(id=teacher_id, is_active=True)
            program = Program.objects.get(id=program_id)
            semester = Semester.objects.get(id=semester_id)
            academic_session = AcademicSession.objects.get(id=academic_session_id)
        except (Course.DoesNotExist, Teacher.DoesNotExist, 
                Program.DoesNotExist, Semester.DoesNotExist, 
                AcademicSession.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'message': 'One or more selected items no longer exist.'
            })

        # Check for existing offering with the exact same combination
        existing_offerings = CourseOffering.objects.filter(
            course=course,
            program=program,
            academic_session=academic_session,
            semester=semester,
            offering_type=offering_type
        )
        
        if existing_offerings.exists():
            return JsonResponse({
                'success': False,
                'message': 'This exact course offering already exists.'
            })

        # Identify active students in the program and semester
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

        # Create the offering
        offering = CourseOffering.objects.create(
            course=course,
            teacher=teacher,
            department=program.department,
            program=program,
            academic_session=academic_session,
            semester=semester,
            is_active=True,
            offering_type=offering_type,
            # max_capacity=active_students.count(),  # Set max capacity based on active students
            current_enrollment=0  # Initialize to 0, will update below
        )

        # Add students to the course offering via CourseEnrollment
        enrolled_count = 0
        for student in active_students:
            # Ensure the student has a semester enrollment for this semester
            semester_enrollment, created = StudentSemesterEnrollment.objects.get_or_create(
                student=student,
                semester=semester,
                defaults={'status': 'enrolled'}
            )

            # Create a new CourseEnrollment for this offering
            course_enrollment, created = CourseEnrollment.objects.get_or_create(
                student_semester_enrollment=semester_enrollment,
                course_offering=offering,
                defaults={'status': 'enrolled'}
            )

            if created:
                enrolled_count += 1
            # If already exists, ensure the status is 'enrolled'
            elif course_enrollment.status != 'enrolled':
                course_enrollment.status = 'enrolled'
                course_enrollment.save()
                enrolled_count += 1

        # Update the current_enrollment of the CourseOffering
        offering.current_enrollment = enrolled_count
        offering.save()

        return JsonResponse({
            'success': True,
            'message': f'Successfully created course offering for {course.code} with {enrolled_count} students enrolled.',
            'offering_id': offering.id
        })
    
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
    if request.user.teacher_profile.designation == 'head_of_department':
        study_materials = StudyMaterial.objects.filter(course_offering__teacher=request.user.teacher_profile).order_by('-uploaded_at')
        return render(request, 'faculty_staff/study_materials.html', {'study_materials': study_materials})
    return JsonResponse({'success': False, 'message': 'Unauthorized access.'})

@login_required
def upload_study_material(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        course_offering_id = request.POST.get('course_offering_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')

        if not all([course_offering_id, title, file]):
            return JsonResponse({'success': False, 'message': 'All required fields must be filled.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
        StudyMaterial.objects.create(
            course_offering=course_offering,
            title=title,
            description=description,
            file=file,
            uploaded_by=request.user.teacher_profile
        )
        return JsonResponse({'success': True, 'message': 'Study material uploaded successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def delete_study_material(request):
    if request.method == "POST" and request.user.teacher_profile.designation == 'head_of_department':
        material_id = request.POST.get('material_id')
        if material_id:
            material = get_object_or_404(StudyMaterial, id=material_id, course_offering__teacher=request.user.teacher_profile)
            if material.file:
                if os.path.isfile(material.file.path):
                    os.remove(material.file.path)
            material.delete()
            return JsonResponse({'success': True, 'message': 'Study material deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Material ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# @login_required
# def search_course_offerings(request):
#     if request.method == "GET":
#         search_query = request.GET.get('q', '')
#         offerings = CourseOffering.objects.filter(
#             Q(course__code__icontains=search_query) | Q(course__name__icontains=search_query),
#             teacher=request.user.teacher_profile
#         ).values('id', 'course__code', 'course__name', 'semester__name', 'academic_session__name')[:10]
#         return JsonResponse({
#             'results': [{'id': offering['id'], 'text': f"{offering['course__code']} - {offering['course__name']} ({offering['semester__name']}, {offering['academic_session__name']})"} for offering in offerings],
#             'more': False
#         })
#     return JsonResponse({'results': [], 'more': False})


@login_required
def search_course_offerings(request):
    if request.method == "GET":
        search_query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        per_page = 10

        course_offerings = CourseOffering.objects.all().select_related('course', 'semester', 'academic_session')

        if search_query:
            course_offerings = course_offerings.filter(
                Q(course__code__icontains=search_query) |
                Q(course__name__icontains=search_query) |
                Q(semester__name__icontains=search_query) |
                Q(academic_session__name__icontains=search_query)
            )

        start = (page - 1) * per_page
        end = start + per_page
        paginated_offerings = course_offerings[start:end]

        results = [
            {'id': offering.id, 'text': str(offering)} for offering in paginated_offerings
        ]

        return JsonResponse({
            'results': results,
            'pagination': {'more': end < course_offerings.count()}
        })
    return JsonResponse({'results': [], 'pagination': {'more': False}})




@login_required
def assignments(request):
    if request.user.teacher_profile.designation == 'head_of_department':
        assignments = Assignment.objects.filter(course_offering__teacher=request.user.teacher_profile).order_by('-created_at')
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

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
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
            assignment = get_object_or_404(Assignment, id=assignment_id, course_offering__teacher=request.user.teacher_profile)
            if assignment.file:
                if os.path.isfile(assignment.file.path):
                    os.remove(assignment.file.path)
            assignment.delete()
            return JsonResponse({'success': True, 'message': 'Assignment deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Assignment ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def assignment_submissions(request, assignment_id):
    if request.user.teacher_profile.designation == 'head_of_department':
        assignment = get_object_or_404(Assignment, id=assignment_id, course_offering__teacher=request.user.teacher_profile)
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

        submission = get_object_or_404(AssignmentSubmission, id=submission_id, assignment__course_offering__teacher=request.user.teacher_profile)
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

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id, teacher=request.user.teacher_profile)
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
            notice = get_object_or_404(Notice, id=notice_id, course_offering__teacher=request.user.teacher_profile)
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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        return render(request, 'faculty_staff/unauthorized.html', {'message': 'You do not have permission to access this page.'})

    # Aggregate exam results by student and course offering
    exam_results = ExamResult.objects.values('student', 'course_offering').annotate(
        mid_marks=Sum('marks_obtained', filter=Q(exam_type='midterm')),
        sessional_marks=Sum('marks_obtained', filter=Q(exam_type='sessional')),
        practical_marks=Sum('marks_obtained', filter=Q(exam_type='practical')),
        project_marks=Sum('marks_obtained', filter=Q(exam_type='project')),
    ).order_by('student', 'course_offering')  # Order for better readability

    # Convert to a list of dictionaries with additional data
    aggregated_results = []
    for result in exam_results:
        try:
            student = Student.objects.get(applicant_id=result['student'])  # Use applicant_id since Student uses applicant as PK
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
            continue  # Skip if student or course offering doesn't exist

    # Load students for the form (optional, can be moved to load_students_for_course)
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
    if not request.user.is_staff or request.user.teacher_profile.designation != 'head_of_department':
        return JsonResponse({'success': False, 'message': 'You do not have permission to access this page.'})

    if request.method == "POST":
        course_offering_id = request.POST.get('course_offering_id')
        if not course_offering_id:
            return JsonResponse({'success': False, 'message': 'Course offering is required.'})

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        enrollments = StudentSemesterEnrollment.objects.filter(semester=course_offering.semester).select_related('student')

        for enrollment in enrollments:
            student = enrollment.student
            student_id = student.applicant.id  # Use applicant.id as the primary key
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
            # Query CourseEnrollment to find enrollments for this CourseOffering
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
            result = get_object_or_404(ExamResult, id=result_id, course_offering__teacher=request.user.teacher_profile)
            result.delete()
            return JsonResponse({'success': True, 'message': 'Exam result deleted successfully.'})
        return JsonResponse({'success': False, 'message': 'Result ID is required.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})









from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('faculty_staff:login')