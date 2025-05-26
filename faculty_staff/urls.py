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
    path('get-offering-type-choices/', views.get_offering_type_choices, name='get_offering_type_choices'),
    path('course-offerings/', views.course_offerings, name='course_offerings'),
    path('search-courses/', views.search_courses, name='search_courses'),
    path('search-teachers/', views.search_teachers, name='search_teachers'),
    path('get-academic-sessions/', views.get_academic_sessions, name='get_academic_sessions'),
    path('search-programs/', views.search_programs, name='search_programs'),
    path('search-semesters/', views.search_semesters, name='search_semesters'),
    path('save-course-offering/', views.save_course_offering, name='save_course_offering'),
    path('delete-course-offering/', views.delete_course_offering, name='delete_course_offering'),
    
    
    
    
    
    
    path('study-materials/', views.study_materials, name='study_materials'),
    path('upload-study-material/', views.upload_study_material, name='upload_study_material'),
    path('delete-study-material/', views.delete_study_material, name='delete_study_material'),
    path('search-course-offerings/', views.search_course_offerings, name='search_course_offerings'),
    path('assignments/', views.assignments, name='assignments'),
    path('create-assignment/', views.create_assignment, name='create_assignment'),
    path('delete-assignment/', views.delete_assignment, name='delete_assignment'),
    path('assignment-submissions/<int:assignment_id>/', views.assignment_submissions, name='assignment_submissions'),
    path('grade-submission/', views.grade_submission, name='grade_submission'),
    path('notices/', views.notices, name='notices'),
    path('post-notice/', views.post_notice, name='post_notice'),
    path('delete-notice/', views.delete_notice, name='delete_notice'),
    path('exam-results/', views.exam_results, name='exam_results'),
    path('record-exam-results/', views.record_exam_results, name='record_exam_results'),
    path('load-students-for-course/', views.load_students_for_course, name='load_students_for_course'),
    path('delete-exam-result/', views.delete_exam_result, name='delete_exam_result'),
    path('search-students/', views.search_students, name='search_students'),
]