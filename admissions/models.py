from django.db import models
from users.models import CustomUser
from academics.models import Program , Department , Faculty


# ===== 5. Academic Sessions & Semesters =====
class AcademicSession(models.Model):
    name = models.CharField(max_length=50, help_text="Enter the name of the academic session (e.g., Fall 2024, Spring 2025).")    # Fall 2024
    start_date = models.DateField(help_text="Select the starting date of this academic session.")
    end_date = models.DateField(help_text="Select the ending date of this academic session.")
    is_active = models.BooleanField(default=False, help_text="Check this if this is the current academic session.")
    
    def __str__(self):
        return self.name


# ===== 6. Admissions =====
class AdmissionCycle(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, help_text="Select the academic program for this admission cycle.")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, help_text="Select the academic session this admission cycle belongs to.")
    application_start = models.DateField(help_text="Select the date when applications open for this cycle.")
    application_end = models.DateField(help_text="Select the deadline for submitting applications in this cycle.")
    is_open = models.BooleanField(default=False, help_text="Check this if the application submission is currently open for this cycle.")
    
    def __str__(self):
        return f"{self.program} - {self.session}"



class Applicant(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications', help_text="Select the user account associated with this applicant.")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, help_text="Select the faculty the applicant is applying to.")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, help_text="Select the department the applicant is applying to.")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, help_text="Select the specific program the applicant is applying for.")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], help_text="Select the current status of the applicant's application.")
    applied_at = models.DateTimeField(auto_now_add=True, help_text="The date and time the application was submitted.")
    # Applicant details
    applicant_photo = models.ImageField(upload_to='photos/', blank=True, help_text="Upload a recent passport-sized photograph of the applicant.")
    full_name = models.CharField(max_length=100, help_text="Enter the applicant's full name.")
    religion = models.CharField(max_length=50, help_text="Enter the applicant's religion.")
    caste = models.CharField(max_length=50, blank=True, help_text="Enter the applicant's caste (optional).")
    cnic = models.CharField(max_length=15, help_text="Enter the applicant's CNIC or B-form number.")
    dob = models.DateField(help_text="Select the applicant's date of birth.")
    contact_no = models.CharField(max_length=15, help_text="Enter the applicant's primary contact phone number.")
    identification_mark = models.TextField(blank=True, help_text="Describe any visible identification mark on the applicant's body (optional).")

    # Father/Guardian details
    father_name = models.CharField(max_length=100, help_text="Enter the full name of the applicant's father or guardian.")
    father_occupation = models.CharField(max_length=100, help_text="Enter the occupation of the applicant's father or guardian.")
    father_cnic = models.CharField(max_length=15, blank=True, help_text="Enter the CNIC of the applicant's father or guardian (optional).")
    monthly_income = models.PositiveIntegerField(blank=True, null=True, help_text="Enter the approximate monthly income of the father or guardian.")
    relationship = models.CharField(max_length=50, choices=[
        ('father', 'Father'),
        ('guardian', 'Guardian')
    ], help_text="Select the relationship of the listed person to the applicant.")
    permanent_address = models.TextField(help_text="Enter the applicant's permanent home address.")

    # Declaration
    declaration = models.BooleanField(default=False, help_text="Check this box to confirm that the applicant agrees to the terms and conditions.")

    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time this applicant record was created.")

    def __str__(self):
        return self.full_name

class AcademicQualification(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='academic_qualifications', help_text="Select the applicant for this academic qualification.")
    exam_passed = models.CharField(max_length=100, help_text="Enter the name of the exam passed (e.g., Matriculation, FSc, Bachelor's).")
    passing_year = models.PositiveIntegerField(help_text="Enter the year the exam was passed.")
    marks_obtained = models.PositiveIntegerField(blank=True, null=True, help_text="Enter the marks obtained in the exam.")
    total_marks = models.PositiveIntegerField(blank=True, null=True, help_text="Enter the total possible marks for the exam.")
    division = models.CharField(max_length=50, blank=True, help_text="Enter the division or grade obtained (e.g., 1st Division, A+).")
    subjects = models.TextField(blank=True, help_text="List the subjects studied in this qualification.")
    institute = models.CharField(max_length=200, help_text="Enter the name of the school, college, or university attended.")
    board = models.CharField(max_length=200, blank=True, help_text="Enter the name of the examining board or university (optional).")
    level = models.CharField(max_length=50, default='N/A', help_text="Enter the academic level of this qualification (e.g., Matric, Intermediate, Bachelor). Optional, defaults to N/A.")

    def __str__(self):
        return f"{self.applicant.full_name} - {self.level}"

class ExtraCurricularActivity(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='extra_curricular_activities', help_text="Select the applicant for this activity record.")
    activity = models.CharField(max_length=200, blank=True, help_text="Describe the extra-curricular activity (e.g., Debate Club, Football Team).")
    position = models.CharField(max_length=100, blank=True, help_text="Enter any position held in the activity (e.g., Captain, Secretary).")
    achievement = models.CharField(max_length=200, blank=True, help_text="Describe any achievements in the activity (e.g., Won 1st Prize).")
    activity_year = models.PositiveIntegerField(null=True, blank=True, help_text="Enter the year this activity took place.")

    def __str__(self):
        return f"{self.applicant.full_name} - {self.activity}"
