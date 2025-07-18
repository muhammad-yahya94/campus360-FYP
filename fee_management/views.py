import os
import tempfile
import subprocess
import logging
from django.urls import reverse 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from faculty_staff.models import OfficeStaff, Office
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from .models import SemesterFee, FeeType, FeeVoucher, StudentFeePayment, FeeToProgram, MeritList, MeritListEntry
from admissions.models import Applicant, AcademicSession, AcademicQualification, ExtraCurricularActivity
from academics.models import Program, Semester  # Added Semester import
from students.models import Student
from decimal import Decimal
from django import forms
from django.db.models import Q, F
from django.utils.timezone import now
from django.utils import timezone
from datetime import date, datetime, timedelta ,timezone
from urllib.parse import urlencode 
from admissions.models import AcademicSession
from payment.models import Payment
from django.forms import modelformset_factory
from admissions.forms import ApplicantForm, AcademicQualificationForm, ExtraCurricularActivityForm

@login_required
def add_student_manually(request):
    AcademicQualificationFormSet = modelformset_factory(AcademicQualification, form=AcademicQualificationForm, extra=1)
    ExtraCurricularActivityFormSet = modelformset_factory(ExtraCurricularActivity, form=ExtraCurricularActivityForm, extra=1)

    if request.method == 'POST':
        applicant_form = ApplicantForm(request.POST, request.FILES)
        qualification_formset = AcademicQualificationFormSet(request.POST, request.FILES, prefix='qualifications')
        activity_formset = ExtraCurricularActivityFormSet(request.POST, request.FILES, prefix='activities')

        if applicant_form.is_valid() and qualification_formset.is_valid() and activity_formset.is_valid():
            # Save applicant
            applicant = applicant_form.save(commit=False)
            applicant.user = request.user  # Or however you want to assign the user
            applicant.status = 'accepted'  # Set status to accepted
            applicant.save()

            # Save qualifications
            for form in qualification_formset:
                if form.cleaned_data:
                    qualification = form.save(commit=False)
                    qualification.applicant = applicant
                    qualification.save()

            # Save activities
            for form in activity_formset:
                if form.cleaned_data:
                    activity = form.save(commit=False)
                    activity.applicant = applicant
                    activity.save()
            
            # Create Student record
            student = Student.objects.create(
                applicant=applicant,
                user=applicant.user,
                program=applicant.program,
                enrollment_date=date.today()
            )
            
            # Generate roll numbers
            # University roll number format: last 2 digits of start year + program id (2 digits) + applicant id (4 digits)
            student.university_roll_no = int(f"{str(applicant.session.start_year)[-2:]}{applicant.program.id:02}{applicant.id:04}")
            
            # Registration number format: start year-GGCJ-university roll number
            student.Registration_number = f"{applicant.session.start_year}-GGCJ-{student.university_roll_no}"
            
            # College roll number format: (program_id + 3) followed by sequential number
            # Base prefix is (program_id + 3)
            roll_prefix = applicant.program.id + 3
            
            # Find the highest existing college roll number with this prefix
            highest_roll = Student.objects.filter(
                college_roll_no__startswith=str(roll_prefix)
            ).order_by('-college_roll_no').first()
            
            if highest_roll and highest_roll.college_roll_no:
                # Extract the numeric part and increment
                try:
                    # Get the last two digits and increment
                    last_digits = int(str(highest_roll.college_roll_no)[-2:])
                    student.college_roll_no = int(f"{roll_prefix}{(last_digits + 1):02d}")
                except (ValueError, IndexError):
                    # Fallback if parsing fails
                    student.college_roll_no = int(f"{roll_prefix}00")
            else:
                # No existing students with this prefix, start with 00
                student.college_roll_no = int(f"{roll_prefix}00")
            
            student.save()
            
            messages.success(request, f'Student {applicant.full_name} added successfully with University Roll No: {student.university_roll_no}')
            return redirect('fee_management:student_management')  # Redirect to student management page

    else:
        applicant_form = ApplicantForm()
        qualification_formset = AcademicQualificationFormSet(queryset=AcademicQualification.objects.none(), prefix='qualifications')
        activity_formset = ExtraCurricularActivityFormSet(queryset=ExtraCurricularActivity.objects.none(), prefix='activities')

    context = {
        'applicant_form': applicant_form,
        'qualification_formset': qualification_formset,
        'activity_formset': activity_formset,
    }
    return render(request, 'fee_management/add_student_manually.html', context)

