from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from announcements.models import Event, News
from academics.models import Faculty, Department, Program
from admissions.models import AcademicSession, AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity
from users.models import CustomUser
from payment.models import Payment 
import json   
import logging
from datetime import datetime  
from site_elements.models import Alumni, Gallery
from faculty_staff.models import Teacher, Office, OfficeStaff
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

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


def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    return render(request, 'teacher_detail.html', {'teacher': teacher})



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
    admission_cycles = AdmissionCycle.objects.filter(is_open=True).select_related('session', 'program')
    
    # Prepare context with faculties and admission cycles
    context = {
        'faculties': faculties,
        'admission_cycles': admission_cycles,
    }
    
    return render(request, 'apply.html', context)

def get_session_for_program(request):
    """
    View to retrieve the academic session for a given program based on an open admission cycle.
    Only accessible to logged-in users.
    Returns JSON response with session details or an error message.

    Query Parameter:
        program_id (int): The ID of the program to fetch the session for.

    Response:
        - success: boolean indicating if the request was successful
        - session: dict with id and name if successful, or None
        - message/error: string with error message if unsuccessful
        - status: HTTP status code
    """
    # Extract program_id from query parameters
    program_id = request.GET.get('program_id')

    # Validate program_id
    if not program_id:
        return JsonResponse({'success': False, 'error': 'Program ID is required.'}, status=400)

    try:
        # Convert program_id to integer
        program_id = int(program_id)

        # Fetch the open AdmissionCycle for the given program
        admission_cycle = AdmissionCycle.objects.filter(
            program_id=program_id,
            is_open=True
        ).select_related('session').first()

        if not admission_cycle or not admission_cycle.session:
            return JsonResponse({
                'success': False,
                'message': 'No open session found for this program.'
            })

        # Get the associated session
        session = admission_cycle.session

        # Prepare response with session details
        session_data = {
            'id': session.id,
            'name': session.name  # Adjust 'name' based on your AcademicSession model
        }

        return JsonResponse({
            'success': True,
            'session': session_data
        })

    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid program ID format.'}, status=400)
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'Program or session not found.'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
    try:
        # Get the session ID from the form (added via hidden input in the template)
        session_id = request.POST.get('session')
        if not session_id:
            raise ValueError("Academic session is required.")

        # Fetch the session object
        session = AcademicSession.objects.get(id=session_id)
        
        # # Check if an applicant already exists for this user and session (due to OneToOneField)
        # existing_applicant = Applicant.objects.filter(user=request.user, session=session).first()
        # if existing_applicant:
        #     raise ValueError("You have already submitted an application for this session.")

        # Create Applicant
        applicant = Applicant.objects.create(
            user=request.user,
            session=session,
            faculty_id=request.POST.get('faculty'),
            department_id=request.POST.get('department'),
            program_id=request.POST.get('program'),
            status='pending',
            full_name=request.POST.get('full_name'),
            religion=request.POST.get('religion'),
            caste=request.POST.get('caste'),
            cnic=request.POST.get('cnic'),
            dob=request.POST.get('dob'),
            contact_no=request.POST.get('contact_no'),
            identification_mark=request.POST.get('identification_mark'),
            gender=request.POST.get('gender'),
            father_name=request.POST.get('father_name'),
            father_occupation=request.POST.get('father_occupation'),
            father_cnic=request.POST.get('father_cnic'),
            monthly_income=request.POST.get('monthly_income'),
            relationship=request.POST.get('relationship'),
            permanent_address=request.POST.get('permanent_address'),
            shift=request.POST.get('shift'),
            declaration=request.POST.get('declaration') == 'on'
        )

        # Handle applicant photo
        if 'applicant_photo' in request.FILES:
            applicant.applicant_photo = request.FILES['applicant_photo']
            applicant.save()

        # Handle Academic Qualifications
        academic_degrees = request.POST.getlist('academic_degree[]')
        academic_boards = request.POST.getlist('academic_board[]')
        academic_passing_years = request.POST.getlist('academic_passing_year[]')
        academic_total_marks = request.POST.getlist('academic_total_marks[]')
        academic_marks_obtained = request.POST.getlist('academic_marks_obtained[]')
        academic_grades = request.POST.getlist('academic_grade[]')
        academic_majors = request.POST.getlist('academic_major[]')
        academic_certificates = request.FILES.getlist('academic_certificate[]')

        for i in range(len(academic_degrees)):   
            if academic_degrees[i]:  # Only create if degree is not empty
                qualification = AcademicQualification.objects.create(
                    applicant=applicant,
                    exam_passed=academic_degrees[i],
                    board=academic_boards[i],
                    passing_year=academic_passing_years[i],
                    total_marks=academic_total_marks[i] if academic_total_marks[i] else None,
                    marks_obtained=academic_marks_obtained[i] if academic_marks_obtained[i] else None,
                    division=academic_grades[i],
                    subjects=academic_majors[i]
                )
                # Handle certificate file if provided
                if i < len(academic_certificates) and academic_certificates[i]:
                    qualification.certificate_file = academic_certificates[i]
                    qualification.save()

        # Handle Extra Curricular Activities
        activities = request.POST.getlist('activity[]')
        positions = request.POST.getlist('position[]')
        achievements = request.POST.getlist('achievement[]')
        activity_years = request.POST.getlist('activity_year[]')
        activity_certificates = request.FILES.getlist('certificate_file[]')

        for i in range(len(activities)):
            if activities[i]:  # Only create if activity is not empty
                activity = ExtraCurricularActivity.objects.create(
                    applicant=applicant,
                    activity=activities[i],
                    position=positions[i],
                    achievement=achievements[i],
                    activity_year=activity_years[i] if activity_years[i] else None
                )
                # Handle certificate file if provided
                if i < len(activity_certificates) and activity_certificates[i]:
                    activity.certificate_file = activity_certificates[i]
                    activity.save()

        messages.success(request, 'Application submitted successfully!')
        return redirect('application_success')

    except Exception as e:
        messages.error(request, f'Error submitting application: {str(e)}')
        return redirect('apply')


