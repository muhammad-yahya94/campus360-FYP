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
    path('view-applicant/<int:applicant_id>/', views.view_applicant, name='view_applicant'),
    path('verify-applicant/<int:applicant_id>/', views.verify_applicant, name='verify_applicant'),
    path('student-management/', views.student_management, name='student_management'),
    path('admission-fee/', views.admission_fee, name='admission_fee'),
    path('semester-fee/', views.semester_fee, name='semester-fee'),
    path('get_programs/', views.get_programs, name='get_programs'),
    path('get_semesters/', views.get_semesters, name='get_semesters'),
    path('get_semesters_by_roll/', views.get_semesters_by_roll, name='get_semesters_by_roll'),
    path('generate-voucher/', views.generate_voucher, name='generate_voucher'),
    path('student/generate-voucher/', views.student_generate_voucher, name='student_generate_voucher'),
    path('fee-verification/', views.fee_verification, name='fee_verification'),
    path('generate-merit-list/', views.generate_merit_list, name='generate_merit_list'),
    path('view-merit-list/<int:merit_list_id>/', views.view_merit_list, name='view_merit_list'),
    path('manage-merit-lists/', views.manage_merit_lists, name='manage_merit_lists'),
    # path('grant-admission/<极list_id>/', views.grant_admission, name='grant_admission'),
    path('grant-admission-single/<int:entry_id>/', views.grant_admission_single, name='grant_admission_single'),
    path('add-student/', views.add_student_manually, name='add_student_manually'),
    path('get-next-list-number/', views.get_next_list_number, name='get_next_list_number'),
]