# Existing views (unchanged except for applicant_verification)
def treasure_office_view(request):
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
        user = authenticate(request, username=email, password=password)
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

def office_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not is_officestaff(request.user):
            messages.error(request, 'You do not have Office Staff access.')
            return redirect('fee_management:office_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@office_required
def applicant_verification(request):
    applicants = Applicant.objects.select_related('program', 'department', 'faculty').all()
    
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
    valid_sort_fields = ['full_name', '-full_name', 'program__name', '-program__name', 'shift', '-shift']
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



from academics.models import Department

@office_required
def student_management(request):
    students = Student.objects.select_related('applicant', 'program').all()
    
    # Get query parameters
    session_id = request.GET.get('session', '')
    department_id = request.GET.get('department', '')
    program_id = request.GET.get('program', '')
    search = request.GET.get('search', '')
    
    # Apply filters
    if session_id:
        students = students.filter(applicant__session__id=session_id)
    if department_id:
        students = students.filter(program__department__id=department_id)
    if program_id:
        students = students.filter(program__id=program_id)
    if search:
        students = students.filter(
            Q(applicant__full_name__icontains=search) |
            Q(university_roll_no__icontains=search) |
            Q(Registration_number__icontains=search)
        )
        
    # Pagination
    paginator = Paginator(students, 25)  # Show 25 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    sessions = AcademicSession.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()
    
    context = {
        'students': page_obj,
        'sessions': sessions,
        'departments': departments,
        'programs': programs,
        'selected_session': session_id,
        'selected_department': department_id,
        'selected_program': program_id,
        'search_query': search,
    }
    return render(request, 'fee_management/student_management.html', context)

@office_required
def admission_fee(request):
    return render(request, 'fee_management/admission_fee.html')

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
            Q(amount__icontains=query) |
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
            print('feetype_id:', request.POST.get('feetype_id'))
            
            # Convert empty string to None for ID fields
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
                        # Update existing FeeType
                        fee_type = get_object_or_404(FeeType, pk=feetype_id)
                        fee_type.name = name
                        fee_type.description = description
                        fee_type.is_active = is_active
                        fee_type.save()
                        messages.success(request, 'Fee Type updated successfully.')
                    else:
                        # Create new FeeType
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
            amount = request.POST.get('amount')
            total_amount = request.POST.get('total_amount')
            shift = request.POST.get('shift')
            computer_fee = request.POST.get('computer_fee') == 'on'
            computer_fee_amount = request.POST.get('computer_fee_amount', '0')
            examination_fund = request.POST.get('examination_fund') == 'on'
            examination_fund_amount = request.POST.get('examination_fund_amount', '0')
            tuition_fee = request.POST.get('tuition_fee') == 'on'
            tuition_fee_amount = request.POST.get('tuition_fee_amount', '0')
            others = request.POST.get('others') == 'on'
            others_amount = request.POST.get('others_amount', '0')
            evening_fund = request.POST.get('evening_fund') == 'on'
            evening_fund_amount = request.POST.get('evening_fund_amount', '0')
            is_active = request.POST.get('is_active') == 'on'
            academic_session_id = request.POST.get('academic_session')
            program_ids = request.POST.getlist('programs')
            semester_ids = request.POST.getlist('semester_number')
            
            # Validation
            if not fee_type_id:
                errors.append("Fee Type is required.")
            if not amount:
                errors.append("Amount is required.")
            if not shift:
                errors.append("Shift is required.")
            if not total_amount:
                errors.append("Total Amount is required.")
            if not academic_session_id:
                errors.append("Academic Session is required.")
            if not program_ids:
                errors.append("At least one Program is required.")
            if not semester_ids:
                errors.append("At least one Semester is required.")
            
            try:
                amount = Decimal(amount) if amount else None
                total_amount = Decimal(total_amount) if total_amount else None
                computer_fee_amount = Decimal(computer_fee_amount) if computer_fee_amount else Decimal('0')
                examination_fund_amount = Decimal(examination_fund_amount) if examination_fund_amount else Decimal('0')
                tuition_fee_amount = Decimal(tuition_fee_amount) if tuition_fee_amount else Decimal('0')
                others_amount = Decimal(others_amount) if others_amount else Decimal('0')
                evening_fund_amount = Decimal(evening_fund_amount) if evening_fund_amount else Decimal('0')
            except (ValueError, TypeError):
                errors.append("Numeric fields must be valid numbers.")
            
            if computer_fee and computer_fee_amount <= 0:
                errors.append("Computer Fee Amount must be greater than 0 when Computer Fee is checked.")
            if examination_fund and examination_fund_amount <= 0:
                errors.append("Examination Fund Amount must be greater than 0 when Examination Fund is checked.")
            if tuition_fee and tuition_fee_amount <= 0:
                errors.append("Tuition Fee Amount must be greater than 0 when Tuition Fee is checked.")
            if others and others_amount <= 0:
                errors.append("Others Amount must be greater than 0 when Others is checked.")
            if evening_fund and evening_fund_amount <= 0:
                errors.append("Evening Fund Amount must be greater than 0 when Evening Fund is checked.")
            
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
                    edit_fee.amount = amount
                    edit_fee.total_amount = total_amount
                    edit_fee.shift = shift
                    edit_fee.computer_fee = computer_fee
                    edit_fee.computer_fee_amount = computer_fee_amount
                    edit_fee.examination_fund = examination_fund
                    edit_fee.examination_fund_amount = examination_fund_amount
                    edit_fee.tuition_fee = tuition_fee
                    edit_fee.tuition_fee_amount = tuition_fee_amount
                    edit_fee.others = others
                    edit_fee.others_amount = others_amount
                    edit_fee.evening_fund = evening_fund
                    edit_fee.evening_fund_amount = evening_fund_amount
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
                        amount=amount,
                        total_amount=total_amount,
                        shift=shift,
                        computer_fee=computer_fee,
                        computer_fee_amount=computer_fee_amount,
                        examination_fund=examination_fund,
                        examination_fund_amount=examination_fund_amount,
                        tuition_fee=tuition_fee,
                        tuition_fee_amount=tuition_fee_amount,
                        others=others,
                        others_amount=others_amount,
                        evening_fund=evening_fund,
                        evening_fund_amount=evening_fund_amount,
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
            ).select_related('program').distinct()
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
def fee_verification(request):
    context = {}
    
    if request.method == 'POST':
        voucher_id = request.POST.get('voucher_id')
        action = request.POST.get('action')
        
        if not voucher_id:
            messages.error(request, 'Voucher ID is required.')
            return redirect('fee_management:fee_verification')
            
        try:
            voucher = FeeVoucher.objects.select_related(
                'student', 'semester_fee', 'semester'
            ).get(voucher_id=voucher_id)
            
            if action == 'verify':
                # Check if already paid
                if voucher.is_paid:
                    messages.warning(request, 'This voucher has already been marked as paid.')
                    payment = voucher.payment
                else:
                    # Check if payment already exists and is not linked to any other voucher
                    payment = StudentFeePayment.objects.filter(
                        student=voucher.student,
                        semester_fee=voucher.semester_fee
                    ).exclude(voucher__isnull=False).first()
                    
                    try:
                        if not payment:
                            # Create new payment record
                            payment = StudentFeePayment.objects.create(
                                student=voucher.student,
                                semester_fee=voucher.semester_fee,
                                amount_paid=voucher.semester_fee.total_amount,
                                remarks=f'Payment verified against voucher {voucher_id}'
                            )
                        
                        # Mark voucher as paid and link to payment
                        if not voucher.is_paid:  # Double check before marking as paid
                            voucher.mark_as_paid(payment)
                            messages.success(
                                request, 
                                f'Payment of {voucher.semester_fee.total_amount} PKR has been recorded ' 
                                f'and voucher {voucher_id} marked as paid.'
                            )
                    except ValueError as e:
                        messages.error(request, str(e))
                        return redirect('fee_management:fee_verification')
                    
                    messages.success(
                        request, 
                        f'Payment of {voucher.semester_fee.total_amount} PKR has been recorded ' 
                        f'and voucher {voucher_id} marked as paid.'
                    )
            
            context.update({
                'voucher': voucher,
                'student': voucher.student,
                'semester_fee': voucher.semester_fee,
                'payment_exists': bool(voucher.payment or (action == 'verify' and payment))
            })
            
        except FeeVoucher.DoesNotExist:
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


