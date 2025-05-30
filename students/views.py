from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from academics.models import Department, Program, Semester
from admissions.models import AcademicSession
from courses.models import Course, CourseOffering, ExamResult, StudyMaterial, Assignment, AssignmentSubmission, Notice
from students.models import Student, StudentSemesterEnrollment, CourseEnrollment
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def student_login(request):
    if request.user.is_authenticated:
        return redirect('students:dashboard')

    if request.method == 'POST':
        email = request.POST.get('username')  # Email field is used as username
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            try:
                student = Student.objects.get(user=user)
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('students:dashboard')
            except Student.DoesNotExist:
                messages.error(request, 'You are not authorized as a student.')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')

@login_required
def student_dashboard(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        course_offering__academic_session=current_session
    ).select_related('course_offering__course', 'course_offering__semester')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'student': student,
        'enrollments': enrollments,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
    }
    return render(request, 'dashboard.html', context)

@login_required
def my_courses(request):
    try:
        user = request.user
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        course_offering__academic_session=current_session
    ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'enrollments': enrollments,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
    }
    return render(request, 'my_courses.html', context)

@login_required
def session_courses(request, session_id):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    session = get_object_or_404(AcademicSession, id=session_id)
    enrollments = CourseEnrollment.objects.filter(
        student_semester_enrollment__student=student,
        course_offering__academic_session=session
    ).select_related('course_offering__course', 'course_offering__semester', 'course_offering__teacher__user')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'enrollments': enrollments,
        'session': session,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'session_courses.html', context)

@login_required
def assignments(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__course_offering__academic_session=current_session
    ).select_related('assignment__course_offering__course')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'submissions': submissions,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
    }
    return render(request, 'assignments.html', context)

@login_required
def study_materials(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    current_session = AcademicSession.objects.filter(is_active=True).first()
    materials = StudyMaterial.objects.filter(
        course_offering__courseenrollment__student_semester_enrollment__student=student,
        course_offering__academic_session=current_session
    ).order_by('-uploaded_at')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'materials': materials,
        'academic_sessions': academic_sessions,
        'current_session': current_session,
    }
    return render(request, 'study_materials.html', context)

@login_required
def notices(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    notices = Notice.objects.filter(
        course_offering__courseenrollment__student_semester_enrollment__student=student
    ).order_by('-created_at')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'notices': notices,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'notices.html', context)

@login_required
def exam_results(request):
    user = request.user
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        messages.error(request, 'You are not authorized as a student.')
        return redirect('students:login')

    results = ExamResult.objects.filter(
        student=student
    ).select_related('course_offering__course', 'course_offering__academic_session')
    academic_sessions = AcademicSession.objects.all().order_by('-start_year')

    context = {
        'results': results,
        'academic_sessions': academic_sessions,
    }
    return render(request, 'exam_results.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('students:login')