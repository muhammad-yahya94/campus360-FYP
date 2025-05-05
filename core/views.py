from django.shortcuts import render , redirect
from announcements.models import Event , News
from academics.models import Faculty , Department , Program
from admissions.models import AdmissionCycle
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from users.models import CustomUser
from django.contrib import messages
from django.http import HttpResponse 


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
            # CHANGE: Use 'email' instead of 'username' to match your form
            email = request.POST.get('email')  # This matches your form field name
            password = request.POST.get('password')
            remember_me = request.POST.get('remember_me') == 'on'

            # CHANGE: Authenticate using email
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                return redirect(request.GET.get('next', 'apply'))
            else:
                context['login_error'] = 'Invalid email or password'
                # Preserve the entered email
                context['entered_email'] = email
                print(f"Login failed for email: {email}")  # Debug
    return render(request, 'admission.html', context)


def password_reset_view(request):
    return render(request, 'password_reset.html')




def home(request):
    recent_news = News.objects.all().order_by('-published_date')[:5]
    recent_events = Event.objects.all().order_by('-event_start_date')[:5]
    print(recent_news)
    
    
    context = {
        'recent_news' : recent_news,
        'recent_events' : recent_events,
    }
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')

def gallery(request):
    return render(request, 'gallery.html')

def events(request):
    return render(request, 'all-news-events.html')

def read_more_event(reques , slug):
    print(f'this is slug field   -- {slug}')
    event_detail = Event.objects.get(slug=slug)
    recent_news = News.objects.all().order_by('-published_date')[:5]
    recent_events = Event.objects.all().order_by('-event_start_date')[:5]
    return render(reques, 'read-more.html' , {
        'event_details':event_detail,
        'recent_news':recent_news,
        'recent_events':recent_events,
    })


def team(request):
    return render(request, 'team.html')

def testimonial(request):
    return render(request, 'testimonial.html')

def contact(request):
    return render(request, 'contact.html')


def apply(request):
    faculties = Faculty.objects.prefetch_related('departments')
    admissioncycle=AdmissionCycle.objects.filter(is_open=True)
    print(admissioncycle)
    return render(request, 'apply.html', {
        'faculties': faculties,
    })


# views.py


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


import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from admissions.models import Faculty, Department, Program, Applicant, AcademicQualification, ExtraCurricularActivity

logger = logging.getLogger(__name__)

@login_required
@require_POST
def submit_application(request):
    try:
        # Log form data line by line
        logger.debug("Received Form Data:")
        for key, value in request.POST.items():
            logger.debug("%s: %s", key, value)
        for key, file in request.FILES.items():
            logger.debug("%s: {name: %s, size: %d, content_type: %s}", 
                        key, file.name, file.size, file.content_type)

        # Get Faculty, Department, Program
        faculty = Faculty.objects.get(id=request.POST['faculty'])
        department = Department.objects.get(id=request.POST['department'], faculty=faculty)
        program = Program.objects.get(id=request.POST['program'], department=department)

        # Create Applicant
        applicant = Applicant(
            user=request.user,
            faculty=faculty,
            department=department,
            program=program,
            applicant_photo=request.FILES['applicant_photo'],
            full_name=request.POST['full_name'],
            religion=request.POST['religion'],
            caste=request.POST['caste'],
            cnic=request.POST['cnic'],
            dob=datetime.strptime(request.POST['dob'], '%Y-%m-%d').date(),
            contact_no=request.POST['contact_no'],
            identification_mark=request.POST.get('identification_mark', ''),
            father_name=request.POST['father_name'],
            father_occupation=request.POST['father_occupation'],
            father_cnic=request.POST['father_cnic'],
            monthly_income=int(request.POST['monthly_income']),
            relationship=request.POST['relationship'],
            permanent_address=request.POST['permanent_address'],
            declaration=request.POST['declaration'] == 'on'
        )
        applicant.save()

        # Create Academic Qualifications
        for level in ['matric', 'inter']:
            qualification = AcademicQualification(
                applicant=applicant,
                level=request.POST[f'{level}_level'],
                exam_passed=request.POST[f'{level}_exam_passed'],
                passing_year=int(request.POST[f'{level}_passing_year']),
                roll_no=request.POST[f'{level}_roll_no'],
                marks_obtained=int(request.POST[f'{level}_marks_obtained']),
                total_marks=int(request.POST[f'{level}_total_marks']),
                division=request.POST[f'{level}_division'],
                subjects=request.POST[f'{level}_subjects'],
                institute=request.POST[f'{level}_institute'],
                board=request.POST[f'{level}_board']
            )
            qualification.save()

        # Create Extra Curricular Activity (if provided)
        if any(request.POST.get(field) for field in ['activity', 'position', 'achievement', 'activity_year']):
            activity = ExtraCurricularActivity(
                applicant=applicant,
                activity=request.POST.get('activity', ''),
                position=request.POST.get('position', ''),
                achievement=request.POST.get('achievement', ''),
                activity_year=int(request.POST['activity_year']) if request.POST.get('activity_year') else None
            )
            activity.save()

        redirect('application_success')

    except Exception as e:
        logger.error("Error processing form: %s", str(e))
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
        
        
        
def application_success(request):
    return render(request, 'apply_successfull.html')       
        
        
        
def admission(request):
    # views.py

    return render(request, 'admission.html')

