from django.urls import path
from . import views
from django.shortcuts import render

app_name = 'fee_management'

urlpatterns = [
    path('treasure-office/', views.treasure_office_view, name='treasure_office'),
    path('office-login/', views.office_login_view, name='office_login'),
    path('office-logout/', views.office_logout_view, name='office_logout'),
    path('office-dashboard/', lambda request: render(request, 'fee_management/office_dashboard.html'), name='office_dashboard'),
    path('applicant-verification/', views.applicant_verification, name='applicant_verification'),
    path('student-management/', views.student_management, name='student_management'),
    path('admission-fee/', views.admission_fee, name='admission_fee'),
path('semester-fee/', views.semester_fee, name='semester-fee'),
path('get_programs/', views.get_programs, name='get_programs'),
path('get_semesters/', views.get_semesters, name='get_semesters'),
    path('get_semesters_by_roll/', views.get_semesters_by_roll, name='get_semesters_by_roll'),
    path('generate-voucher/', views.generate_voucher, name='generate_voucher'),
    path('fee-verification/', views.fee_verification, name='fee_verification'),
] 