from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Applicant, AcademicQualification, ExtraCurricularActivity
from academics.models import Program, Department, Faculty

# Create your views here.

@login_required
def apply(request):
    if request.method == 'POST':
        try:
            # Create Applicant
            applicant = Applicant.objects.create(
                user=request.user,
                faculty_id=request.POST.get('faculty'),
                department_id=request.POST.get('department'),
                program_id=request.POST.get('program'),
                status='pending',
                full_name=request.POST.get('full_name'),
                religion=request.POST.get('religion'),
                caste=request.POST.get('caste'),
                cnic=request.POST.get('cnic'),
                dob=request.POST.get('dob'),
                contact_no=request.POST.get('contact_no'),
                identification_mark=request.POST.get('identification_mark'),
                father_name=request.POST.get('father_name'),
                father_occupation=request.POST.get('father_occupation'),
                father_cnic=request.POST.get('father_cnic'),
                monthly_income=request.POST.get('monthly_income'),
                relationship=request.POST.get('relationship'),
                permanent_address=request.POST.get('permanent_address'),
                declaration=request.POST.get('declaration') == 'on'
            )

            # Handle applicant photo
            if 'applicant_photo' in request.FILES:
                applicant.applicant_photo = request.FILES['applicant_photo']
                applicant.save()

            # Handle Academic Qualifications
            exam_passed = request.POST.getlist('exam_passed[]')
            passing_year = request.POST.getlist('passing_year[]')
            marks_obtained = request.POST.getlist('marks_obtained[]')
            total_marks = request.POST.getlist('total_marks[]')
            division = request.POST.getlist('division[]')
            subjects = request.POST.getlist('subjects[]')
            board = request.POST.getlist('board[]')
            certificate_files = request.FILES.getlist('certificate_file[]')

            for i in range(len(exam_passed)):
                if exam_passed[i]:  # Only create if exam_passed is not empty
                    qualification = AcademicQualification.objects.create(
                        applicant=applicant,
                        exam_passed=exam_passed[i],
                        passing_year=passing_year[i],
                        marks_obtained=marks_obtained[i] if marks_obtained[i] else None,
                        total_marks=total_marks[i] if total_marks[i] else None,
                        division=division[i],
                        subjects=subjects[i],
                        board=board[i]
                    )
                    # Handle certificate file if provided
                    if i < len(certificate_files) and certificate_files[i]:
                        qualification.certificate_file = certificate_files[i]
                        qualification.save()

            # Handle Extra Curricular Activities
            activities = request.POST.getlist('activity[]')
            positions = request.POST.getlist('position[]')
            achievements = request.POST.getlist('achievement[]')
            activity_years = request.POST.getlist('activity_year[]')
            activity_certificates = request.FILES.getlist('certificate_file[]')

            for i in range(len(activities)):
                if activities[i]:  # Only create if activity is not empty
                    activity = ExtraCurricularActivity.objects.create(
                        applicant=applicant,
                        activity=activities[i],
                        position=positions[i],
                        achievement=achievements[i],
                        activity_year=activity_years[i] if activity_years[i] else None
                    )
                    # Handle certificate file if provided
                    if i < len(activity_certificates) and activity_certificates[i]:
                        activity.certificate_file = activity_certificates[i]
                        activity.save()

            messages.success(request, 'Application submitted successfully!')
            return redirect('application_success')

        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
            return redirect('apply')

    # GET request - show the form
    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()

    context = {
        'faculties': faculties,
        'departments': departments,
        'programs': programs,
    }
    return render(request, 'admissions/apply.html', context)
