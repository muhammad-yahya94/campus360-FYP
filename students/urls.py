from django.urls import path
from . import views
from . import auth_views


app_name = 'students'  

urlpatterns = [
    # ========== 1. Authentication ==========
    path('login/', views.student_login, name='login'),  # 1.1 Login
    path('logout/', views.logout_view, name='logout'),  # 1.2 Logout
    
    # ========== 2. Password Reset ==========
    path('password-reset/', auth_views.StudentPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.StudentPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.StudentPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.StudentPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # ========== 2. Dashboard ==========
    path('dashboard/', views.student_dashboard, name='dashboard'),  # 2.1 Student Dashboard

    # ========== 3. Courses ==========
    path('my-courses/', views.my_courses, name='my_courses'),  # 3.1 My Courses


    # ========== 4. Assignments & Study Material ==========
    path('assignments/<int:course_offering_id>/', views.assignments, name='assignments'),
    path('submit_assignment/<int:assignment_id>/', views.submit_assignment, name='submit_assignment'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('study-materials/<int:course_offering_id>/', views.study_materials, name='study_materials'),

    # ========== 5. Notices & Results ==========
    path('notices/', views.notices, name='notices'),  # 5.1 Notices
    path('exam-results/', views.exam_results, name='exam_results'),  # 5.2 Exam Results
    path('exam_slip/', views.exam_slip, name='exam_slip'),
    
    # ========== 6. Timetable ==========  
    path('timetable/', views.student_timetable, name='timetable'),  # 6.1 Student Timetable

    # ========== 7. Attendance ==========
    path('attendance/<int:course_offering_id>/', views.student_attendance, name='attendance'),  # 7.1 View Attendance
    path('attendance-stats/', views.student_attendance_stats, name='attendance_stats'),  # 7.2 Attendance Stats

    # ========== 8. Quizzes ==========
    path('solve-quiz/<int:course_offering_id>/', views.solve_quiz, name='solve_quiz'),  # 8.1 Solve Quiz
    path('get-quiz/<int:quiz_id>/', views.get_quiz, name='get_quiz'),  # 8.2 Get Quiz
    path('submit-quiz/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),  # 8.3 Submit Quiz

    # ========== 9. Profile & Settings ==========
    path('profile/', views.profile_view, name='profile'),  # 9.1 Profile Page
    path('settings/', views.settings_view, name='settings'),  # 9.2 Settings Page
    path('settings/update-account/', views.update_account, name='update_account'),  # 9.3 Update Account
    path('settings/change-password/', views.change_password, name='change_password'),  # 9.4 Change Password
    
    # ========== 10. Online IDE ==========
    path('ide/', views.ide, name='ide'),  # 10.1 Online Code Editor
    
    # ========== 11. Semester Fees ==========
    path('fees/', views.semester_fees, name='semester_fees'),  # 11.1 Semester Fees
    
    path('fund_payments/', views.fund_payments, name='fund_payments'),
]
