# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('events/', views.events, name='events'),
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('contact/', views.contact, name='contact'),
    path('admission/', views.admission, name='admission'),
]
