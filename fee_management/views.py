import os
import tempfile
import subprocess
import logging
from django.urls import reverse 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from faculty_staff.models import OfficeStaff, Office
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from .models import SemesterFee, FeeType, FeeVoucher, StudentFeePayment, FeeToProgram, MeritList, MeritListEntry
from courses.models import CourseOffering, Course, ExamResult
from students.models import Student
# from admissions.models import Applicant, AcademicSession, AcademicQualification, ExtraCurricularActivity
from academics.models import Program, Semester  # Added Semester import
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction
from students.models import StudentSemesterEnrollment, CourseEnrollment
from .forms import OfficerUpdateForm, OfficerPasswordChangeForm 
from .models import SemesterFee, FeeType, FeeVoucher, StudentFeePayment, FeeToProgram
from students.models import Student
from academics.models import Program, Semester
from admissions.models import AcademicSession
from django.db.models import Q
import json
from django.views.decorators.http import require_http_methods
from admissions.models import AcademicSession
from fee_management.models import FeeToProgram
from courses.models import CourseOffering
from faculty_staff.models import Office, OfficeStaff
from students.models import Student
from decimal import Decimal
from django import forms
from django.db.models import Q
from datetime import date, datetime, timedelta
import os
import tempfile
import subprocess
import json  # Added json import

# Create your views here.

from django.db.models import Q, F
from django.utils.timezone import now
from django.utils import timezone
from datetime import date, datetime, timedelta ,timezone
from urllib.parse import urlencode 
from admissions.models import AcademicSession
from payment.models import Payment
from django.forms import modelformset_factory
# from admissions.forms import  AcademicQualificationForm, ExtraCurricularActivityForm
from academics.models import Department
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, date
from .models import Program, Applicant,AcademicSession, MeritList, MeritListEntry
from django.db.models import F
from dateutil import parser
# Added json import

# Create your views here.

def treasure_office_view(request):
    # Get the Treasure Office and its staff
    try:
        office = Office.objects.prefetch_related('staff__user').get(slug='treasure-office')
        staff_members = office.staff.all()
    except Office.DoesNotExist:
        office = None
        staff_members = []
    return render(request, 'fee_management/treasure_office.html', {
        'office': office,
        'staff_members': staff_members,
    })

def office_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email, password)
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            try:
                officestaff_profile = user.officestaff_profile
                login(request, user)
                messages.success(request, 'Login successful! Welcome, Office Staff.')
                return redirect('fee_management:office_dashboard')
            except OfficeStaff.DoesNotExist:
                messages.error(request, 'You do not have Office Staff access.')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'fee_management/office_login.html')

@login_required
def office_logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('fee_management:office_login')

def is_officestaff(user):
    try:
        return hasattr(user, 'officestaff_profile')
    except Exception:
        return False

def is_student(user):
    try:
        return hasattr(user, 'student_profile')
    except Exception:
        return False

def office_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not is_officestaff(request.user):
            messages.error(request, 'You do not have Office Staff access.')
            return redirect('fee_management:office_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@office_required
def applicant_verification(request):
    # Get applicants who have at least one successful payment
    applicants = Applicant.objects.filter(
        payment__status='paid'
    ).select_related('program', 'department', 'faculty').distinct()
    
    # Get query parameters
    program_id = request.GET.get('program', '')
    shift = request.GET.get('shift', '')
    sort = request.GET.get('sort', '')
    search = request.GET.get('search', '')
    per_page = request.GET.get('per_page', '10')

    # Apply filters
    if program_id:
        try:
            applicants = applicants.filter(program__id=int(program_id))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid program selected.')
    if shift:
        applicants = applicants.filter(shift__iexact=shift.lower())
    if search:
        applicants = applicants.filter(full_name__icontains=search.strip())

    # Apply sorting
    valid_sort_fields = ['full_name', '-full_name', 'program_name', '-program_name', 'shift', '-shift']
    if sort in valid_sort_fields:
        applicants = applicants.order_by(sort)
    else:
        applicants = applicants.order_by('full_name')

    # Pagination
    try:
        per_page = int(per_page)
        if per_page not in [25, 50,100]:
            per_page = 100
    except (ValueError, TypeError):
        per_page = 50
    paginator = Paginator(applicants, per_page)
    page_number = request.GET.get('page',"1")
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)

    programs = Program.objects.all()

    context = {
        'applicants': page_obj,
        'programs': programs,
        'selected_program': program_id,
        'selected_shift': shift,
        'selected_sort': sort,
        'search_query': search,
        'per_page': str(per_page),
    }
    return render(request, 'fee_management/applicant_verification.html', context)

@office_required
def verify_applicant(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        valid_statuses = ['accepted', 'rejected']
        if status in valid_statuses:
            applicant.status = status
            if status == 'rejected':
                applicant.rejection_reason = rejection_reason
            else:
                applicant.rejection_reason = ''
            applicant.save()
            messages.success(request, f'Applicant {applicant.full_name} {status} successfully.')
        else:
            messages.error(request, 'Invalid status selected.')

        # Redirect back to the applicant detail page
        return redirect('fee_management:view_applicant', applicant_id=applicant_id)

    return redirect('fee_management:view_applicant', applicant_id=applicant_id)


@office_required
def view_applicant(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id)
    qualifications = applicant.academic_qualifications.all()
    
    # Get payment details for this applicant
    payments = Payment.objects.filter(user=applicant)
    
    # Get extracurricular activities for this applicant
    # (Assuming ExtracurricularActivity model exists with FK to Applicant)
    try:
        from admissions.models import ExtracurricularActivity
        extracurriculars = ExtracurricularActivity.objects.filter(applicant=applicant)
    except ImportError:
        extracurriculars = None
    
    return render(request, 'fee_management/applicant_detail.html', {
        'applicant': applicant,
        'qualifications': qualifications,
        'payments': payments,
        'extracurriculars': extracurriculars
    })
@office_required
def student_management(request):
    return render(request, 'fee_management/student_management.html')







def calculate_grade(percentage):
    """Calculate grade based on percentage according to the provided conversion table."""
    if percentage is None:
        return 'N/A'
    percentage = float(percentage)
    if percentage >= 85:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 75:
        return 'B+'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 65:
        return 'C+'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


from django.db.models import Q, F
from students.models import Student
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)
from collections import defaultdict
import math

def calculate_grade(percentage):
    """Calculate grade based on percentage."""
    if percentage is None:
        return 'F'
    percentage = float(percentage)
    if percentage >= 85:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'

