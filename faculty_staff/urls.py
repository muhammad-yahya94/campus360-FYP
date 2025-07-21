# faculty_staff/urls.py
from django.urls import path
from . import views, auth_views


app_name = 'faculty_staff'   

urlpatterns = [

    # ========== 1. Authentication ==========
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ========== 2. Password Reset ==========
    path('password-reset/', auth_views.FacultyStaffPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.FacultyStaffPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.FacultyStaffPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.FacultyStaffPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # ========== 2. Dashboards ==========
    path('hod-dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('prof-dashboard/', views.professor_dashboard, name='professor_dashboard'),

    # ========== 3. Staff Management ==========
    path('staff-management/', views.staff_management, name='staff_management'),
    path('staff/add/', views.add_staff, name='add_staff'),
    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),

    # ========== 4. Students & Enrollment ==========
    # Students URL - handles both with and without session_id
    path('students/', views.session_students, name='session_students'),
    path('students/<int:session_id>/', views.session_students, name='session_students_by_id'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('edit-enrollment-status/', views.edit_enrollment_status, name='edit_enrollment_status'),
    path('view-students/<int:offering_id>', views.view_students, name='view_students'),
    path('student/<int:student_id>/set_role/', views.set_student_role, name='set_student_role'),

    # ========== 5. Courses & Offerings ==========
    path('add-course/', views.add_course, name='add_course'),
    path('course-offerings/', views.course_offerings, name='course_offerings'),
    path('course-offerings/get/', views.get_course_offering, name='get_course_offering'),
    path('course-offerings/edit/', views.edit_course_offering, name='edit_course_offering'),
    path('save-course-offering/', views.save_course_offering, name='save_course_offering'),
    path('delete-course-offering/', views.delete_course_offering, name='delete_course_offering'),

    # ========== 6. Timetable ==========
    path('timetable/get/', views.get_timetable_slot, name='get_timetable_slot'),
    path('timetable/edit/', views.edit_timetable_slot, name='edit_timetable_slot'),
    path('save-timetable-slot/', views.save_timetable_slot, name='save_timetable_slot'),
    path('delete-timetable-slot/', views.delete_timetable_slot, name='delete_timetable_slot'),
    path('timetable-schedule/<int:offering_id>/', views.timetable_schedule, name='timetable_schedule'),
    path('weekly-timetable/', views.weekly_timetable, name='weekly_timetable'),
    path('search-timetable-slots/', views.search_timetable_slots, name='search_timetable_slots'),
    path('my-timetable/', views.my_timetable, name='my_timetable'),
    path('timetable/replacement/create/', views.lecture_replacement_create, name='lecture_replacement_create'),
  
  
    # ========== 7. Search APIs ==========
    path('search-courses/', views.search_courses, name='search_courses'),
    path('search-teachers/', views.search_teachers, name='search_teachers'),
    path('search-venues/', views.search_venues, name='search_venues'),
    path('search-programs/', views.search_programs, name='search_programs'),
    path('search-semesters/', views.search_semesters, name='search_semesters'),
    path('search-students/', views.search_students, name='search_students'),
    path('search-course-offerings/', views.search_course_offerings, name='search_course_offerings'),
    path('get-offering-type-choices/', views.get_offering_type_choices, name='get_offering_type_choices'),
    path('get-academic-sessions/', views.get_academic_sessions, name='get_academic_sessions'),

    # ========== 8. Venue Management ==========
    path('save-venue/', views.save_venue, name='save_venue'),

    # ========== 9. Study Materials ==========
    path('study-materials/<int:offering_id>/', views.study_materials, name='study_materials'),
    path('create-study-material/', views.create_study_material, name='create_study_material'),
    path('edit-study-material/', views.edit_study_material, name='edit_study_material'),
    path('delete-study-material/', views.delete_study_material, name='delete_study_material'),

    # ========== 10. Assignments ==========
    path('assignments/<int:offering_id>/', views.assignments, name='assignments'),
    path('create-assignment/', views.create_assignment, name='create_assignment'),
    path('edit-assignment/', views.edit_assignment, name='edit_assignment'),
    path('delete-assignment/', views.delete_assignment, name='delete_assignment'),
    path('assignment-submissions/<int:assignment_id>/', views.assignment_submissions, name='assignment_submissions'),
    path('grade-submission/', views.grade_submission, name='grade_submission'),


    # ========== 12. Exam Results ==========
    path('exam-results/<int:course_offering_id>/', views.exam_results, name='exam_results'),
    path('record-exam-results/', views.record_exam_results, name='record_exam_results'),
    
    
    
    
    # ==========  student performace ==========
    path('course/<int:course_offering_id>/student/<int:student_id>/performance/', views.student_performance, name='student_performance'),
    path('student/<int:student_id>/performance/', views.student_semester_performance, name='student_semester_performance'),
 
 
 
    # ========== 13. Notice Board ==========
    path('notices/', views.notice_board, name='notice_board'),
    
    # ========== 14. Attendance ==========
    path('attendance/<int:offering_id>/', views.attendance, name='attendance'),
    path('load-students-for-course/', views.load_students_for_course, name='load_students_for_course'),
    path('record-attendance/', views.record_attendance, name='record_attendance'),
    path('load-attendance/', views.load_attendance, name='load_attendance'),
    path('edit-attendance/', views.edit_attendance, name='edit_attendance'),

    # ========== 14. Semester Management ==========
    path('semester-management/', views.semester_management, name='semester_management'),
    path('semester/add/', views.add_semester, name='add_semester'),
    path('semester/edit/', views.edit_semester, name='edit_semester'),
    path('semester/delete/', views.delete_semester, name='delete_semester'),
    # New AJAX endpoints
    path('get-programs/', views.get_programs, name='get_programs'),
    path('get-academic-sessions/', views.get_academic_sessions, name='get_academic_sessions'),

    # ========== 15. Teacher Courses ==========
    path('teacher-course-list/', views.teacher_course_list, name='teacher_course_list'),
    path('teacher/<int:teacher_id>/lectures/', views.teacher_lecture_details, name='teacher_lecture_details'),

    # ========== 16. Settings & Profile ==========
    path('settings/', views.settings, name='settings'),
    path('update_account/', views.update_account, name='update_account'),
    path('change_password/', views.change_password, name='change_password'),
    path('update_status/', views.update_status, name='update_status'),
    
    # ========== 17. Quizs ==========
    path('create-quiz/<int:course_offering_id>/', views.create_quiz, name='create_quiz'),
    path('get-quiz/<int:quiz_id>/', views.get_quiz, name='get_quiz'),

    # ========== 18. Department Funds ==========
    path('department-funds/', views.department_funds_management, name='department_funds_management'),
    path('department-funds/view/<int:fund_id>/', views.view_department_fund, name='view_department_fund'),
    path('department-funds/get-programs/', views.get_programs_fund, name='get_programs_fund'),
    path('department-funds/get-semesters/', views.get_semesters_fund, name='get_semesters_fund'),
]
