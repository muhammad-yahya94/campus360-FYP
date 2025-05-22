from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from announcements.models import Event, News
from academics.models import Faculty, Department, Program
from admissions.models import AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from users.models import CustomUser
import json
import logging
from datetime import datetime  
from site_elements.models import Alumni, Gallery
from faculty_staff.models import Teacher, Office, OfficeStaff

from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# Authentication Views
def register_view(request):
    context = {}
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            context['register_error'] = 'Passwords do not match'
        else:
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False, # Deactivate user until email is verified
                )
                
                # Generate token and send verification email
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                domain = request.get_host() # Get the current domain
                verify_url = f'http://{domain}/verify/{uid}/{token}/'
                
                subject = 'Verify your email address'
                message = render_to_string('emails/verify_email.html', {
                    'user': user,
                    'verify_url': verify_url,
                })
                
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                
                messages.success(request, 'Please check your email to verify your account.')
                return redirect('email_verification_success') # Redirect to success page

            except Exception as e:   
                context['register_error'] = str(e)
                logger.error(f"Error during user registration: {e}", exc_info=True)

        # Preserve form inputs on error
        context.update({
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        })

    return render(request, 'admission.html', context)


def login_view(request):
    context = {}
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'

        user = authenticate(request, email=email, password=password)
        if user is not None:
            # Check if user is active (email verified) before logging in
            if user.is_active:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                # Redirect to apply page after successful login and verification
                return redirect(request.GET.get('next', 'apply'))
            else:
                context['login_error'] = 'Please verify your email address before logging in.'
        else:
            context['login_error'] = 'Invalid email or password'
            context['entered_email'] = email
            logger.warning(f"Failed login attempt for email: {email}")

    return render(request, 'admission.html', context)


def password_reset_view(request):
    return render(request, 'password_reset.html')


# Main Site Views
def home(request):
    recent_news = News.objects.all().order_by('-published_date')[:5]
    recent_events = Event.objects.all().order_by('-event_start_date')[:5]
    
    context = {
        'recent_news': recent_news,
        'recent_events': recent_events,
    }
    return render(request, 'index.html', context)

from django.shortcuts import render, get_object_or_404
from academics.models import Department

def department_detail(request, slug):
    department = get_object_or_404(Department, slug=slug)
    teachers = department.teachers.all()
    programs = department.programs.all()
    context = {
        'department': department,
        'teachers': teachers,
        'programs': programs,
    }
    return render(request, 'department_detail.html', context)


def about(request):
    return render(request, 'about.html')


def gallery(request):
    gallery_items = Gallery.objects.all().order_by('-date_added')
    context = {
        'gallery_items': gallery_items
    }
    return render(request, 'gallery.html', context)


from django.shortcuts import render, get_object_or_404
from announcements.models import News, Event
from django.core.paginator import Paginator
from django.utils import timezone

def news_events(request):
    # Fetch recent events (all, ordered by start date descending)
    recent_events = Event.objects.all().order_by('-event_start_date')
    
    # Paginate events (5 per page)
    events_paginator = Paginator(recent_events, 5)
    events_page_number = request.GET.get('events_page')
    events_page_obj = events_paginator.get_page(events_page_number)
    
    # Fetch recent news (all published, for pagination)
    recent_news = News.objects.filter(is_published=True).order_by('-published_date')
    
    # Paginate news (5 per page)
    news_paginator = Paginator(recent_news, 5)
    news_page_number = request.GET.get('news_page')
    news_page_obj = news_paginator.get_page(news_page_number)
    
    context = {
        'events': events_page_obj,
        'recent_news': news_page_obj,
    }
    return render(request, 'all-news-events.html', context)

def read_more_event(request, slug):
    event_detail = get_object_or_404(Event, slug=slug)
    recent_news = News.objects.filter(is_published=True).order_by('-published_date')[:5]
    recent_events = Event.objects.all().order_by('-event_start_date')[:5]
    print(f"Recent events: {recent_events}")  # Debug   
    return render(request, 'read-more-events.html', {
        'event_details': event_detail,
        'recent_news': recent_news,
        'recent_events': recent_events,
    })

def read_more_news(request, slug):
    news_detail = get_object_or_404(News, slug=slug, is_published=True)
    recent_news = News.objects.filter(is_published=True).exclude(slug=slug).order_by('-published_date')[:5]
    recent_events = Event.objects.filter(
        event_start_date__gte=timezone.now()
    ).order_by('event_start_date')[:5]
    
    return render(request, 'read-more-news.html', {
        'news_details': news_detail,
        'recent_news': recent_news,
        'recent_events': recent_events,
    })



def team(request):
    return render(request, 'team.html')


def testimonial(request):
    return render(request, 'testimonial.html')


def contact(request):
    return render(request, 'contact.html')


# Application and Admission Views
@login_required
def apply(request):
    # Check if user is verified
    if not request.user.is_active:
        messages.warning(request, 'Please verify your email address before submitting an application.')
        return redirect('admission')
        
    faculties = Faculty.objects.prefetch_related('departments')
    admission_cycle = AdmissionCycle.objects.filter(is_open=True)
    
    return render(request, 'apply.html', {
        'faculties': faculties,
        'admission_cycle': admission_cycle,
    })