@office_required
def generate_voucher(request):
    errors = []
    
    if request.method == 'POST':
        roll_no = request.POST.get('university_roll_no')
        semester_id = request.POST.get('semester')
        
        if not roll_no:
            errors.append("University Roll Number is required.")
        if not semester_id:
            errors.append("Semester is required.")
        
        try:
            student = Student.objects.get(university_roll_no=roll_no)
        except Student.DoesNotExist:
            errors.append("Student with this roll number does not exist.")
            return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        try:
            semester = Semester.objects.get(pk=semester_id)
        except Semester.DoesNotExist:
            errors.append("Invalid semester selected.")
            return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        # Get student's shift from their program or applicant info
        student_shift = getattr(student.applicant, 'shift', None) or 'morning'  # Default to morning if shift not set
        
        # Find matching SemesterFee for student's program, semester, shift and active session
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
                return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
        semester_fee = fee_to_program.SemesterFee
        
        # Check or create voucher
        voucher, created = FeeVoucher.objects.get_or_create(
            student=student,
            semester_fee=semester_fee,
            semester=semester,
            defaults={
                'due_date': date.today() + timedelta(days=7),
                'office': request.user.office if hasattr(request.user, 'office') else None
            }
        )
        
        # Prepare context for HTML
        generated_at = datetime.now().strftime('%d %B %Y %I:%M %p %Z')  # Current date and time
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
            'amount': str(semester_fee.amount),
            'computer_fee': semester_fee.computer_fee,
            'computer_fee_amount': str(semester_fee.computer_fee_amount) if semester_fee.computer_fee else '0',
            'examination_fund': semester_fee.examination_fund,
            'examination_fund_amount': str(semester_fee.examination_fund_amount) if semester_fee.examination_fund else '0',
            'tuition_fee': semester_fee.tuition_fee,
            'tuition_fee_amount': str(semester_fee.tuition_fee_amount) if semester_fee.tuition_fee else '0',
            'others': semester_fee.others,
            'others_amount': str(semester_fee.others_amount) if semester_fee.others else '0',
            'evening_fund': semester_fee.evening_fund,
            'evening_fund_amount': str(semester_fee.evening_fund_amount) if semester_fee.evening_fund else '0',
            'total_amount': str(semester_fee.total_amount),
            'due_date': voucher.due_date.strftime('%d %B %Y'),
            'generated_at': generated_at,
        }
        
        return render(request, 'fee_management/voucher.html', context)
    
    return render(request, 'fee_management/generate_voucher.html', {'errors': errors})

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from datetime import datetime, date
import logging
from payment.models import Payment
from .models import Program, Applicant,AcademicSession, MeritList, MeritListEntry
from django.db.models import F
from dateutil import parser

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
                total_seats = 50  # Default total seats for the first merit list
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
                            merit_list__list_number__lte=prev_list_num,
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

@office_required
def view_merit_list(request, merit_list_id):
    merit_list = get_object_or_404(MeritList.objects.select_related('program'), pk=merit_list_id)
    entries = merit_list.entries.select_related('applicant', 'qualification_used').order_by('merit_position')
    
    return render(request, 'fee_management/view_merit_list.html', {
        'merit_list': merit_list,
        'entries': entries
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
 

from django.utils import timezone  # Import timezone
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
