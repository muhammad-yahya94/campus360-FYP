import os
import tempfile
import subprocess
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from faculty_staff.models import OfficeStaff
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import HttpResponse, Http404

from .models import SemesterFee, FeeType, FeeVoucher, StudentFeePayment
from students.models import Student
from academics.models import Program
from admissions.models import AcademicSession
from fee_management.models import FeeToProgram
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
                        if not payment:
                            payment = StudentFeePayment.objects.create(
                                student=voucher.student,
                                semester_fee=voucher.semester_fee,
                                amount_paid=voucher.semester_fee.total_amount,
                                remarks=f'Payment verified against voucher {voucher_id}'
                            )
                        
                        if not voucher.is_paid:
                            voucher.mark_as_paid(payment)
                            success_message = (
                                f'Payment of {voucher.semester_fee.total_amount} PKR has been recorded ' 
                                f'and voucher {voucher_id} marked as paid.'
                            )
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                context.update({
                                    'voucher': voucher,
                                    'student': voucher.student,
                                    'semester_fee': voucher.semester_fee,
                                    'payment_exists': bool(voucher.payment)
                                })
                                html = render_to_string('fee_management/voucher_details.html', context, request)
                                return JsonResponse({'html': html, 'message': success_message})
                            messages.success(request, success_message)
                    except ValueError as e:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'error': str(e)}, status=400)
                        messages.error(request, str(e))
                        return redirect('fee_management:fee_verification')
            
            context.update({
                'voucher': voucher,
                'student': voucher.student,
                'semester_fee': voucher.semester_fee,
                'payment_exists': bool(voucher.payment)
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






def student_generate_voucher(request):
    """
    View for students to generate their own fee vouchers.
    Students can only generate vouchers for themselves.
    """
    errors = []
    
    if not hasattr(request.user, 'student_profile'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'errors': ['Student profile not found.']}, status=400)
        return redirect('login')
    
    student = request.user.student_profile
    
    if request.method == 'GET':
        # Get all semesters for the student's program and session
        all_semesters = Semester.objects.filter(program=student.program, session=student.applicant.session)
        
        # Get IDs of semesters that already have paid vouchers
        paid_semester_ids = FeeVoucher.objects.filter(
            student=student,
            is_paid=True
        ).values_list('semester_id', flat=True)
        
        # Exclude already paid semesters
        available_semesters = all_semesters.exclude(id__in=paid_semester_ids)
        
        print("\n=== DEBUG: Available Semesters ===")
        print(f"All semesters: {list(all_semesters.values_list('name', flat=True))}")
        print(f"Paid semester IDs: {list(paid_semester_ids)}")
        print(f"Available semesters: {list(available_semesters.values_list('name', flat=True))}")
        print("==============================\n")
        
        return render(request, 'fee_management/student_generate_voucher.html', {
            'semesters': available_semesters,
            'errors': errors
        })
    
    # Handle POST request (form submission)
    semester_id = request.POST.get('semester')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not semester_id:
        errors.append("Semester is required.")
        if is_ajax:
            return JsonResponse({'errors': errors}, status=400)
        semesters = Semester.objects.filter(program=student.program, session=student.session)
        return render(request, 'fee_management/student_generate_voucher.html', {
            'semesters': semesters,
            'errors': errors
        })
    
    try:
        semester = Semester.objects.get(pk=semester_id)
    except Semester.DoesNotExist:
        errors.append("Invalid semester selected.")
        if is_ajax:
            return JsonResponse({'errors': errors}, status=400)
        semesters = Semester.objects.filter(program=student.program, session=student.session)
        return render(request, 'fee_management/student_generate_voucher.html', {
            'semesters': semesters,
            'errors': errors
        })
    
    # Get student's shift (assuming it's stored in the student model)
    student_shift = getattr(student, 'shift', 'morning').lower()
    
    # Find matching fee program
    fee_to_program = FeeToProgram.objects.filter(
        semester_number=semester,
        programs=student.program,
        academic_session=student.applicant.session,
        SemesterFee__shift__iexact=student_shift
    ).first()
    
    if not fee_to_program:
        # Try without shift filter if no match found
        fee_to_program = FeeToProgram.objects.filter(
            semester_number=semester,
            programs=student.program,
            academic_session=student.applicant.session
        ).first()
        
        if not fee_to_program:
            error_msg = f"No fee schedule found for {student_shift} shift in this program and semester."
            if is_ajax:
                return JsonResponse({'errors': [error_msg]}, status=400)
            errors.append(error_msg)
            semesters = Semester.objects.filter(program=student.program, session=student.applicant.session)
            return render(request, 'fee_management/student_generate_voucher.html', {
                'semesters': semesters,
                'errors': errors
            })
    
    semester_fee = fee_to_program.SemesterFee
    
    # Get the office (use default or first available)
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
    
    # Update office if it wasn't set during creation
    if not created and not voucher.office and office:
        voucher.office = office
        voucher.save(update_fields=['office'])
    
    # Prepare dynamic fees dictionary
    dynamic_fees = {}
    if semester_fee.dynamic_fees:
        try:
            # If dynamic_fees is a string, try to parse it as JSON
            if isinstance(semester_fee.dynamic_fees, str):
                print("Dynamic fees is a string, attempting to parse as JSON")
                dynamic_fees = json.loads(semester_fee.dynamic_fees)
            # If it's already a dictionary, use it directly
            elif isinstance(semester_fee.dynamic_fees, dict):
                print("Dynamic fees is already a dictionary")
                dynamic_fees = semester_fee.dynamic_fees
            else:
                print(f"Unexpected type for dynamic_fees: {type(semester_fee.dynamic_fees)}")
                try:
                    dynamic_fees = dict(semester_fee.dynamic_fees)
                    print("Converted to dictionary successfully")
                except (TypeError, ValueError) as e:
                    print(f"Could not convert to dictionary: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Problematic JSON string: {semester_fee.dynamic_fees}")
            errors.append("Invalid fee structure in database.")
        except Exception as e:
            print(f"Error parsing dynamic_fees: {e}")
            errors.append("Error processing fee structure.")
    else:
        print("No dynamic_fees found in semester_fee")
        # Fallback: Use total_amount as a single fee head
        dynamic_fees = {"Semester Fee": float(semester_fee.total_amount)}
        print(f"Fallback dynamic_fees: {dynamic_fees}")
    
    # Validate dynamic_fees
    if not dynamic_fees:
        errors.append("No fee details available for this semester.")
        if is_ajax:
            return JsonResponse({'errors': errors}, status=400)
        semesters = Semester.objects.filter(program=student.program, session=student.applicant.session)
        return render(request, 'fee_management/student_generate_voucher.html', {
            'semesters': semesters,
            'errors': errors
        })
    
    print("\n=== DEBUGGING FEE DATA ===")
    print(f"Semester Fee ID: {semester_fee.id}")
    print(f"Dynamic Fees Type: {type(semester_fee.dynamic_fees)}")
    print(f"Dynamic Fees Content: {semester_fee.dynamic_fees}")
    print(f"Final dynamic_fees: {dynamic_fees}")
    print("=== END DEBUGGING ===\n")
    
    # Prepare context for template
    generated_at = timezone.now().strftime('%d %B %Y %I:%M %p PKT')
    context = {
        'voucher_id': voucher.voucher_id,
        'student_name': f"{student.applicant.full_name}",
        'cnic': getattr(student.applicant, 'cnic', 'N/A'),
        'father_name': getattr(student.applicant, 'father_name', 'N/A'),
        'program': student.program.name,
        'semester': semester.name,
        'shift': student_shift.title(),
        'academic_session': student.applicant.session.name,
        'fee_type': semester_fee.fee_type.name,
        'dynamic_fees': dynamic_fees,  # Use the parsed or fallback dictionary
        'total_amount': str(semester_fee.total_amount),
        'due_date': voucher.due_date.strftime('%d %B %Y'),
        'office_name': office.name if office else 'N/A',
        'office_address': office.location if office else 'N/A',
        'office_contact': office.contact_phone if office else 'N/A',
        'generated_at': generated_at,
    }
    
    if is_ajax:
        # Render the voucher HTML
        voucher_html = render_to_string('fee_management/voucher.html', context, request)
        return JsonResponse({
            'success': True,
            'voucher_html': voucher_html,
            'voucher_id': str(voucher.voucher_id)
        })
    
    return render(request, 'fee_management/voucher.html', context)


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
                return render(request, 'fee_management/generate_voucher.html', {'errors': errors})
        
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
        
        # Update office if it wasn't set during creation
        if not created and not voucher.office and office:
            voucher.office = office
            voucher.save(update_fields=['office'])
        
        # Prepare context for HTML
        generated_at = datetime.now().strftime('%d %B %Y %I:%M %p PKT')  # Use PKT timezone
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
            'dynamic_fees': semester_fee.dynamic_fees,  # Dictionary of fee heads and amounts
            'total_amount': str(semester_fee.total_amount),
            'due_date': voucher.due_date.strftime('%d %B %Y'),
            'office_name': voucher.office.name if voucher.office else 'N/A',
            'office_address': voucher.office.location if voucher.office else 'N/A',
            'office_contact': voucher.office.contact_phone if voucher.office else 'N/A',
            'generated_at': generated_at,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Render voucher HTML for AJAX response
            voucher_html = render_to_string('fee_management/voucher.html', context)
            return JsonResponse({'voucher_html': voucher_html})
        
        return render(request, 'fee_management/generate_voucher.html', context)
    
    return render(request, 'fee_management/generate_voucher.html', {'errors': errors})