@login_required
def results(request):
    # Initialize context with default values
    context = {
        'student': None,
        'semester_results': {},
        'semester_gpas': {},
        'opt_results': [],
        'roll_no': None,
        'session': None,
        'semester_totals': {},
        'total_credit_hours': 0,
        'total_full_marks': 0,
        'max_marks': 0,
        'avg_percentage': 0,
        'total_quality_points': 0,
        'cgpa': 0,
        'search_query': request.GET.get('search', '').strip(),
    }
    
    search_query = context['search_query']
    
    if not search_query:
        return render(request, 'fee_management/results.html', context)
    
    try:
        # Try to find student by university_roll_no or Registration_number
        student = Student.objects.get(
            Q(university_roll_no__iexact=search_query) |
            Q(Registration_number__iexact=search_query)
        )
    except Student.DoesNotExist:
        messages.error(request, f"No student found with ID: {search_query}")
        return render(request, 'fee_management/results.html', context)
    except Exception as e:
        messages.error(request, f"Error searching for student: {str(e)}")
        return render(request, 'fee_management/results.html', context)
    
    roll_no = student.university_roll_no or 'N/A'
    session = student.applicant.session

    # Fetch published exam results only
    results = ExamResult.objects.filter(
        student=student,
        is_published=True
    ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__academic_session').order_by(
        'course_offering__semester__name', 'course_offering__course__code'
    )
    print(f"Results fetched: {results.count()} entries.")

    # Handle case where no results are found
    not_found_roll = f"No results found for roll number {roll_no}" if roll_no and not results else None

    # Separate optional and non-optional results
    opt_results = results.filter(course_offering__course__opt=True)
    non_opt_results = results.exclude(course_offering__course__opt=True)
    print(f"Optional results count: {opt_results.count()}, Non-optional results count: {non_opt_results.count()}.")

    def calculate_quality_points(result):
        credit_hour = result.course_offering.course.credits
        total_marks = math.ceil(float(result.percentage or 0))
        print(f"Result for {result.student.university_roll_no}: Percentage: {result.percentage}, Ceiled: {total_marks}")

        quality_points_mapping = {
            40: 1.0, 41: 1.1, 42: 1.2, 43: 1.3, 44: 1.4, 45: 1.5,
            46: 1.6, 47: 1.7, 48: 1.8, 49: 1.9, 50: 2.0, 51: 2.07,
            52: 2.14, 53: 2.21, 54: 2.28, 55: 2.35, 56: 2.42, 57: 2.49,
            58: 2.56, 59: 2.63, 60: 2.70, 61: 2.76, 62: 2.82, 63: 2.88,
            64: 2.94, 65: 3.00, 66: 3.05, 67: 3.10, 68: 3.15, 69: 3.20,
            70: 3.25, 71: 3.30, 72: 3.35, 73: 3.40, 74: 3.45, 75: 3.50,
            76: 3.55, 77: 3.60, 78: 3.65, 79: 3.70, 80: 3.75, 81: 3.80,
            82: 3.85, 83: 3.90, 84: 3.95, 85: 4.0, 86: 4.0, 87: 4.0,
            88: 4.0, 89: 4.0, 90: 4.0, 91: 4.0, 92: 4.0, 93: 4.0,
            94: 4.0, 95: 4.0, 96: 4.0, 97: 4.0, 98: 4.0, 99: 4.0,
            100: 4.0
        }
        quality_points = quality_points_mapping.get(total_marks, 0.0) * credit_hour
        print(f"Result: {result.student.university_roll_no}, Marks: {total_marks}, Quality Points: {quality_points}")
        return round(quality_points, 2)

    # Add calculated fields to non-optional results
    for result in non_opt_results:
        result.quality_points = calculate_quality_points(result)
        result.grade = calculate_grade(result.percentage)
        
        # Set is_fail based on grade and save to database
        if result.grade == 'F' and not result.is_fail:
            result.is_fail = True
            result.save(update_fields=['is_fail'])
        
        # Get enrollment info to check if this is a repeat course
        try:
            enrollment = CourseEnrollment.objects.get(
                student_semester_enrollment__student=result.student,
                course_offering=result.course_offering
            )
            result.is_repeat = enrollment.is_repeat
        except CourseEnrollment.DoesNotExist:
            result.is_repeat = False
        
        result.effective_credit_hour = result.course_offering.course.credits
        result.course_marks = result.course_offering.course.credits * 20 + (
            result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
        )
        print(f"Result: {result.student.university_roll_no}, Quality Points: {result.quality_points}, "
              f"Effective Credit Hours: {result.effective_credit_hour}, Course Marks: {result.course_marks}")

    # Add grades and repeat status to optional results
    for opt_result in opt_results:
        opt_result.grade = calculate_grade(opt_result.percentage)
        try:
            enrollment = CourseEnrollment.objects.get(
                student_semester_enrollment__student=opt_result.student,
                course_offering=opt_result.course_offering
            )
            opt_result.is_repeat = enrollment.is_repeat
        except CourseEnrollment.DoesNotExist:
            opt_result.is_repeat = False

    # Group non-optional results by semester
    semester_results = defaultdict(list)
    for result in non_opt_results:
        semester_results[result.course_offering.semester.name].append(result)

    # Calculate semester-wise metrics
    semester_gpas = {}
    semester_totals = {}
    for semester, semester_data in semester_results.items():
        total_qp = sum(calculate_quality_points(result) for result in semester_data)
        total_credit_hours = sum(result.course_offering.course.credits for result in semester_data)
        semester_gpas[semester] = round(total_qp / total_credit_hours, 2) if total_credit_hours > 0 else 0

        total_marks = sum(float(result.percentage or 0) * result.course_offering.course.credits for result in semester_data)
        avg_percentage = math.ceil(total_marks / total_credit_hours) if total_credit_hours > 0 else 0
        total_full_marks = sum(
            (result.course_offering.course.credits * 20 + (
                result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
            )) for result in semester_data
        )
        max_marks = sum(result.total_marks or 0 for result in semester_data)
        total_quality_points = round(sum(calculate_quality_points(result) for result in semester_data), 2)

        semester_totals[semester] = {
            'total_credit_hours': total_credit_hours,
            'total_full_marks': total_full_marks,
            'max_marks': max_marks,
            'average_percentage': avg_percentage,
            'total_quality_points': total_quality_points
        }
        print(f"Semester: {semester}")
        print(f"  Total Credit Hours: {total_credit_hours}")
        print(f"  Total Full Marks: {total_full_marks}")
        print(f"  Max Marks: {max_marks}")
        print(f"  Average Percentage: {avg_percentage}%")
        print(f"  Total Quality Points: {total_quality_points}")

    # Calculate overall CGPA (excluding optional courses)
    total_quality_points = round(sum(result.quality_points for result in non_opt_results), 2)
    total_credit_hours = sum(result.course_offering.course.credits for result in non_opt_results)
    cgpa = round(total_quality_points / total_credit_hours, 2) if total_credit_hours > 0 else 0
    print(f"Total Quality Points: {total_quality_points}, Total Credit Hours: {total_credit_hours}, CGPA: {cgpa}")

    total_marks = sum(float(result.percentage or 0) * result.course_offering.course.credits for result in non_opt_results)
    avg_percentage = math.ceil(total_marks / total_credit_hours) if total_credit_hours > 0 else 0
    print(f"Total Marks: {total_marks}, Average Percentage: {avg_percentage}")

    total_full_marks = sum(
        (result.course_offering.course.credits * 20 + (
            result.course_offering.course.lab_work * 20 if result.course_offering.course.lab_work > 0 else 0
        )) for result in non_opt_results
    )
    max_marks = sum(result.total_marks or 0 for result in non_opt_results)
    print(f"Total Full Marks: {total_full_marks}, Max Marks: {max_marks}")

    context.update({
        'student': student,
        'semester_results': dict(semester_results),
        'semester_gpas': semester_gpas,
        'opt_results': opt_results,
        'roll_no': roll_no,
        'session': session,
        'semester_totals': semester_totals,
        'msg': not_found_roll,
        'total_credit_hours': total_credit_hours,
        'total_full_marks': total_full_marks,
        'max_marks': max_marks,
        'avg_percentage': avg_percentage,
        'total_quality_points': total_quality_points,
        'cgpa': cgpa,
        'search_query': search_query,
    })

    return render(request, 'fee_management/results.html', context)











from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.template.loader import render_to_string
from .models import SemesterFee, FeeType, AcademicSession, Program, FeeToProgram, Semester
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.http import JsonResponse

import json

@office_required
def semester_fee(request):
    query = request.GET.get('q', '')
    edit_id = request.GET.get('edit')
    delete_id = request.GET.get('delete')
    
    semester_fees = SemesterFee.objects.select_related('fee_type').prefetch_related('semester_fees__academic_session', 'semester_fees__programs', 'semester_fees__semester_number').all()
    fee_types = FeeType.objects.all()
    academic_sessions = AcademicSession.objects.filter(is_active=True)
    programs = Program.objects.all()
    
    if query:
        semester_fees = semester_fees.filter(
            Q(fee_type__name__icontains=query) |
            Q(total_amount__icontains=query)
        )
    
    edit_fee = None
    delete_fee = None
    errors = []
    fee_type_errors = []
    
    if edit_id:
        edit_fee = get_object_or_404(SemesterFee, pk=edit_id)
    
    if delete_id:
        delete_fee = get_object_or_404(SemesterFee, pk=delete_id)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'fee_type':
            feetype_id = int(request.POST.get('feetype_id')) if request.POST.get('feetype_id') and request.POST.get('feetype_id').isdigit() else None
            name = request.POST.get('fee_type_name')
            description = request.POST.get('fee_type_description', '')
            is_active = request.POST.get('fee_type_is_active') == 'on'
            
            if not name:
                fee_type_errors.append("Name is required.")
            elif FeeType.objects.filter(name=name).exclude(pk=feetype_id).exists():
                fee_type_errors.append("Fee Type with this name already exists.")
            
            if not fee_type_errors:
                try:
                    if feetype_id is not None:
                        fee_type = get_object_or_404(FeeType, pk=feetype_id)
                        fee_type.name = name
                        fee_type.description = description
                        fee_type.is_active = is_active
                        fee_type.save()
                        messages.success(request, 'Fee Type updated successfully.')
                    else:
                        FeeType.objects.create(
                            name=name,
                            description=description, 
                            is_active=is_active
                        )
                        messages.success(request, 'Fee Type added successfully.')
                    return redirect('fee_management:semester-fee')
                except (ValueError, TypeError) as e:
                    fee_type_errors.append('Invalid fee type ID. Please try again.')
        
        elif form_type == 'delete_feetype':
            feetype_id = request.POST.get('feetype_id')
            fee_type = get_object_or_404(FeeType, pk=feetype_id)
            if fee_type.semester_fees.exists():
                messages.error(request, 'Cannot delete Fee Type because it is associated with Semester Fees.')
            else:
                fee_type.delete()
                messages.success(request, 'Fee Type deleted successfully.')
            return redirect('fee_management:semester-fee')
        
        elif form_type == 'delete_fee':
            delete_fee = get_object_or_404(SemesterFee, pk=request.POST['delete_id'])
            delete_fee.delete()
            messages.success(request, 'Semester fee deleted successfully.')
            return redirect('fee_management:semester-fee')
        
        elif form_type == 'semester_fee':
            fee_type_id = request.POST.get('fee_type')
            total_amount = request.POST.get('total_amount')
            shift = request.POST.get('shift')
            is_active = request.POST.get('is_active') == 'on'
            academic_session_id = request.POST.get('academic_session')
            program_ids = request.POST.getlist('programs')
            semester_ids = request.POST.getlist('semester_number')
            dynamic_fees_json = request.POST.get('dynamic_fees')
            
            # Validation
            if not fee_type_id:
                errors.append("Fee Type is required.")
            if not total_amount:
                errors.append("Total Amount is required.")
            if not shift:
                errors.append("Shift is required.")
            if not academic_session_id:
                errors.append("Academic Session is required.")
            if not program_ids:
                errors.append("At least one Program is required.")
            if not semester_ids:
                errors.append("At least one Semester is required.")
            
            try:
                total_amount = Decimal(total_amount) if total_amount else None
                dynamic_fees = json.loads(dynamic_fees_json) if dynamic_fees_json else {}
                # Validate dynamic fees
                for head, amount in dynamic_fees.items():
                    if not head:
                        errors.append("Fee head name cannot be empty.")
                    if not isinstance(amount, (int, float)) or amount < 0:
                        errors.append(f"Invalid amount for {head}. Amount must be a non-negative number.")
            except (ValueError, TypeError, json.JSONDecodeError):
                errors.append("Invalid fee data provided.")
            
            try:
                fee_type = FeeType.objects.get(pk=fee_type_id) if fee_type_id else None
            except FeeType.DoesNotExist:
                errors.append("Invalid Fee Type selected.")
            
            try:
                academic_session = AcademicSession.objects.get(pk=academic_session_id) if academic_session_id else None
            except AcademicSession.DoesNotExist:
                errors.append("Invalid Academic Session selected.")
            
            if not errors:
                if 'edit_id' in request.POST:
                    # Update existing SemesterFee
                    edit_fee = get_object_or_404(SemesterFee, pk=request.POST['edit_id'])
                    edit_fee.fee_type = fee_type
                    edit_fee.total_amount = total_amount
                    edit_fee.shift = shift
                    edit_fee.dynamic_fees = dynamic_fees
                    edit_fee.is_active = is_active
                    edit_fee.save()
                    
                    # Update FeeToProgram
                    ftp = edit_fee.semester_fees.first()
                    if ftp:
                        ftp.academic_session = academic_session
                        ftp.programs.set(Program.objects.filter(pk__in=program_ids))
                        ftp.semester_number.set(Semester.objects.filter(pk__in=semester_ids))
                        ftp.save()
                    else:
                        ftp = FeeToProgram.objects.create(
                            SemesterFee=edit_fee,
                            academic_session=academic_session
                        )
                        ftp.programs.set(Program.objects.filter(pk__in=program_ids))
                        ftp.semester_number.set(Semester.objects.filter(pk__in=semester_ids))
                    
                    messages.success(request, 'Semester fee updated successfully.')
                    return redirect('fee_management:semester-fee')
                else:
                    # Create new SemesterFee
                    semester_fee = SemesterFee.objects.create(
                        fee_type=fee_type,
                        total_amount=total_amount,
                        shift=shift,
                        dynamic_fees=dynamic_fees,
                        is_active=is_active
                    )
                    
                    # Create FeeToProgram
                    ftp = FeeToProgram.objects.create(
                        SemesterFee=semester_fee,
                        academic_session=academic_session
                    )
                    ftp.programs.set(Program.objects.filter(pk__in=program_ids))
                    ftp.semester_number.set(Semester.objects.filter(pk__in=semester_ids))
                    
                    messages.success(request, 'Semester fee scheduled successfully.')
                    return redirect('fee_management:semester-fee')
    
    return render(request, 'fee_management/semester_fee.html', {
        'semester_fees': semester_fees,
        'fee_types': fee_types,
        'academic_sessions': academic_sessions,
        'programs': programs,
        'edit_fee': edit_fee,
        'delete_fee': delete_fee,
        'query': query,
        'errors': errors,
        'fee_type_errors': fee_type_errors
    })





