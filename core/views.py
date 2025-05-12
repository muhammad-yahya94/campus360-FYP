from django.shortcuts import render, redirect
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
                    last_name=last_name
                )
                login(request, user)
                return redirect('apply')
            except Exception as e:
                context['register_error'] = str(e)
        
        # Preserve form inputs
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
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            return redirect(request.GET.get('next', 'apply'))
        else:
            context['login_error'] = 'Invalid email or password'
            context['entered_email'] = email
            print(f"Login failed for email: {email}")  # Debug

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


def about(request):
    return render(request, 'about.html')


def gallery(request):
    return render(request, 'gallery.html')


def events(request):
    return render(request, 'all-news-events.html')


def read_more_event(request, slug):
    print(f"This is slug field: {slug}")
    event_detail = Event.objects.get(slug=slug)
    recent_news = News.objects.all().order_by('-published_date')[:5]
    recent_events = Event.objects.all().order_by('-event_start_date')[:5]
    
    return render(request, 'read-more.html', {
        'event_details': event_detail,
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
def apply(request):
    faculties = Faculty.objects.prefetch_related('departments')
    admission_cycle = AdmissionCycle.objects.filter(is_open=True)
    print(admission_cycle)
    
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
def my_applications(request):
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