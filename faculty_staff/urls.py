# faculty_staff/urls.py
from django.urls import path
from . import views

app_name = 'faculty_staff'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('hod-dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('prof-dashboard/', views.professor_dashboard, name='professor_dashboard'),
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
    path('search-venues/', views.search_venues, name='search_venues'),
    path('save-venue/', views.save_venue, name='save_venue'),
    path('course-offerings/get/', views.get_course_offering, name='get_course_offering'),
    path('course-offerings/edit/', views.edit_course_offering, name='edit_course_offering'),
    path('timetable/get/', views.get_timetable_slot, name='get_timetable_slot'),
    path('timetable/edit/', views.edit_timetable_slot, name='edit_timetable_slot'),
    path('save-timetable-slot/', views.save_timetable_slot, name='save_timetable_slot'),
    path('delete-timetable-slot/', views.delete_timetable_slot, name='delete_timetable_slot'),
    path('timetable-schedule/<int:offering_id>/', views.timetable_schedule, name='timetable_schedule'),
    
    path('weekly-timetable/', views.weekly_timetable, name='weekly_timetable'),
    
    path('my-timetable/', views.my_timetable, name='my_timetable'),
    
    # New URLs for study materials
    path('study-materials/', views.study_materials, name='study_materials'),
    path('create-study-material/', views.create_study_material, name='create_study_material'),
    path('edit-study-material/', views.edit_study_material, name='edit_study_material'),
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
    
    
    path('teacher-course-list/', views.teacher_course_list, name='teacher_course_list'),
    
    
    
    
    path('attendance/', views.attendance, name='attendance'),
    path('record-attendance/', views.record_attendance, name='record_attendance'),
    path('load-attendance/', views.load_attendance, name='load_attendance'),
    path('edit-attendance/', views.edit_attendance, name='edit_attendance'),
    
    
    
    
    
    
    
    path('semester-management/', views.semester_management, name='semester_management'),
    path('semester/add/', views.add_semester, name='add_semester'),
    path('semester/edit/', views.edit_semester, name='edit_semester'),
    path('semester/delete/', views.delete_semester, name='delete_semester'),
    
    
    path('view-students/', views.view_students, name='view_students'),
]