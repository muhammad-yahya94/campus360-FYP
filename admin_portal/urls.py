# from django.contrib import admin
# from django.urls import path
# from django.contrib.auth.views import LogoutView
# from . import views


# urlpatterns = [
#     path('login/', views.admin_login , name='admin-login'),
#     path('dashboard/', views.dashboard , name='admin-dashboard'),
#     path('staff/', views.admin_staff , name='admin-staff'),
#     path('edit-staff/<int:id>/', views.update_staff, name='edit_staff'),
#     path('delete-staff/<int:id>/', views.delete_staff, name='delete_staff'),
#     path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
#     path('set-password/', views.set_password, name='set_password'),
#     path('settings/', views.admin_settings , name='admin-settings'),
#     path('settings/change-password/', views.change_password, name='admin_change_password'),
#     path('department/', views.admin_departments , name='admin-department'),
#     path('content-management/', views.content_management , name='content-management'),
 
#     path('logout/', views.custom_logout, name='custom_logout'), 

# ]







from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    # Authentication URLs
    path('login/', views.admin_login , name='admin-login'),
    
    # Custom Profile Update URL
    path('update-profile/', views.update_profile, name='update_profile'),
    
    # Admin Panel Pages
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('departments/', views.departments, name='departments'),
    path('events/', views.events, name='events'),
    path('faculties/', views.faculties, name='faculties'),
    path('news/', views.news, name='news'),
    path('roles/', views.roles, name='roles'),
    path('slider/', views.slider, name='slider'),
    path('staff/', views.staff, name='staff'),
    path('change-password/', views.change_password, name='change_password'),
    
    
    path('logout/', views.logout_view, name='logout'),
    # Error Pages
    path('invalid-link/', views.invalid_link, name='invalid_link'),
]