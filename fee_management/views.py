import os
import tempfile
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from faculty_staff.models import OfficeStaff
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.conf import settings
from django.http import HttpResponse

from .models import SemesterFee, FeeType, FeeVoucher
from academics.models import Program
from admissions.models import AcademicSession
from fee_management.models import FeeToProgram
from students.models import Student
from decimal import Decimal 
from django import forms
from django.db.models import Q
from datetime import date, datetime, timedelta
import os
import tempfile
import subprocess

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

def office_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not is_officestaff(request.user):
            messages.error(request, 'You do not have Office Staff access.')
            return redirect('fee_management:office_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@office_required
def applicant_verification(request):
    return render(request, 'fee_management/applicant_verification.html')

@office_required
def student_management(request):
    return render(request, 'fee_management/student_management.html')

@office_required
def admission_fee(request):
    return render(request, 'fee_management/admission_fee.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import SemesterFee, FeeType, AcademicSession, Program, FeeToProgram, Semester
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.http import JsonResponse

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
def fee_verification(request):
    return render(request, 'fee_management/fee_verification.html')

@office_required
def get_semesters_by_roll(request):
    roll_no = request.GET.get('roll_no')
    if roll_no:
        try:
            student = Student.objects.get(university_roll_no=roll_no)
            session = student.applicant.session
            semesters = Semester.objects.filter(
                program=student.program,
                session=session,
            ).select_related('program')
            print(semesters)
            semesters_data = [
                {
                    'id': semester.pk,
                    'name': semester.name,
                    'program_name': semester.program.name,
                    'session': semester.session.name,
                }
                for semester in semesters
            ]
            return JsonResponse({'semesters': semesters_data})
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student with this roll number does not exist.'})
    return JsonResponse({'error': 'Roll number is required.'})


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