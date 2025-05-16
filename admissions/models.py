from django.db import models
from users.models import CustomUser
from academics.models import Program , Department , Faculty


# ===== 5. Academic Sessions & Semesters =====
class AcademicSession(models.Model):
    name = models.CharField(max_length=50)    # Fall 2024
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


# ===== 6. Admissions =====
class AdmissionCycle(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    application_start = models.DateField()
    application_end = models.DateField()
    is_open = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.program} - {self.session}"



class Applicant(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ])
    applied_at = models.DateTimeField(auto_now_add=True)
    # Applicant details
    applicant_photo = models.ImageField(upload_to='photos/', blank=True)
    full_name = models.CharField(max_length=100)
    religion = models.CharField(max_length=50)
    caste = models.CharField(max_length=50)
    cnic = models.CharField(max_length=15)
    dob = models.DateField()
    contact_no = models.CharField(max_length=15)
    identification_mark = models.TextField(blank=True)

    # Father/Guardian details
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100)
    father_cnic = models.CharField(max_length=15)
    monthly_income = models.PositiveIntegerField()
    relationship = models.CharField(max_length=50, choices=[
        ('father', 'Father'),
        ('guardian', 'Guardian')
    ])
    permanent_address = models.TextField()

    # Declaration
    declaration = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class AcademicQualification(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='academic_qualifications')
    exam_passed = models.CharField(max_length=100)
    passing_year = models.PositiveIntegerField()
    marks_obtained = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()
    division = models.CharField(max_length=50)
    subjects = models.TextField()
    institute = models.CharField(max_length=200)
    board = models.CharField(max_length=200)
    level = models.CharField(max_length=50, default='N/A')

    def __str__(self):
        return f"{self.applicant.full_name} - {self.level}"

class ExtraCurricularActivity(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='extra_curricular_activities')
    activity = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=100, blank=True)
    achievement = models.CharField(max_length=200, blank=True)
    activity_year = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.applicant.full_name} - {self.activity}"