@office_required
def get_programs(request):
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            # Fetch programs that have semesters in the selected academic session
            programs = Program.objects.filter(semesters__session_id=session_id).distinct()
            print(programs)
            programs_data = [{'id': program.pk, 'name': program.name} for program in programs]
            return JsonResponse({'programs': programs_data})
        except AcademicSession.DoesNotExist:
            return JsonResponse({'programs': []})
    return JsonResponse({'programs': []})



@office_required
def get_semesters(request):
    session_id = request.GET.get('session_id')
    program_ids = request.GET.get('program_ids', '').split(',')
    if session_id and program_ids and program_ids[0]:
        try:
            # Fetch semesters for the selected session and programs
            semesters = Semester.objects.filter(
                session_id=session_id,
                program_id__in=program_ids
            ).select_related('program')
            semesters_data = [
                {
                    'id': semester.pk,
                    'name': semester.name,
                    'program_name': semester.program.name
                }
                for semester in semesters
            ]
            return JsonResponse({'semesters': semesters_data})
        except AcademicSession.DoesNotExist:
            return JsonResponse({'semesters': []})
    return JsonResponse({'semesters': []})    
    
    
@office_required
def get_bulk_programs(request):
    """
    AJAX view to get programs filtered by department and session for bulk voucher generation.
    Expected GET parameters:
    - department: Department ID
    - session_id: Academic session ID
    """
    print("\n=== DEBUG: get_bulk_programs ===")
    print(f"Request GET params: {request.GET}")
    
    try:
        session_id = request.GET.get('session_id')
        department_id = request.GET.get('department')
        
        print(f"Session ID: {session_id}, Department ID: {department_id}")
        
        if not department_id or not session_id:
            error_msg = 'Both department ID and session_id are required'
            print(f"Error: {error_msg}")
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=400
            )
        
        # Debug: Check if department exists
        from academics.models import Department
        try:
            dept = Department.objects.get(id=department_id)
            print(f"Found department: {dept.name} (ID: {dept.id})")
        except Department.DoesNotExist:
            error_msg = f"Department with ID {department_id} does not exist"
            print(error_msg)
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=400
            )
        
        # Debug: Check if session exists
        from admissions.models import AcademicSession
        try:
            session = AcademicSession.objects.get(id=session_id)
            print(f"Found session: {session.name} (ID: {session.id})")
        except AcademicSession.DoesNotExist:
            error_msg = f"Session with ID {session_id} does not exist"
            print(error_msg)
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=400
            )
        
        # Get programs for the selected department and session
        programs = Program.objects.filter(
            department_id=department_id,
            semesters__session_id=session_id
        ).distinct()
        
        print(f"Found {programs.count()} programs for department {department_id} and session {session_id}")
        for p in programs:
            print(f"- {p.name} (ID: {p.id})")
        
        programs_data = [
            {'id': program.id, 'name': program.name} 
            for program in programs
        ]
        
        response_data = {
            'success': True,
            'programs': programs_data
        }
        
        print(f"Sending response: {response_data}")
        print("==========================\n")
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': f'An error occurred while fetching programs: {str(e)}'}, 
            status=500
        )

@office_required
def get_bulk_semesters(request):
    """
    AJAX view to get active semesters for bulk voucher generation.
    Expected GET parameters:
    - program_id: Program ID
    - session_id: Academic session ID
    """
    try:
        program_id = request.GET.get('program_id')
        session_id = request.GET.get('session_id')
        
        if not program_id or not session_id:
            return JsonResponse(
                {'success': False, 'error': 'Both program ID and session_id are required'}, 
                status=400
            )
        
        # Get active semesters for the selected program and session
        semesters = Semester.objects.filter(
            program_id=program_id,
            session_id=session_id,
            is_active=True
        ).select_related('program')
        
        semesters_data = [
            {
                'id': semester.id,
                'name': semester.name,
                'number': semester.number,
                'program_name': semester.program.name
            }
            for semester in semesters
        ]
        
        return JsonResponse({
            'success': True,
            'semesters': semesters_data
        })
        
    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': f'An error occurred while fetching semesters: {str(e)}'}, 
            status=500
        )
    
@login_required
@office_required
def bulk_generate_vouchers(request):
    print(f'this is showing view of bult voucher genrte.......')
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            department_id = data.get('department')
            program_id = data.get('program')
            session_id = data.get('session')
            semester_id = data.get('semester')
            
            # Validate required fields
            if not all([department_id, program_id, session_id, semester_id]):
                return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)
            
            # Get the office of the current officer
            try:
                office = request.user.officestaff_profile.office
            except OfficeStaff.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Officer profile not found'}, status=400)
            
            # Get the semester fee for the selected program and semester
            try:
                fee_to_program = FeeToProgram.objects.get(
                    programs__id=program_id,
                    semester_number__id=semester_id,
                    academic_session_id=session_id
                )
                semester_fee = fee_to_program.SemesterFee
                
                # Get all students matching the criteria through semester enrollments
                students = Student.objects.filter(
                    program_id=program_id,
                    semester_enrollments__semester_id=semester_id,
                    semester_enrollments__semester__session_id=session_id
                ).select_related('program__department').distinct()
                
                if not students.exists():
                    return JsonResponse({'success': False, 'error': 'No students found matching the criteria'}, status=400)
                
                # Generate vouchers
                generated_vouchers = []
                for student in students:
                    student_department_name = student.program.department.name if student.program and student.program.department else 'N/A'
                    
                    # Check if a voucher already exists
                    existing_voucher = FeeVoucher.objects.filter(
                        student=student,
                        semester_fee=semester_fee,
                        semester_id=semester_id
                    ).first()
                    
                    if existing_voucher:
                        generated_vouchers.append({
                            'student': student.university_roll_no or f"ID-{student.pk}",
                            'name': student.applicant.full_name if hasattr(student, 'applicant') else 'Unknown',
                            'voucher_id': existing_voucher.voucher_id,
                            'status': 'exists',
                            'message': f'Voucher {existing_voucher.voucher_id} already exists',
                            'department_name': student_department_name
                        })
                        continue
                    
                    # Create new voucher
                    try:
                        voucher = FeeVoucher.objects.create(
                            student=student,
                            semester_fee=semester_fee,
                            semester_id=semester_id,
                            due_date=timezone.now().date() + timezone.timedelta(days=15),
                            office=office
                        )
                        generated_vouchers.append({
                            'student': student.university_roll_no or f"ID-{student.pk}",
                            'name': student.applicant.full_name if hasattr(student, 'applicant') else 'Unknown',
                            'voucher_id': voucher.voucher_id,
                            'status': 'created',
                            'message': 'Voucher created successfully',
                            'department_name': student_department_name
                        })
                    except Exception as e:
                        generated_vouchers.append({
                            'student': student.university_roll_no or f"ID-{student.pk}",
                            'name': student.applicant.full_name if hasattr(student, 'applicant') else 'Unknown',
                            'voucher_id': None,
                            'status': 'error',
                            'message': str(e),
                            'department_name': student_department_name
                        })
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully generated {len([v for v in generated_vouchers if v["status"] == "created"])} vouchers',
                    'vouchers': generated_vouchers
                })
                
            except FeeToProgram.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No fee structure found for the selected criteria'}, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - show the form
    from academics.models import Department
    
    # Get all active departments
    departments = Department.objects.filter(
        programs__isnull=False  # Only departments with programs
    ).distinct().order_by('name')
    print(f'this is departments: {departments}')
    # Format the departments to match the expected structure
    departments_list = [
        {
            'department_id': dept.id,
            'department_name': dept.name,
            'code': dept.code  # Include the code if needed
        }
        for dept in departments
    ]
    
    # Debug output
    print("\n=== DEBUG: Departments Data ===")
    print(f"Number of departments: {len(departments_list)}")
    for dept in departments_list:
        print(f"ID: {dept['department_id']}, Name: {dept['department_name']}, Code: {dept['code']}")
    print("==========================\n")
    
    # Debug template context
    context = {
        'departments': departments_list,
        'sessions': AcademicSession.objects.filter(is_active=True).order_by('-start_year'),
        'debug_departments': departments_list,  # For template debugging
    }
    
    print("\n=== DEBUG: Template Context ===")
    print(f"Context keys: {list(context.keys())}")
    print(f"Departments in context: {len(context['departments'])} items")
    print("First department:", context['departments'][0] if context['departments'] else 'No departments')
    print("==========================\n")
    
    # Use the context dictionary we prepared
    return render(request, 'fee_management/bulk_generate_vouchers.html', context)
    
    
    

