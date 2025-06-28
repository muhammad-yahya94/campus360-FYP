from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # ========== 1. Authentication ==========
    path('login/', views.student_login, name='login'),  # 1.1 Login
    path('logout/', views.logout_view, name='logout'),  # 1.2 Logout

    # ========== 2. Dashboard ==========
    path('dashboard/', views.student_dashboard, name='dashboard'),  # 2.1 Student Dashboard

    # ========== 3. Courses ==========
    path('my-courses/', views.my_courses, name='my_courses'),  # 3.1 My Courses
    path('session-courses/<int:session_id>/', views.session_courses, name='session_courses'),  # 3.2 Session Courses

    # ========== 4. Assignments & Study Material ==========
    path('assignments/', views.assignments, name='assignments'),  # 4.1 Assignments
    path('study-materials/', views.study_materials, name='study_materials'),  # 4.2 Study Materials

    # ========== 5. Notices & Results ==========
    path('notices/', views.notices, name='notices'),  # 5.1 Notices
    path('exam-results/', views.exam_results, name='exam_results'),  # 5.2 Exam Results

    # ========== 6. Timetable ==========
    path('timetable/', views.student_timetable, name='timetable'),  # 6.1 Student Timetable

    # ========== 7. Attendance ==========
    path('attendance/', views.student_attendance, name='attendance'),  # 7.1 View Attendance
    path('attendance-stats/', views.student_attendance_stats, name='attendance_stats'),  # 7.2 Attendance Stats

    # ========== 8. Quizzes ==========
    path('solve-quiz/<int:course_offering_id>/', views.solve_quiz, name='solve_quiz'),  # 8.1 Solve Quiz
    path('get-quiz/<int:quiz_id>/', views.get_quiz, name='get_quiz'),  # 8.2 Get Quiz
    path('submit-quiz/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),  # 8.3 Submit Quiz
]
