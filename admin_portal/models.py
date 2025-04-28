from django.db import models
from users.models import CustomUser
from django_ckeditor_5.fields import CKEditor5Field
# ===== 1. Degree Types (Separate Table) =====
class DegreeType(models.Model):
    code = models.CharField(max_length=10, unique=True)  # BS, MS, PhD
    name = models.CharField(max_length=100)              # Bachelor of Science
    
    def __str__(self):
        return f"{self.code} - {self.name}"

# ===== 2. Faculty =====
class Faculty(models.Model):
    name = models.CharField(max_length=100)  # Engineering, Languages
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

# ===== 3. Department =====
class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # Computer Science
    code = models.CharField(max_length=10)   # CS
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# ===== 4. Program =====
class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)       # BS Computer Science
    degree_type = models.ForeignKey(DegreeType, on_delete=models.PROTECT)
    duration_years = models.IntegerField()        # 4
    
    def __str__(self):
        return self.name

# ===== 5. Academic Sessions & Semesters =====
class AcademicSession(models.Model):
    name = models.CharField(max_length=50)    # Fall 2024
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Semester(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)    # Semester 1
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"{self.session} - {self.name}"

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
    CustomUser = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    admission_cycle = models.ForeignKey(AdmissionCycle, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ])
    applied_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.CustomUser.username} - {self.program}"

# ===== 7. Courses & Enrollment =====
class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)    # CS101
    title = models.CharField(max_length=100)  # Introduction to Programming
    credits = models.IntegerField()           # 3
    
    def __str__(self):
        return f"{self.code}: {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, blank=True, null=True)  # A, B, C
    
    def __str__(self):
        return f"{self.student} - {self.course}"
    
    
    


class Slider(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='slider/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Alumni(models.Model):
    name = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField()
    profession = models.CharField(max_length=200)
    testimonial = models.TextField()
    image = models.ImageField(upload_to='alumni/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Gallery(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='gallery/')
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class News(models.Model):
    title = models.CharField(max_length=200)
    content = CKEditor5Field('Text', config_name='default')
    published_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = CKEditor5Field('Text', config_name='default') 
    event_date = models.DateTimeField(
        help_text="Select date YYYY-MM-DD (e.g., 2023-12-31) and time HH:MM (e.g., 14:30)"
    )
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    
    def __str__(self):
        return self.title