@office_required
def fee_verification(request):
    context = {}
    
    if request.method == 'POST':
        voucher_id = request.POST.get('voucher_id')
        action = request.POST.get('action')
        
        if not voucher_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Voucher ID is required.'}, status=400)
            messages.error(request, 'Voucher ID is required.')
            return redirect('fee_management:fee_verification')
            
        try:
            voucher = FeeVoucher.objects.select_related(
                'student', 'semester_fee', 'semester'
            ).get(voucher_id=voucher_id)
            
            if action == 'verify':
                if voucher.is_paid:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': 'This voucher has already been marked as paid.'}, status=400)
                    messages.warning(request, 'This voucher has already been marked as paid.')
                    payment = voucher.payment
                else:
                    payment = StudentFeePayment.objects.filter(
                        student=voucher.student,
                        semester_fee=voucher.semester_fee
                    ).exclude(voucher__isnull=False).first()
                    
                    try:
                        # Calculate late fees if applicable
                        dynamic_fees = dict(voucher.semester_fee.dynamic_fees) if voucher.semester_fee.dynamic_fees else {}
                        total_amount = voucher.semester_fee.total_amount
                        late_fee_type = None
                        late_fee_amount = 0
                        today = date.today()
                        due_passed = voucher.due_date and voucher.due_date < today
                        
                        # Check if student's semester is active
                        enrollment = StudentSemesterEnrollment.objects.filter(
                            student=voucher.student, 
                            semester=voucher.semester
                        ).first()
                        is_active_semester = enrollment and enrollment.status == 'enrolled'
                        
                        # Late fee logic
                        if due_passed and not voucher.is_paid:
                            if is_active_semester:
                                # Add Late Fee 10%
                                late_fee_type = 'Late Fee 10%'
                                late_fee_amount = (Decimal('0.1') * total_amount).quantize(Decimal('1.00'))
                                dynamic_fees[late_fee_type] = str(late_fee_amount)
                                total_amount += late_fee_amount
                            else:
                                # Add Late Fee 100%
                                late_fee_type = 'Late Fee 100%'
                                late_fee_amount = total_amount
                                dynamic_fee_amount = total_amount
                                dynamic_fees[late_fee_type] = str(late_fee_amount)
                                total_amount += late_fee_amount
                        elif not is_active_semester and not voucher.is_paid:
                            # Add Late Dues 100% (same as total_amount)
                            late_fee_type = 'Late Dues'
                            late_fee_amount = total_amount
                            dynamic_fees[late_fee_type] = str(late_fee_amount)
                            total_amount += late_fee_amount
                            
                        if not payment:
                            payment = StudentFeePayment.objects.create(
                                student=voucher.student,
                                semester_fee=voucher.semester_fee,
                                amount_paid=total_amount,  # Use total_amount which includes late fees
                                remarks=f'Payment verified against voucher {voucher_id}. ' + 
                                       (f'Late fee applied: {late_fee_type} - {late_fee_amount} PKR' if late_fee_type else '')
                            )
                        
                        if not voucher.is_paid:
                            voucher.mark_as_paid(payment)
                            success_message = (
                                f'Payment of {total_amount} PKR (Base: {voucher.semester_fee.total_amount} PKR' +
                                (f', Late Fee: {late_fee_amount} PKR' if late_fee_amount else '') +
                                f') has been recorded and voucher {voucher_id} marked as paid.'
                            )
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                # Update context with all necessary data including late fees
                                context.update({
                                    'voucher': voucher,
                                    'student': voucher.student,
                                    'semester_fee': voucher.semester_fee,
                                    'payment_exists': bool(voucher.payment),
                                    'dynamic_fees': dynamic_fees,
                                    'total_amount': total_amount,
                                    'late_fee_type': late_fee_type,
                                    'late_fee_amount': late_fee_amount,
                                    'is_active_semester': is_active_semester,
                                    'due_passed': due_passed
                                })
                                html = render_to_string('fee_management/voucher_details.html', context, request)
                                return JsonResponse({'html': html, 'message': success_message})
                            messages.success(request, success_message)
                    except ValueError as e:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'error': str(e)}, status=400)
                        messages.error(request, str(e))
                        return redirect('fee_management:fee_verification')
            
            # Calculate late fees if applicable
            dynamic_fees = dict(voucher.semester_fee.dynamic_fees) if voucher.semester_fee.dynamic_fees else {}
            total_amount = voucher.semester_fee.total_amount
            late_fee_type = None
            late_fee_amount = 0
            today = date.today()
            due_passed = voucher.due_date and voucher.due_date < today
            
            # Check if student's semester is active
            enrollment = StudentSemesterEnrollment.objects.filter(
                student=voucher.student, 
                semester=voucher.semester
            ).first()
            is_active_semester = enrollment and enrollment.status == 'enrolled'
            
            # Late fee logic
            if due_passed and not voucher.is_paid:
                if is_active_semester:
                    # Add Late Fee 10%
                    late_fee_type = 'Late Fee 10%'
                    late_fee_amount = (Decimal('0.1') * total_amount).quantize(Decimal('1.00'))
                    dynamic_fees[late_fee_type] = str(late_fee_amount)
                    total_amount += late_fee_amount
                else:
                    # Add Late Fee 100%
                    late_fee_type = 'Late Fee 100%'
                    late_fee_amount = total_amount
                    dynamic_fees[late_fee_type] = str(late_fee_amount)
                    total_amount += late_fee_amount
            elif not is_active_semester and not voucher.is_paid:
                # Add Late Dues 100% (same as total_amount)
                late_fee_type = 'Late Dues'
                late_fee_amount = total_amount
                dynamic_fees[late_fee_type] = str(late_fee_amount)
                total_amount += late_fee_amount
            
            context.update({
                'voucher': voucher,
                'student': voucher.student,
                'semester_fee': voucher.semester_fee,
                'payment_exists': bool(voucher.payment),
                'dynamic_fees': dynamic_fees,
                'total_amount': total_amount,
                'late_fee_type': late_fee_type,
                'late_fee_amount': late_fee_amount,
                'is_active_semester': is_active_semester,
                'due_passed': due_passed
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('fee_management/voucher_details.html', context, request)
                return JsonResponse({'html': html})
                
        except FeeVoucher.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid voucher ID. Please check and try again.'}, status=404)
            messages.error(request, 'Invalid voucher ID. Please check and try again.')
            return redirect('fee_management:fee_verification')
    
    return render(request, 'fee_management/fee_verification.html', context)






@office_required
def get_semesters_by_roll(request):
    # Initialize logger
    logger = logging.getLogger(__name__)
    
    roll_no = request.GET.get('roll_no')
    if not roll_no:
        return JsonResponse({'error': 'Roll number is required.'}, status=400)
    
    try:
        # Get the student and their program/session
        student = Student.objects.get(university_roll_no=roll_no)
        program = student.program
        session = student.applicant.session
        
        # Get student's shift from applicant
        student_shift = student.applicant.shift.lower()  # 'morning' or 'evening'
        
        # Get fee programs that match the student's program, session, and shift
        fee_programs = FeeToProgram.objects.filter(
            programs=program,
            academic_session=session,
            SemesterFee__shift__iexact=student_shift
        ).select_related('SemesterFee').prefetch_related('semester_number')
        
        # Debug logging
        logger.info(f"Student shift: {student_shift}")
        logger.info(f"Found {fee_programs.count()} fee programs matching program {program.name}, session {session.name}, and shift {student_shift}")
        
        # Get all semesters from fee programs
        semesters = set()
        for fp in fee_programs:
            semesters.update(fp.semester_number.all())
            
        if not semesters:
            return JsonResponse(
                {'error': 'No fee programs found for this student.'}, 
                status=404
            )
            
        # Get all fee vouchers for this student
        student_vouchers = FeeVoucher.objects.filter(
            student=student,
            semester__in=semesters
        ).select_related('semester', 'semester_fee')
        
        paid_vouchers = student_vouchers.filter(is_paid=True)
        
        # Find semesters that have unpaid fee vouchers
        available_semesters = []
        
        for semester in semesters:
            # Get all fee programs for this semester
            semester_fee_programs = [
                fp for fp in fee_programs 
                if semester in fp.semester_number.all()
            ]
            
            if not semester_fee_programs:
                continue  # Skip semesters with no fee programs
                
            # Check if there are any unpaid vouchers for this semester
            has_unpaid_vouchers = student_vouchers.filter(
                semester=semester,
                is_paid=False
            ).exists()
            
            # Check if all fee programs for this semester are paid
            all_paid = all(
                paid_vouchers.filter(
                    semester_fee=fp.SemesterFee,
                    semester=semester
                ).exists()
                for fp in semester_fee_programs
            )
            
            # If there are no unpaid vouchers and all fees are paid, skip
            if not has_unpaid_vouchers and all_paid:
                continue
                
            # Get the fee details for this semester
            fee_details = []
            for fp in semester_fee_programs:
                is_paid = paid_vouchers.filter(
                    semester_fee=fp.SemesterFee,
                    semester=semester
                ).exists()
                
                fee_details.append({
                    'fee_type': fp.SemesterFee.fee_type.name,
                    'amount': float(fp.SemesterFee.total_amount),
                    'is_paid': is_paid,
                    'due_date': fp.due_date.isoformat() if hasattr(fp, 'due_date') else None,
                    'shift': fp.SemesterFee.get_shift_display() if hasattr(fp.SemesterFee, 'get_shift_display') else 'N/A'
                })
            
            available_semesters.append({
                'id': semester.id,
                'name': semester.name,
                'program_name': program.name,
                'session': session.name,
                'fees': fee_details,
                'has_unpaid_vouchers': has_unpaid_vouchers
            })
        
        return JsonResponse({
            'student': {
                'id': student.applicant.id,
                'name': student.applicant.full_name,
                'roll_no': student.university_roll_no,
                'program': program.name,
                'session': session.name
            },
            'available_semesters': available_semesters
        })
        
    except Student.DoesNotExist:
        return JsonResponse(
            {'error': 'Student with this roll number does not exist.'}, 
            status=404
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_semesters_by_roll: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'An error occurred while fetching semester data. Please try again later.'}, 
            status=500
        )





# def student_generate_voucher(request):
#     """
#     View for students to view and print their existing fee vouchers.
#     Students cannot generate new vouchers - they can only view/print existing ones.
#     """
#     if not hasattr(request.user, 'student_profile'):
#         return redirect('login')
    
#     student = request.user.student_profile
    
#     # Get all existing vouchers for the student
#     vouchers = FeeVoucher.objects.filter(
#         student=student
#     ).select_related('semester', 'semester_fee', 'semester_fee__fee_type').order_by('-generated_at')
    
#     # Get all semesters for the student's program and session
#     all_semesters = Semester.objects.filter(
#         program=student.program, 
#         session=student.applicant.session
#     ).order_by('name')
    
#     # Get semester details for each voucher
#     voucher_data = []
#     for voucher in vouchers:
#         try:
#             fee_details = json.loads(voucher.semester_fee.dynamic_fees) if \
#                 isinstance(voucher.semester_fee.dynamic_fees, str) else \
#                 voucher.semester_fee.dynamic_fees or {"Semester Fee": float(voucher.semester_fee.total_amount)}
#         except (json.JSONDecodeError, AttributeError):
#             fee_details = {"Semester Fee": float(voucher.semester_fee.total_amount)}
            
#         voucher_data.append({
#             'id': voucher.id,
#             'voucher_id': voucher.voucher_id,
#             'semester': voucher.semester.name,
#             'fee_type': voucher.semester_fee.fee_type.name,
#             'amount': voucher.semester_fee.total_amount,
#             'due_date': voucher.due_date.strftime('%d %B %Y'),
#             'is_paid': voucher.is_paid,
#             'paid_at': voucher.paid_at.strftime('%d %B %Y %I:%M %p') if voucher.paid_at else None,
#             'generated_at': voucher.generated_at.strftime('%d %B %Y %I:%M %p'),
#             'fee_details': fee_details
#         })
    
#     context = {
#         'vouchers': voucher_data,
#         'all_semesters': all_semesters,
#         'student_name': student.applicant.full_name,
#         'program': student.program.name,
#     }
    
#     # Handle AJAX request for viewing a specific voucher
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         voucher_id = request.GET.get('voucher_id')
#         if voucher_id:
#             try:
#                 voucher = FeeVoucher.objects.get(
#                     id=voucher_id,
#                     student=student
#                 )
                
#                 # Prepare voucher context
#                 office = voucher.office
#                 dynamic_fees = {}
#                 try:
#                     dynamic_fees = json.loads(voucher.semester_fee.dynamic_fees) if \
#                         isinstance(voucher.semester_fee.dynamic_fees, str) else \
#                         voucher.semester_fee.dynamic_fees or {"Semester Fee": float(voucher.semester_fee.total_amount)}
#                 except (json.JSONDecodeError, AttributeError):
#                     dynamic_fees = {"Semester Fee": float(voucher.semester_fee.total_amount)}
                
#                 context = {
#                     'voucher_id': voucher.voucher_id,
#                     'student_name': f"{student.applicant.full_name}",
#                     'cnic': getattr(student.applicant, 'cnic', 'N/A'),
#                     'father_name': getattr(student.applicant, 'father_name', 'N/A'),
#                     'program': student.program.name,
#                     'semester': voucher.semester.name,
#                     'shift': getattr(voucher.semester_fee, 'shift', 'Morning').title(),
#                     'academic_session': student.applicant.session.name,
#                     'fee_type': voucher.semester_fee.fee_type.name,
#                     'dynamic_fees': dynamic_fees,
#                     'total_amount': str(voucher.semester_fee.total_amount),
#                     'due_date': voucher.due_date.strftime('%d %B %Y'),
#                     'office_name': office.name if office else 'N/A',
#                     'office_address': office.location if office else 'N/A',
#                     'office_contact': office.contact_phone if office else 'N/A',
#                     'generated_at': voucher.generated_at.strftime('%d %B %Y %I:%M %p PKT'),
#                     'is_paid': voucher.is_paid,
#                     'paid_at': voucher.paid_at.strftime('%d %B %Y %I:%M %p') if voucher.paid_at else None,
#                 }
                
#                 voucher_html = render_to_string('fee_management/voucher.html', context, request)
#                 return JsonResponse({
#                     'success': True,
#                     'voucher_html': voucher_html,
#                     'voucher_id': str(voucher.voucher_id)
#                 })
#             except FeeVoucher.DoesNotExist:
#                 return JsonResponse({'error': 'Voucher not found or access denied'}, status=404)
        
#         return JsonResponse({
#             'success': True,
#             'vouchers': voucher_data
#         })
    
#     return render(request, 'fee_management/student_generate_voucher.html', context)

def student_generate_voucher(request):
    """
    View for students to view and print their existing fee voucher for the active semester.
    Students cannot generate new vouchers.
    """
    if not hasattr(request.user, 'student_profile'):
        return redirect('login')
    
    student = request.user.student_profile
    
    # Determine the active semester
    current_semester = Semester.objects.filter(
        program=student.program,
        session=student.applicant.session,
        is_active=True
    ).first()
    
    if not current_semester:
        # Fallback: Get the latest semester based on name
        current_semester = Semester.objects.filter(
            program=student.program,
            session=student.applicant.session
        ).order_by('-name').first()
    
    # Get the existing voucher for the active semester, if any
    voucher = FeeVoucher.objects.filter(
        student=student,
        semester=current_semester
    ).select_related('semester', 'semester_fee', 'semester_fee__fee_type').first()
    
    voucher_data = []
    if voucher:
        try:
            fee_details = json.loads(voucher.semester_fee.dynamic_fees) if \
                isinstance(voucher.semester_fee.dynamic_fees, str) else \
                voucher.semester_fee.dynamic_fees or {"Semester Fee": float(voucher.semester_fee.total_amount)}
        except (json.JSONDecodeError, AttributeError):
            fee_details = {"Semester Fee": float(voucher.semester_fee.total_amount)}
            
        voucher_data.append({
            'id': voucher.id,
            'voucher_id': voucher.voucher_id,
            'semester': voucher.semester.name,
            'fee_type': voucher.semester_fee.fee_type.name,
            'amount': voucher.semester_fee.total_amount,
            'due_date': voucher.due_date.strftime('%d %B %Y') if voucher.due_date else 'N/A',
            'is_paid': voucher.is_paid,
            'paid_at': voucher.paid_at.strftime('%d %B %Y %I:%M %p') if voucher.paid_at else None,
            'generated_at': voucher.generated_at.strftime('%d %B %Y %I:%M %p') if voucher.generated_at else 'N/A',
            'fee_details': fee_details
        })
    
    context = {
        'vouchers': voucher_data,
        'current_semester': current_semester,
        'student_name': student.applicant.full_name,
        'program': student.program.name,
    }
    
    # Handle AJAX requests for viewing a specific voucher
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        voucher_id = request.GET.get('voucher_id')
        if voucher_id:
            try:
                voucher = FeeVoucher.objects.get(
                    id=voucher_id,
                    student=student,
                    semester=current_semester
                )
                
                # Prepare voucher context
                office = voucher.office
                dynamic_fees = {}
                try:
                    dynamic_fees = json.loads(voucher.semester_fee.dynamic_fees) if \
                        isinstance(voucher.semester_fee.dynamic_fees, str) else \
                        voucher.semester_fee.dynamic_fees or {"Semester Fee": float(voucher.semester_fee.total_amount)}
                except (json.JSONDecodeError, AttributeError):
                    dynamic_fees = {"Semester Fee": float(voucher.semester_fee.total_amount)}
                
                voucher_context = {
                    'voucher_id': voucher.voucher_id,
                    'student_name': f"{student.applicant.full_name}",
                    'cnic': getattr(student.applicant, 'cnic', 'N/A'),
                    'father_name': getattr(student.applicant, 'father_name', 'N/A'),
                    'program': student.program.name,
                    'semester': voucher.semester.name,
                    'shift': getattr(voucher.semester_fee, 'shift', 'Morning').title(),
                    'academic_session': student.applicant.session.name,
                    'fee_type': voucher.semester_fee.fee_type.name,
                    'dynamic_fees': dynamic_fees,
                    'total_amount': str(voucher.semester_fee.total_amount),
                    'updated_total_amount': str(voucher.semester_fee.total_amount),
                    'due_date': voucher.due_date.strftime('%d %B %Y') if voucher.due_date else 'N/A',
                    'generated_at': voucher.generated_at.strftime('%d %B %Y %I:%M %p') if voucher.generated_at else 'N/A',
                    'office_name': office.name if office else 'N/A',
                    'office_address': office.location if office else 'N/A',
                    'office_contact': office.contact_phone if office else 'N/A',
                    'is_paid': voucher.is_paid,
                    'paid_at': voucher.paid_at.strftime('%d %B %Y %I:%M %p') if voucher.paid_at else None,
                }
                
                voucher_html = render_to_string('fee_management/voucher.html', voucher_context, request)
                return JsonResponse({
                    'success': True,
                    'voucher_html': voucher_html,
                    'voucher_id': str(voucher.voucher_id)
                })
            except FeeVoucher.DoesNotExist:
                return JsonResponse({'error': 'Voucher not found or access denied'}, status=404)
        
        return JsonResponse({
            'success': True,
            'vouchers': voucher_data
        })
    
    return render(request, 'fee_management/student_generate_voucher.html', context)



def generate_voucher(request):
    errors = []
    
    if request.method == 'POST':
        roll_no = request.POST.get('university_roll_no')
        semester_id = request.POST.get('semester')
        
        if not roll_no:
            errors.append("University Roll Number is required.")
        if not semester_id:
            errors.append("Semester is required.")
        
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': errors}, status=400)
            return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        try:
            student = Student.objects.get(university_roll_no=roll_no)
        except Student.DoesNotExist:
            errors.append("Student with this roll number does not exist.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': errors}, status=400)
            return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        try:
            semester = Semester.objects.get(pk=semester_id)
        except Semester.DoesNotExist:
            errors.append("Invalid semester selected.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': errors}, status=400)
            return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        # Get student's shift from their program or applicant info
        student_shift = getattr(student.applicant, 'shift', None) or 'morning'  # Default to morning if shift not set
        
        # Find matching SemesterFee for student's program, semester, shift, and active session
        fee_to_program = FeeToProgram.objects.filter(
            semester_number__in=[semester],
            programs__in=[student.program],
            academic_session__is_active=True
        ).filter(
            SemesterFee__shift=student_shift
        ).first()
        
        if not fee_to_program:
            # Try to find any fee without shift filter if no match found
            fee_to_program = FeeToProgram.objects.filter(
                semester_number__in=[semester],
                programs__in=[student.program],
                academic_session__is_active=True
            ).first()
            
            if not fee_to_program:
                errors.append(f"No fee schedule found for {student_shift} shift in this program and semester.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'errors': errors}, status=400)
                return render(request, 'fee_management/voucher.html', {'errors': errors})
        
        semester_fee = fee_to_program.SemesterFee
        
        # Get the office from the request user or use the first available office as fallback
        office = None
        if hasattr(request.user, 'office'):
            office = request.user.office
        else:
            # Fallback to the first available office if user doesn't have one
            office = Office.objects.first()
            
        # Check or create voucher
        voucher, created = FeeVoucher.objects.get_or_create(
            student=student,
            semester_fee=semester_fee,
            semester=semester,
            defaults={
                'due_date': date.today() + timedelta(days=7),
                'office': office
            }
        )

        # Use original generated_at if voucher already exists (assume created_at field exists; fallback to voucher.due_date minus 7 days if not)
        if hasattr(voucher, 'created_at'):
            generated_at = voucher.created_at.strftime('%d %B %Y %I:%M %p PKT')
        else:
            generated_at = (voucher.due_date - timedelta(days=7)).strftime('%d %B %Y %I:%M %p PKT') if voucher.due_date else datetime.now().strftime('%d %B %Y %I:%M %p PKT')

        # Update office if it wasn't set during creation
        if not created and not voucher.office and office:
            voucher.office = office
            voucher.save(update_fields=['office'])

        # Check if student's semester is active
        enrollment = StudentSemesterEnrollment.objects.filter(student=student, semester=semester).first()
        is_active_semester = enrollment and enrollment.status == 'enrolled'
        dynamic_fees = dict(semester_fee.dynamic_fees) if semester_fee.dynamic_fees else {}
        total_amount = semester_fee.total_amount
        late_fee_type = None
        late_fee_amount = 0
        today = date.today()
        due_passed = voucher.due_date and voucher.due_date < today
        new_voucher_created = False
        # Late fee logic
        if due_passed:
            if is_active_semester:
                # Add Late Fee 10%
                late_fee_type = 'Late Fee 10%'
                late_fee_amount = (Decimal('0.1') * total_amount).quantize(Decimal('1.00'))
                dynamic_fees[late_fee_type] = str(late_fee_amount)
                total_amount = total_amount + late_fee_amount
            else:
                # Add Late Fee 100%
                late_fee_type = 'Late Fee 100%'
                late_fee_amount = total_amount
                dynamic_fees[late_fee_type] = str(late_fee_amount)
                total_amount = total_amount + late_fee_amount
            # Instead of creating a new voucher, update the due_date of the existing voucher
            voucher.due_date = today + timedelta(days=7)
            voucher.save(update_fields=['due_date'])
            new_voucher_created = True
            # Set generated_at to now for the new voucher period (optional: keep original if you want)
            generated_at = datetime.now().strftime('%d %B %Y %I:%M %p PKT')
        elif not is_active_semester:
            # Add Late Dues 100% (same as total_amount)
            late_fee_type = 'Late Dues'
            late_fee_amount = total_amount
            dynamic_fees[late_fee_type] = str(late_fee_amount)
            total_amount = total_amount + late_fee_amount
        # Calculate updated_total_amount (total including all dynamic fees)
        updated_total_amount = sum(Decimal(str(amount)) for amount in dynamic_fees.values()) if dynamic_fees else Decimal(str(total_amount))
        context = {
            'voucher_id': voucher.voucher_id,
            'student_name': student.applicant.full_name,
            'cnic': student.applicant.cnic,
            'father_name': student.applicant.father_name,
            'program': student.program.name,
            'semester': semester.name,
            'shift': student_shift,
            'academic_session': fee_to_program.academic_session.name,
            'fee_type': semester_fee.fee_type.name,
            'dynamic_fees': dynamic_fees,  # Dictionary of fee heads and amounts
            'total_amount': str(total_amount),
            'due_date': voucher.due_date.strftime('%d %B %Y'),
            'office_name': voucher.office.name if voucher.office else 'N/A',
            'office_address': voucher.office.location if voucher.office else 'N/A',
            'office_contact': voucher.office.contact_phone if voucher.office else 'N/A',
            'generated_at': generated_at,
            'late_fee_type': late_fee_type,
            'late_fee_amount': str(late_fee_amount) if late_fee_amount else None,
            'new_voucher_created': new_voucher_created,
            'updated_total_amount': str(updated_total_amount),
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Render voucher HTML for AJAX response
            voucher_html = render_to_string('fee_management/voucher.html', context)
            return JsonResponse({'voucher_html': voucher_html})
        
        return render(request, 'fee_management/voucher.html', context)
    
    return render(request, 'fee_management/generate_voucher.html', {'errors': errors})




#  meirt list related section 
def active_session_required(program_id):
    try:
        selected_program = Program.objects.get(pk=program_id)
        print(f"Selected Program: {selected_program.name}")
        required_duration = selected_program.duration_years
        print(f"Required Duration: {required_duration} years")
        active_session = AcademicSession.objects.filter(
            is_active=True,
            end_year=F('start_year') + required_duration
        ).order_by('-start_year').first()
        print(f"Active Session: {active_session}")
        if not required_duration:
            messages.error(f"Program {selected_program.name} has no duration set.")
        if not active_session:
            messages.error(f"No active admission session found for a {required_duration}-year program.")
        return active_session
    except Program.DoesNotExist:
        messages.error("Invalid program selected")
        return None
# Set up logging
logger = logging.getLogger(__name__)

# Define valid shifts
VALID_SHIFTS = ['morning', 'evening']

@office_required
def generate_merit_list(request):
    programs = Program.objects.all()
    errors = []
    total_seats = 50  # Default total seats for the first merit list

    if request.method == 'POST':
        program_id = request.POST.get('program')
        list_number = request.POST.get('list_number')
        valid_until = request.POST.get('valid_until')
        notes = request.POST.get('notes', '')
        shift = request.POST.get('shift')
        total_seats = request.POST.get('no_of_seats', 50)  # Default to 50 if not provided

        # Validation
        if not program_id:
            errors.append("Program is required")
        if not list_number:
            errors.append("List number is required")
        if not valid_until:
            errors.append("Valid until date is required")
        if not shift or shift not in VALID_SHIFTS:
            errors.append(f"Shift must be one of: {', '.join(VALID_SHIFTS)}")

        # Additional validation
        list_num = None
        if program_id:
            try:
                program = Program.objects.get(pk=program_id)
                if list_number:
                    list_num = int(list_number)
                    if MeritList.objects.filter(program=program, list_number=list_num, shift=shift).exists():
                        errors.append(f"Merit list #{list_number} already exists for {program.name} and shift {shift}")
            except Program.DoesNotExist:
                errors.append("Invalid program selected")
            except (ValueError, TypeError):
                errors.append("List number must be a valid number")

        if list_number and not list_num:
            try:
                list_num = int(list_number)
                if list_num <= 0:
                    errors.append("List number must be a positive integer")
            except (ValueError, TypeError):
                errors.append("List number must be a valid number")

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        # Determine session duration based on program   
        selected_program = Program.objects.filter(pk=program_id).first()
        active_session = active_session_required(program_id)
        if not active_session:
                errors.append("No active session found for the selected program.")

        # Validate valid_until date
        valid_until_dt = None
        if valid_until:
            try:
                # Try strict YYYY-MM-DD format first
                valid_until_dt = datetime.strptime(valid_until, '%Y-%m-%d')
            except ValueError:
                try:
                    # Fallback to flexible parsing with dateutil
                    valid_until_dt = parser.parse(valid_until)
                    # Convert to YYYY-MM-DD for consistency
                    valid_until = valid_until_dt.strftime('%Y-%m-%d')
                except ValueError:
                    errors.append(f"Invalid date format for valid until: '{valid_until}'. Use YYYY-MM-DD (e.g., 2025-07-18).")
                    logger.warning(f"Invalid date format for valid_until: '{valid_until}'")
            if valid_until_dt and valid_until_dt.date() < date.today():
                errors.append("Valid until date must be in the future.")
        else:
            errors.append("Valid until date is required.")

        if errors:
            logger.error(f"Validation errors: {errors}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors})
            return render(request, 'fee_management/generate_merit_list.html', {
                'errors': errors,
                'programs': programs
            })
        
        if list_number:
            list_num = int(list_number)
            if list_num == 1:
                total_seats = total_seats  # Default total seats for the first merit list
            else:
                previous_list = MeritList.objects.filter(
                program=selected_program,
                list_number=list_num - 1,
                shift=shift
                ).first()
                total_seats = previous_list.total_seats-previous_list.seccured_seats 
# Default to 50 if no previous list
        try:
            program = Program.objects.get(pk=program_id)
            if total_seats <= 0:
                errors.append("Program has no seats defined or invalid seat count.")
                logger.error(f"Program {program.name} has invalid total_seats: {total_seats}")
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors})
                return render(request, 'fee_management/generate_merit_list.html', {
                    'errors': errors,
                    'programs': programs
                })

            logger.info(f"Generating merit list #{list_num} for program {program.name}, shift {shift} with {total_seats} total seats")
            excluded_applicants = MeritListEntry.objects.filter(
                merit_list__program=program,
                merit_list__shift=shift,
                merit_list__list_number__lt=list_num
            ).values_list('applicant_id', flat=True)
            # Get applicants with paid status
            applicants = Applicant.objects.filter(
                program=program,
                status='accepted',
                shift__iexact=shift,
                session=active_session,
                payment__status='paid'
            ).exclude(id__in=excluded_applicants).select_related('program').prefetch_related('academic_qualifications').distinct()

            relevant_applicants = []
            for applicant in applicants:
                qualification = applicant.academic_qualifications.order_by('-passing_year').first()
                if qualification and qualification.marks_obtained and qualification.total_marks:
                    percentage = (qualification.marks_obtained / qualification.total_marks) * 100
                    relevant_applicants.append((applicant, qualification, percentage))

            relevant_applicants.sort(key=lambda x: x[2], reverse=True)

            if not relevant_applicants:
                errors.append("No applicants found with paid status for the selected program and shift.")
                logger.warning(f"No paid applicants for program {program.name}, shift {shift}, session {active_session}")
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors})
                return render(request, 'fee_management/generate_merit_list.html', {
                    'errors': errors,
                    'programs': programs
                })

            admitted_count = 0
            relevant_applicants_for_current = []
            if list_num > 1:
                prev_list_num = list_num - 1
                try:
                    previous_list = MeritList.objects.get(program=program, list_number=prev_list_num, shift=shift)
                    if previous_list.valid_until.date() >= date.today() and previous_list.valid_until.time() > datetime.now().time():
                        errors.append(
                            f"Cannot generate list #{list_num} because the previous list is still valid until "
                            f"{previous_list.valid_until.strftime('%d-%b-%Y %H:%M')}.")
                    else:
                        admitted_count = MeritListEntry.objects.filter(
                            merit_list__program=program,
                            merit_list__shift=shift,
                            merit_list_list_number_lte=prev_list_num,
                            applicant__status='admitted'
                        ).count()
                        logger.info(f"Admitted count for program {program.name}, shift {shift}, list #{list_num}: {admitted_count}")
                        seats_for_current_list = total_seats - admitted_count
                        logger.info(f"Seats available for list #{list_num}: {seats_for_current_list} (total_seats: {total_seats})")
                        if seats_for_current_list <= 0:
                            errors.append(f"No seats available for merit list #{list_num}. All {total_seats} seats have been filled.")
                        else:
                            relevant_applicants_for_current = relevant_applicants[admitted_count:admitted_count + seats_for_current_list]
                            if not relevant_applicants_for_current:
                                errors.append("No more eligible applicants available for this merit list.")
                            logger.info(f"Selected {len(relevant_applicants_for_current)} applicants for list #{list_num}")
                except MeritList.DoesNotExist:
                    errors.append(f"Merit list #{prev_list_num} for {program.name} ({shift} shift) does not exist. Please generate it first.")
            else:
                relevant_applicants_for_current = relevant_applicants[:total_seats]
                logger.info(f"Selected {len(relevant_applicants_for_current)} applicants for first list (total_seats: {total_seats})")

            if errors:
                logger.error(f"Errors generating merit list #{list_num}: {errors}")
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors})
                return render(request, 'fee_management/generate_merit_list.html', {
                    'errors': errors,
                    'programs': programs
                })

            with transaction.atomic():
                merit_list = MeritList.objects.create(
                    program=selected_program,
                    list_number=list_num,
                    shift=shift,
                    academic_session=active_session,
                    total_seats=total_seats,
                    seccured_seats=0,  # Corrected to match model field
                    valid_until=valid_until,
                    notes=notes,
                    is_active=True,
                )
                entries_created = 0
                start_position = 1 if list_num == 1 else admitted_count + 1
                for idx, (applicant, qualification, percentage) in enumerate(relevant_applicants_for_current, start=start_position):
                    MeritListEntry.objects.create(
                        merit_list=merit_list,
                        applicant=applicant,
                        merit_position=idx,
                        relevant_percentage=percentage,
                        qualification_used=qualification,
                        status='selected',
                        passing_year=getattr(qualification, 'passing_year', None),
                        marks_obtained=getattr(qualification, 'marks_obtained', None),
                    )
                    entries_created += 1

                success_message = f'Merit list #{list_num} generated successfully with {entries_created} students.'
                logger.info(f"{success_message} for program {program.name}, shift {shift}")
                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message, 'merit_list_id': merit_list.id})
                else:
                    messages.success(request, success_message)
                    return redirect('fee_management:view_merit_list', merit_list_id=merit_list.id)

        except (Program.DoesNotExist, ValueError, TypeError) as e:
            errors.append(f"An error occurred: {e}")
            logger.error(f"Error generating merit list: {e}")
        except Exception as e:
            errors.append(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Unexpected error generating merit list: {str(e)}")

        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors})
            return render(request, 'fee_management/generate_merit_list.html', {
                'errors': errors,
                'programs': programs
            })

    return render(request, 'fee_management/generate_merit_list.html', {
        'programs': programs,
        'errors': errors
    })