@require_GET
def get_departments(request):
    faculty_id = request.GET.get('faculty_id')
    try:
        faculty = Faculty.objects.get(pk=faculty_id)
        departments = faculty.departments.all()
        
        data = {
            'departments': [
                {
                    'id': dept.id,
                    'name': dept.name,
                    'program_count': dept.programs.count()
                }
                for dept in departments
            ]
        }
        return JsonResponse(data)
    except Faculty.DoesNotExist:
        return JsonResponse({'error': 'Faculty not found'}, status=404)


@require_GET
def get_programs(request):
    department_id = request.GET.get('department_id')
    
    try:
        department = Department.objects.get(pk=department_id)
        programs = Program.objects.filter(department_id=department_id)
        data = [{
            'id': program.id,
            'name': program.name,
            'duration': program.duration_years,
            'is_open': program.admissioncycle_set.filter(is_open=True).exists()
        } for program in programs]

        return JsonResponse(data, safe=False)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)



@require_POST
def submit_application(request):
    if not request.user.is_authenticated:
        return render('admission')
    if request.method == 'POST':
        form_data = request.POST
        files = request.FILES

        try:
            # Get foreign key instances
            faculty = Faculty.objects.get(id=form_data['faculty'])
            department = Department.objects.get(id=form_data['department'])
            program = Program.objects.get(id=form_data['program'])
            user = request.user

            # Create Applicant instance
            applicant = Applicant(
                user=user,
                faculty=faculty,
                department=department,
                program=program,
                status='pending',
                applicant_photo=files.get('applicant_photo'),
                full_name=form_data['full_name'],
                religion=form_data['religion'],
                caste=form_data['caste'],
                cnic=form_data['cnic'],
                dob=form_data['dob'],
                contact_no=form_data['contact_no'],
                identification_mark=form_data.get('identification_mark', ''),
                father_name=form_data['father_name'],
                father_occupation=form_data['father_occupation'],
                father_cnic=form_data['father_cnic'],
                monthly_income=int(form_data['monthly_income']),
                relationship=form_data['relationship'],
                permanent_address=form_data['permanent_address'],
                declaration=bool(form_data.get('declaration', False))
            )
            applicant.save()

            # Handle academic qualifications
            academic_degrees = form_data.getlist('academic_degree[]')
            academic_boards = form_data.getlist('academic_board[]')
            academic_passing_years = form_data.getlist('academic_passing_year[]')
            academic_total_marks = form_data.getlist('academic_total_marks[]')
            academic_marks_obtained = form_data.getlist('academic_marks_obtained[]')
            academic_grades = form_data.getlist('academic_grade[]')
            academic_majors = form_data.getlist('academic_major[]')

            for i in range(len(academic_degrees)):
                AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=academic_degrees[i],
                    board=academic_boards[i],
                    passing_year=int(academic_passing_years[i]),
                    total_marks=int(academic_total_marks[i]),
                    marks_obtained=int(academic_marks_obtained[i]),
                    division=academic_grades[i],
                    subjects=academic_majors[i]
                )

            # Handle extra-curricular activities
            activities = form_data.getlist('activity[]')
            positions = form_data.getlist('position[]')
            achievements = form_data.getlist('achievement[]')
            activity_years = form_data.getlist('activity_year[]')

            for i in range(len(activities)):
                if activities[i]:
                    ExtraCurricularActivity.objects.create(
                        applicant=applicant,
                        activity=activities[i],
                        position=positions[i] or '',
                        achievement=achievements[i] or '',
                        activity_year=int(activity_years[i]) if activity_years[i] else None
                    )

            return redirect('application_success')

        except Exception as e:
            logger.error(f"Application submission error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


def application_success(request):
    return render(request, 'apply_successfull.html')

def my_applications(request):
    if not request.user.is_authenticated:
        return render('admission')
    if not request.user.is_authenticated:
        return render('admission')

    # Retrieve all applications for the authenticated user
    applications = Applicant.objects.filter(user=request.user).select_related('faculty', 'department', 'program')
    
    context = {
        'applications': applications
    }
    return render(request, 'my_applications.html', context)    
    

def admission(request):
    return render(request, 'admission.html')

def alumni_view(request):
    alumni_list = Alumni.objects.all().order_by('graduation_year', 'name')
    context = {
        'alumni_list': alumni_list
    }
    return render(request, 'alumni.html', context)

def office_detail(request, slug):
    office = get_object_or_404(Office, slug=slug)
    officestaff = office.staff.all()
    context = {
        'office': office,
        'officestaff': officestaff,
    }
    return render(request, 'office_detail.html', context)

# New Faculty Detail View
def faculty_detail_view(request, slug):
    faculty = get_object_or_404(Faculty, slug=slug)
    departments = faculty.departments.all()
    context = {
        'faculty': faculty,
        'departments': departments,
    }
    return render(request, 'faculty_detail.html', context)

# Email Verification View
def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True # Activate user after successful verification
        user.save()
        # Log the user in automatically after verification
        login(request, user)
        messages.success(request, 'Your email has been successfully verified! You can now submit applications.')
        return redirect('apply') # Redirect to apply page after verification
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('admission') # Redirect to admission page with error message

# Add the email verification success view
def email_verification_success(request):
    return render(request, 'email_verification_success.html')