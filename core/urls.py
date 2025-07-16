from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    
    # News-Event-related pages
    path('news-events/', views.news_events, name='events'),
    path('event/<slug:slug>/', views.read_more_event, name='events_detail'),
    path('news/<slug:slug>/', views.read_more_news, name='news_detail'),
    
    path('departments/<slug:slug>/', views.department_detail, name='department_detail'),
    path('teacher/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    # Team and testimonial pages
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    
    # Contact and application pages
    path('contact/', views.contact, name='contact'),
    path('apply/', views.apply, name='apply'),
    path('apply/form/', views.submit_application, name='submit_application'),
    path('apply/success/', views.application_success, name='application_success'),
    path('apply/my-applications/', views.my_applications, name='my_applications'),
    path('get-session-for-program/', views.get_session_for_program, name='get_session_for_program'),
    # API endpoints
    path('api/departments/', views.get_departments, name='get_departments'),
    path('api/programs/', views.get_programs, name='get_programs'),
    
    # Admission-related pages
    path('admission/', views.admission, name='admission'),
    path('admission/login/', views.login_view, name='loginview'),
    path('admission/register/', views.register_view, name='registerview'),
    
    # Email verification
    path('verify/<str:uidb64>/<str:token>/', views.verify_email_view, name='verify_email'),
    path('email-verification-success/', views.email_verification_success, name='email_verification_success'),
    
    # Alumni page
    path('alumni/', views.alumni_view, name='alumni'),

    # Office detail page
    path('offices/<slug:slug>/', views.office_detail, name='office_detail'),

    # Faculty detail page
    path('faculties/<slug:slug>/', views.faculty_detail_view, name='faculty_detail'),
    
    # Merit list page
    path('merit-lists/', views.merit_list_view, name='merit_lists'),
    path('merit-list/pdf/',views.merit_list_pdf, name='merit_list_pdf'),
    
    path('accounts/logout/', views.logout_view, name='logout')
]