def get_next_list_number(request):
    program_id = request.GET.get('program')
    shift = request.GET.get('shift')
    
    if not program_id or not shift:
        return JsonResponse({'error': 'Program and shift are required'}, status=400)
    
    try:
        program = Program.objects.get(id=program_id)
    except Program.DoesNotExist:
        return JsonResponse({'error': 'Invalid program'}, status=400)
    
    # Fix typo: 'acdemic_session' -> 'academic_session'
    session = active_session_required(program_id)
    
    existing_lists = MeritList.objects.filter(
        program=program,
        shift=shift,
        academic_session=session,     
    ).count() 
    if not existing_lists:
        next_list_number = 1
    else:
        next_list_number = existing_lists + 1

    return JsonResponse({'next_list_number': next_list_number})

@office_required
def view_merit_list(request, merit_list_id):
    merit_list = get_object_or_404(MeritList.objects.select_related('program'), pk=merit_list_id)
    entries = merit_list.entries.select_related('applicant', 'qualification_used').order_by('merit_position')
    
    return render(request, 'fee_management/view_merit_list.html', {
        'merit_list': merit_list,
        'entries': entries
    })
 
from django.utils import timezone
 # Import timezone
@office_required
def manage_merit_lists(request):
    program_id = request.GET.get('program')
    sort = request.GET.get('sort', '-generation_date')
    current_time = timezone.now()  # Use timezone.now() instead of datetime.now()
    merit_lists = MeritList.objects.select_related('program').all()
    for merit_list in merit_lists.filter(is_active=True):
        if merit_list.valid_until <= current_time:
            merit_list.is_active = False
            merit_list.save(update_fields=['is_active'])
            logger.info(f"Deactivated Merit List #{merit_list.list_number}")

    merit_lists = MeritList.objects.select_related('program').all()
    
    if program_id:
        merit_lists = merit_lists.filter(program_id=program_id)
    
    merit_lists = merit_lists.order_by(sort)
    programs = Program.objects.all()
    
    return render(request, 'fee_management/manage_merit_lists.html', {
        'merit_lists': merit_lists,
        'programs': programs,
        'selected_program': program_id,
        'selected_sort': sort
    })