@login_required
def application_success(request):
    logger.info(f"Application success page accessed for user {request.user.id}")
    show_payment_link = False
    applicant = None
    payment = None
    if request.user.is_authenticated:
        try:
            # Get the most recent Applicant for the user
            applicants = Applicant.objects.filter(user=request.user).order_by('-applied_at')
            if not applicants.exists():
                logger.warning(f"No Applicant record found for user {request.user.id}")
                show_payment_link = True
            else:
                applicant = applicants.first()
                # Check for payment status using the user, not the applicant
                payment = Payment.objects.filter(user=request.user).order_by('-created_at').first()
                if payment and payment.status != 'paid':
                    show_payment_link = True
                elif not payment:
                    # If no payment record exists, assume payment is needed
                    show_payment_link = True
        except Exception as e:
            logger.error(f"Error retrieving Applicant or Payment: {str(e)}", exc_info=True)
            show_payment_link = True  # Fallback to show payment link on error
    context = {
        'show_payment_link': show_payment_link,
        'applicant': applicant,
        'payment': payment
    }
    return render(request, 'apply_successfull.html', context)





@login_required
def my_applications(request):
    logger.info(f"My applications page accessed for user {request.user.id}")
    
    # Retrieve all applications for the authenticated user
    applications = Applicant.objects.filter(user=request.user).select_related('faculty', 'department', 'program')
    
    # Prepare a list of applications with their payment status
    application_data = []
    for application in applications:
        payment = Payment.objects.filter(user=application).order_by('-created_at').first()
        payment_status = {
            'is_paid': payment.status == 'paid' if payment else False,
            'status_text': 'Paid' if payment and payment.status == 'paid' else 'Not Paid',
            'payment': payment
        }
        application_data.append({
            'application': application,
            'payment_status': payment_status
        })
    
    context = {
        'applications': application_data
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

def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True  # Activate user after successful verification
        user.save()
        # Log the user in automatically after verification
        login(request, user)
        messages.success(request, 'Your email has been successfully verified! You can now submit applications.')
        return render(request, 'email_verification_result.html', {'verification_success': True})
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return render(request, 'email_verification_result.html', {'verification_success': False})

# Add the email verification success view
def email_verification_success(request):
    return render(request, 'email_verification_success.html')



@login_required
def logout_view(request):
    """
    Logs out the current user and redirects to the home page.
    """
    user = request.user
    logger.info(f'User logout: user={user.first_name}, id={user.id}')
    logout(request)
    return HttpResponseRedirect(reverse('home'))

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from admissions.models import AcademicSession
from admissions.models import Applicant
from academics.models import Department, Program
from fee_management.models import   MeritList , MeritListEntry

def merit_list_view(request):
    sessions = AcademicSession.objects.all()
    selected_session = request.GET.get('session')
    selected_department = request.GET.get('department')
    selected_program = request.GET.get('program')
    selected_shift = request.GET.get('shift')
    
    departments = None
    programs = None
    shifts = None
    merit_lists = None
    page_obj = None
    
    if selected_session:
        departments = Department.objects.filter(
            id__in=Applicant.objects.filter(session_id=selected_session).values_list('department_id', flat=True)
        ).distinct()
        
        if selected_department:
            programs = Program.objects.filter(
                department_id=selected_department,
                id__in=Applicant.objects.filter(
                    session_id=selected_session,
                    department_id=selected_department
                ).values_list('program_id', flat=True)
            ).distinct()
            if selected_program:
                shifts = MeritList.objects.filter(
                    program_id=selected_program
                ).values_list('shift', flat=True).distinct()
                if selected_shift:
                    merit_lists = MeritList.objects.filter(
                        academic_session_id=selected_session,
                        program_id=selected_program,
                        shift=selected_shift
                    ).order_by('list_number')
                    if merit_lists.exists():
                        paginator = Paginator(merit_lists, 1)  # 1 merit list per page
                        page_number = request.GET.get('page', 1)
                        try:
                            page_obj = paginator.page(page_number)
                        except (PageNotAnInteger, EmptyPage):
                            page_obj = paginator.page(1)  # Default to first page
                    else:
                        print("No merit lists found for the selected criteria.")
    
    print(f"Selected session: {selected_session}")
    print(f"Selected department: {selected_department}")
    print(f"Selected program: {selected_program}")
    print(f"Selected shift: {selected_shift}")
    print(f"merit_lists: {merit_lists}")
    print(f"page_obj: {page_obj}")
    if page_obj:
        for merit_list in page_obj:
            print(f"Merit List #{merit_list.list_number} entries: {merit_list.entries.count()}")

    context = {
        'sessions': sessions,
        'departments': departments,
        'programs': programs,
        'shifts': shifts,
        'page_obj': page_obj,
        'selected_session': selected_session,
        'selected_department': selected_department,
        'selected_program': selected_program,
        'selected_shift': selected_shift,
    }
    return render(request, 'merit_lists.html', context)

def merit_list_pdf(request):
    session = request.GET.get('session')
    department = request.GET.get('department')
    program = request.GET.get('program')
    shift = request.GET.get('shift')
    list_number = request.GET.get('list_number')

    # Get the specific merit list for this program, shift, and list number
    merit_list = MeritList.objects.filter(
        program_id=program,
        shift=shift,
        list_number=list_number
    ).first()

    if not merit_list:
        return HttpResponse("No active merit list found for this program and shift")

    # Get all entries for this merit list ordered by position
    entries = MeritListEntry.objects.filter(
        merit_list=merit_list
    ).select_related('applicant', 'qualification_used').order_by('merit_position')

    # Fetch related objects for display names
    department_obj = Department.objects.filter(id=department).first()
    program_obj = Program.objects.filter(id=program).first()

    context = {
        'applicants': [entry.applicant for entry in entries],
        'merit_entries': entries,
        'department': department_obj.name if department_obj else '',
        'program': program_obj.name if program_obj else '',
        'shift': shift,
        'total_candidates': entries.count(),
        'valid_until': merit_list.valid_until.strftime('%d-%b-%Y'),
        'current_date': datetime.now().strftime('%d-%b-%Y'),
        'merit_list': merit_list,
    }

    html = render_to_string('merit_list_pdf_template.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="merit_list.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response