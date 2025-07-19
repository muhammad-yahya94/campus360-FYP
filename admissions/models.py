from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty




class AcademicSession(models.Model):
    """
    Represents an academic session spanning multiple years (e.g., 2021-2025).
    Each session contains multiple semesters and is associated with a specific batch of students.
    """
    name = models.CharField(
        max_length=50,
        help_text="Enter the name of the academic session (e.g., '2021-2025', 'Fall 2021-Spring 2025')"
    )
    start_year = models.IntegerField(
        help_text="Enter the starting year of this academic session (e.g., 2021)"
    )
    end_year = models.IntegerField(
        help_text="Enter the ending year of this academic session (e.g., 2025)"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Check this if this is the current academic session. Only one session can be active at a time."
    )
    description = models.TextField(
        blank=True,
        help_text="Optional: Add any additional information about this academic session"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Academic Session"
        verbose_name_plural = "Academic Sessions"
        ordering = ['-start_year']

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
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, null=True, blank=True, help_text="Select the academic session this applicant applied for.")
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
    gender = models.CharField(
        max_length=6,
        choices=[('male', 'Male'), ('female', 'Female')],
        help_text="Select the gender of the applicant.")

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

    # New Shift Field
    shift = models.CharField(max_length=10, choices=[
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ], help_text="Select the preferred shift for the program.")

    # Declaration
    declaration = models.BooleanField(default=False, help_text="Check this box to confirm that the applicant agrees to the terms and conditions.")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection if application is rejected.")
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
    board = models.CharField(max_length=200, blank=True, help_text="Enter the name of the examining board or university (optional).")
    certificate_file = models.FileField(upload_to='academic_certificates/%Y/%m/', blank=True, null=True, help_text="Upload the certificate or transcript for this qualification.")

    def __str__(self):
        return f"{self.applicant.full_name} - {self.exam_passed}"

class ExtraCurricularActivity(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='extra_curricular_activities', help_text="Select the applicant for this activity record.")
    activity = models.CharField(max_length=200, blank=True, help_text="Describe the extra-curricular activity (e.g., Debate Club, Football Team).")
    position = models.CharField(max_length=100, blank=True, help_text="Enter any position held in the activity (e.g., Captain, Secretary).")
    achievement = models.CharField(max_length=200, blank=True, help_text="Describe any achievements in the activity (e.g., Won 1st Prize).")
    activity_year = models.PositiveIntegerField(null=True, blank=True, help_text="Enter the year this activity took place.")
    certificate_file = models.FileField(upload_to='extra_curricular_certificates/%Y/%m/', blank=True, null=True, help_text="Upload certificate or proof of participation/achievement.")

    def __str__(self):
        return f"{self.applicant.full_name} - {self.activity}"