@office_required
def grant_admission_single(request, entry_id):
    entry = get_object_or_404(MeritListEntry, pk=entry_id)
    applicant = entry.applicant

    if applicant.status != 'admitted':        
        # Create Student record
        student, created = Student.objects.get_or_create(
            applicant=applicant,
            defaults={
                'user': applicant.user,
                'program': applicant.program,
                'enrollment_date': date.today(),
            }
        )

        if created:
            # Generate roll numbers for new student
            student.university_roll_no = int(f"{str(applicant.session.start_year)[-2:]}{applicant.program.id:02}{applicant.id:04}")
            student.Registration_number = f"{applicant.session.start_year}-GGCJ-{student.university_roll_no}"
            if applicant.shift == 'morning':
                student.college_roll_no = f"{applicant.program.id:02}{entry.merit_list.seccured_seats + 1:02}"
            else:
                student.college_roll_no = f"{applicant.program.id:02}{entry.merit_list.seccured_seats+ 51:02}"
            student.save()
        # Update entry status
        entry.status = 'admitted'
        entry.save()
        
        # Increment secured seats
        merit_list = entry.merit_list
        merit_list.seccured_seats += 1
        merit_list.save()

        return JsonResponse({
            'success': True,
            'message': f"Admission granted to {applicant.full_name}.",
            'student': {
                'full_name': student.applicant.full_name,
                'university_roll_no': student.university_roll_no,
                'college_roll_no': student.college_roll_no,
                'registration_no':student.Registration_number,
                'program': student.program.name,
                'shift': student.applicant.shift,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f"{applicant.full_name} is already admitted."
        })









@login_required
def manual_course_enrollment(request):
    context = {
        'semesters': Semester.objects.none(),
        'courses': CourseOffering.objects.none(),
    }

    if request.method == 'POST':
        step = request.POST.get('step')

        if step == 'lookup':
            university_roll_no = request.POST.get('university_roll_no')
            if not university_roll_no:
                messages.error(request, "Please enter a university roll number.")
                return render(request, 'fee_management/manual_course_enrollment.html', context)
                
            try:
                student = Student.objects.select_related('applicant').get(university_roll_no=university_roll_no)
                context['student'] = student
                student_program = student.applicant.program
                
                # Get the student's department from their program
                student_department = student_program.department
                
                # Filter semesters by the student's department
                context['semesters'] = Semester.objects.filter(
                    program__department=student_department
                ).select_related('session').order_by('start_time', 'number')
                
                # Filter courses by the student's department
                courses = CourseOffering.objects.filter(
                    program__department=student_department
                ).select_related('course', 'semester', 'academic_session').order_by('academic_session__start_year', 'course__code')
                
                # Check for previously taken courses
                previously_taken_courses = set(
                    CourseEnrollment.objects.filter(
                        student_semester_enrollment__student=student,
                        course_offering__course__in=[c.course for c in courses]
                    ).values_list('course_offering__course_id', flat=True)
                )
                
                # Create course data with repeat status
                course_data = []
                for course in courses:
                    is_repeat = course.course.id in previously_taken_courses
                    course_data.append({
                        'course': course,
                        'is_repeat': is_repeat
                    })
                
                context['courses_json'] = [
                    {
                        'id': course.id,
                        'name': f"{course.course.code} - {course.course.name}",
                        'semester_id': course.semester.id,
                        'is_repeat': course.course.id in previously_taken_courses
                    }
                    for course in courses
                ]
                context['course_data'] = course_data
                
                print(f"Found {context['semesters'].count()} semesters and {len(courses)} courses for program: {student_program}")
                return render(request, 'fee_management/manual_course_enrollment.html', context)
                
            except Student.DoesNotExist:
                messages.error(request, f"No student found with university roll number {university_roll_no}.")
                return render(request, 'fee_management/manual_course_enrollment.html', context)
                
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, 'fee_management/manual_course_enrollment.html', context)

        elif step == 'enroll':
            student_id = request.POST.get('student_id')
            semester_id = request.POST.get('semester')
            course_ids = request.POST.getlist('courses')

            if not course_ids:
                messages.error(request, "Please select at least one course.")
                if student_id:
                    try:
                        context['student'] = Student.objects.get(pk=student_id)
                    except Student.DoesNotExist:
                        pass
                return render(request, 'fee_management/manual_course_enrollment.html', context)

            try:
                with transaction.atomic():
                    student = Student.objects.select_related('applicant').get(pk=student_id)
                    semester = Semester.objects.get(pk=semester_id)
                    semester_enrollment, created = StudentSemesterEnrollment.objects.get_or_create(
                        student=student,
                        semester=semester,
                        defaults={
                            'status': 'enrolled',
                            'enrollment_date': timezone.now().date()
                        }
                    )

                    enrolled_courses = []
                    repeat_enrollments = []
                    previous_enrollments = CourseEnrollment.objects.filter(
                        student_semester_enrollment__student=student,
                        course_offering__course__in=[CourseOffering.objects.get(pk=cid).course for cid in course_ids]
                    ).select_related('course_offering__course')
                    previous_course_ids = {e.course_offering.course.id for e in previous_enrollments}
                    
                    for course_id in course_ids:
                        course_offering = CourseOffering.objects.get(pk=course_id)
                        is_repeat = course_offering.course.id in previous_course_ids
                        existing_enrollment = CourseEnrollment.objects.filter(
                            student_semester_enrollment=semester_enrollment,
                            course_offering=course_offering
                        ).first()
                        
                        if existing_enrollment:
                            messages.info(request, f"Already enrolled in {course_offering.course.name} for this semester.")
                            continue
                            
                        enrollment = CourseEnrollment.objects.create(
                            student_semester_enrollment=semester_enrollment,
                            course_offering=course_offering,
                            status='enrolled',
                            is_repeat=is_repeat
                        )
                        
                        if is_repeat:
                            repeat_enrollments.append(course_offering.course.name)
                        enrolled_courses.append(course_offering.course.name)
                    
                    if repeat_enrollments:
                        messages.info(
                            request, 
                            f"The following courses are being repeated: {', '.join(repeat_enrollments)}. "
                            "The repeat flag has been set for these enrollments."
                        )

                    if enrolled_courses:
                        messages.success(
                            request, 
                            f"Successfully enrolled {student.applicant.full_name} in: {', '.join(enrolled_courses)}"
                        )
                    else:
                        messages.info(request, "No new courses were enrolled. The student was already enrolled in all selected courses.")
                    
                    return redirect('fee_management:manual_course_enrollment')

            except Student.DoesNotExist:
                messages.error(request, "Selected student does not exist.")
            except Semester.DoesNotExist:
                messages.error(request, "Selected semester does not exist.")
            except CourseOffering.DoesNotExist:
                messages.error(request, "One or more selected courses are invalid.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                
            try:
                context['student'] = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                pass
                
            return render(request, 'fee_management/manual_course_enrollment.html', context)

    return render(request, 'fee_management/manual_course_enrollment.html', context)






@login_required
def settings(request):
    user = request.user
    
    if request.method == 'POST':
        # Check which form was submitted
        if 'update_account' in request.POST:
            form = OfficerUpdateForm(
                request.POST, 
                request.FILES, 
                instance=user
            )
            if form.is_valid():
                form.save()
                messages.success(request, 'Your account has been updated successfully!')
                return redirect('fee_management:settings')
        elif 'change_password' in request.POST:
            form = OfficerPasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('fee_management:settings')
            else:
                # If password form is invalid, show errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect('fee_management:settings?tab=security')
    else:
        # Initialize forms
        form = OfficerUpdateForm(instance=user)
        password_form = OfficerPasswordChangeForm(user)
    
    return render(request, 'fee_management/settings.html', {
        'active_tab': request.GET.get('tab', 'account'),
        'form': form,
        'password_form': password_form,
    })


def update_account(request):
    if request.method == 'POST':
        user = request.user
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        
        if user_form.is_valid():
            user_form.save()
            
            # Update officer profile if it exists
            if hasattr(user, 'officestaff_profile'):
                profile = user.officestaff_profile
                profile.contact_no = request.POST.get('contact_no', '')
                profile.save()
            
            messages.success(request, 'Account updated successfully.')
            return redirect('fee_management:settings')
        else:
            messages.error(request, 'Error updating account. Please check the form.')
    return redirect('fee_management:settings')


def change_password(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
        else:
            messages.error(request, 'Error changing password. Please check the form.')
    return redirect('fee_management:settings')

from .models import OfficeToHODNotification
@login_required
def notification_list(request):
    notifications = OfficeToHODNotification.objects.order_by('-created_at')
    return render(request, 'fee_management/office_notices_list.html', {'notifications': notifications})

@office_required
def office_notice_detail_view(request, pk):
    notification = get_object_or_404(OfficeToHODNotification, pk=pk)
    return render(request, "fee_management/office_notices_detail.html", {
        "notification": notification
    })

office_required
@require_http_methods(["GET", "POST"])
def office_notice_view(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        department_ids = request.POST.getlist("departments")
        attached_file = request.FILES.get("attached_file")
        user = request.user

        if not title:
            messages.error(request, "Title is required.")
        if not message:
            messages.error(request, "Message is required.")
        if not department_ids:
            messages.error(request, "Please select at least one department.")

        if messages.get_messages(request):
            # There are error messages, re-render form with errors
            departments = Department.objects.all()
            return render(request, "fee_management/office_notices.html", {
                "departments": departments,
                "title": title,
                "message": message,
                "selected_departments": list(map(int, department_ids)),
            })

        # Create notification
        notification = OfficeToHODNotification.objects.create(
            title=title,
            message=message,
            sent_by=user,
            attached_file=attached_file if attached_file else None,
        )
        # Add departments
        departments = Department.objects.filter(id__in=department_ids)
        notification.departments.set(departments)
        notification.save()

        # TODO: Implement actual notification sending logic here (e.g., email to department heads)

        messages.success(request, "Notification sent successfully.")
        return redirect("fee_management:office_notice")

    else:
        departments = Department.objects.all()
        return render(request, "fee_management/office_notices.html", {
            "departments": departments,
        })