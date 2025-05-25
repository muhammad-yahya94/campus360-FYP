# faculty_staff/urls.py
from django.urls import path
from . import views

app_name = 'faculty_staff'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('staff-management/', views.staff_management, name='staff_management'),
    path('staff/add/', views.add_staff, name='add_staff'),
    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('session-students/<int:session_id>/', views.session_students, name='session_students'),
    path('add-course/', views.add_course, name='add_course'),
    path('course-offerings/', views.course_offerings, name='course_offerings'),
    path('search-courses/', views.search_courses, name='search_courses'),
    path('search-teachers/', views.search_teachers, name='search_teachers'),
    path('search-programs/', views.search_programs, name='search_programs'),
    path('search-semesters/', views.search_semesters, name='search_semesters'),
    path('save-course-offering/', views.save_course_offering, name='save_course_offering'),
    path('delete-course-offering/', views.delete_course_offering, name='delete_course_offering'),
]