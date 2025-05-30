from django.urls import path
from . import views

app_name = 'students'
urlpatterns = [
    path('login/', views.student_login, name='login'),
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('session-courses/<int:session_id>/', views.session_courses, name='session_courses'),
    path('assignments/', views.assignments, name='assignments'),
    path('study-materials/', views.study_materials, name='study_materials'),
    path('notices/', views.notices, name='notices'),
    path('exam-results/', views.exam_results, name='exam_results'),
    path('logout/', views.logout_view, name='logout'),
]