from django.urls import path, include
from . import views
from .auth_views import (
    OfficePasswordResetView, OfficePasswordResetDoneView,
    OfficePasswordResetConfirmView, OfficePasswordResetCompleteView
)
from django.shortcuts import render

app_name = 'fee_management'

urlpatterns = [
    # ========== 1. Authentication & Dashboard ==========
    path('treasure-office/', views.treasure_office_view, name='treasure_office'),  # 1.1 Treasure Office Home
    path('office-login/', views.office_login_view, name='office_login'),  # 1.2 Office Login
    path('office-logout/', views.office_logout_view, name='office_logout'),  # 1.3 Office Logout
    path('office-dashboard/', lambda request: render(request, 'fee_management/office_dashboard.html'), name='office_dashboard'),  # 1.4 Office Dashboard
    
    # ========== 2. Applicant Management ==========
    path('applicant-verification/', views.applicant_verification, name='applicant_verification'),  # 2.1 Applicant Verification List
    path('view-applicant/<int:applicant_id>/', views.view_applicant, name='view_applicant'),  # 2.2 View Applicant Details
    path('verify-applicant/<int:applicant_id>/', views.verify_applicant, name='verify_applicant'),  # 2.3 Verify Applicant
    
    # ========== 3. Student Management ==========
    path('student-management/', views.student_management, name='student_management'),  # 3.1 Student Management
    # path('add-student/', views.add_student_manually, name='add_student_manually'),  # 3.2 Add Student (Commented Out)
    #=========== Results ===================
    path('results/', views.results, name='results'),  # 3.3 Results
    # ========== 4. Fee Management ==========
 # 4.1 Admission Fee
    path('semester-fee/', views.semester_fee, name='semester-fee'),  # 4.2 Semester Fee
    path('fee-verification/', views.fee_verification, name='fee_verification'),  # 4.3 Fee Verification
    
    # ========== 5. Voucher Management ==========
    path('generate-voucher/', views.generate_voucher, name='generate_voucher'),  # 5.1 Generate Voucher (Admin)
    path('student/generate-voucher/', views.student_generate_voucher, name='student_generate_voucher'),  # 5.2 Student Voucher Generation
    
    # ========== 6. Merit List Management ==========
    path('generate-merit-list/', views.generate_merit_list, name='generate_merit_list'),  # 6.1 Generate Merit List
    path('view-merit-list/<int:merit_list_id>/', views.view_merit_list, name='view_merit_list'),  # 6.2 View Merit List
    path('manage-merit-lists/', views.manage_merit_lists, name='manage_merit_lists'),  # 6.3 Manage Merit Lists
    path('grant-admission-single/<int:entry_id>/', views.grant_admission_single, name='grant_admission_single'),  # 6.4 Grant Admission (Single)
    path('get-next-list-number/', views.get_next_list_number, name='get_next_list_number'),  # 6.5 Get Next List Number
    
    # ========== 7. AJAX Endpoints ==========
    path('get_programs/', views.get_programs, name='get_programs'),  # 7.1 Get Programs (AJAX)
    path('get_semesters/', views.get_semesters, name='get_semesters'),  # 7.2 Get Semesters (AJAX)
    path('get_semesters_by_roll/', views.get_semesters_by_roll, name='get_semesters_by_roll'),  # 7.3 Get Semesters by Roll (AJAX)
    
    
    
    # ========= 8. course enrollment ========
    path('repeat-course-enrollment/', views.manual_course_enrollment, name='manual_course_enrollment'),
    
    # ========== 9. Password Reset ==========
    path('password-reset/', OfficePasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', OfficePasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', OfficePasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', OfficePasswordResetCompleteView.as_view(), name='password_reset_complete'),
] 