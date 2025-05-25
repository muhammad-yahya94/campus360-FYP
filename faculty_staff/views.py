from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from academics.models import Department, Program , Semester
from admissions.models import AcademicSession
from .models import Teacher
from admissions.models import AdmissionCycle , Applicant
from students.models import Student

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




from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('faculty_staff:login')