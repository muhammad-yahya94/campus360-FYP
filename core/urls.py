from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    
    # Event-related pages
    path('events/', views.events, name='events'),
    path('event/<slug:slug>/', views.read_more_event, name='events_detail'),
    
    # Team and testimonial pages
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    
    # Contact and application pages
    path('contact/', views.contact, name='contact'),
    path('apply/', views.apply, name='apply'),
    path('apply/form/', views.submit_application, name='submit_application'),
    path('apply/success/', views.application_success, name='application_success'),
    path('apply/my-applications/', views.my_applications, name='my_applications'),
    
    # API endpoints
    path('api/departments/', views.get_departments, name='get_departments'),
    path('api/programs/', views.get_programs, name='get_programs'),
    
    # Admission-related pages
    path('admission/', views.admission, name='admission'),
    path('admission/login/', views.login_view, name='loginview'),
    path('admission/register/', views.register_view, name='registerview'),
]
