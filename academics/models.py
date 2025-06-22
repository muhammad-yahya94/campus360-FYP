from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

# ===== 1. Faculty =====
class Faculty(models.Model):
    name = models.CharField(max_length=100, help_text="Enter the full name of the academic faculty (e.g., Faculty of Engineering).")  # e.g., Engineering, Languages
    slug = models.SlugField(unique=True, max_length=100, help_text="A unique, web-friendly identifier for the faculty (e.g., faculty-of-engineering). Automatically generated if left blank.")
    description = models.TextField(blank=True, help_text="Provide a brief description of the faculty.")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Faculty"
        verbose_name_plural = "Faculties"


# ===== 2. Department =====
class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments', help_text="Select the faculty that this department belongs to.")
    name = models.CharField(max_length=100, help_text="Enter the full name of the department (e.g., Department of Computer Science).")  # e.g., Computer Science
    slug = models.SlugField(unique=True, max_length=100, help_text="A unique, web-friendly identifier for the department (e.g., computer-science). Automatically generated if left blank.")
    code = models.CharField(max_length=10, help_text="Enter the short code or abbreviation for the department (e.g., CS).")   # e.g., CS
    image = models.ImageField(upload_to='departments/', blank=True, null=True, help_text="Upload an image to represent the department.")
    introduction = models.TextField(blank=True, null=True, help_text="Provide a brief introductory text for the department page.")
    details = models.TextField(blank=True, null=True, help_text="Provide detailed information about the department, its facilities, etc.")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"


# ===== 3. Program =====
class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs', help_text="Select the department that offers this academic program.")
    name = models.CharField(max_length=100, help_text="Enter the full name of the academic program (e.g., Bachelor of Science in Computer Science).")
    degree_type = models.CharField(max_length=10, help_text='e.g., PhD, MPhil, BS. Enter the type of degree awarded by this program.')
    duration_years = models.IntegerField(help_text="Enter the number of years it typically takes to complete the program.")
    total_semesters = models.PositiveIntegerField(default=8, help_text="Enter the total number of semesters in the program.")
    start_year = models.PositiveIntegerField(help_text="Enter the year when this program started")
    end_year = models.PositiveIntegerField(null=True, blank=True, help_text="Enter the year when this program ended (leave blank if still active)")
    is_active = models.BooleanField(default=True, help_text="Check this if this program is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"




# ===== Semester Model =====
class Semester(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters', help_text="Select the program this semester belongs to.")
    session = models.ForeignKey('admissions.AcademicSession', on_delete=models.CASCADE, related_name='semesters', help_text="Select the academic session this semester belongs to.")
    number = models.PositiveIntegerField(help_text="Semester number in the program sequence")
    name = models.CharField(max_length=100, help_text="Name of the semester (e.g., 'Semester 1', 'Semester 2')")
    description = models.TextField(blank=True, help_text="Description of what this semester covers")
    start_time = models.DateField(null=True, blank=True, help_text="Start date of the semester")
    end_time = models.DateField(null=True, blank=True, help_text="End date of the semester")
    is_active = models.BooleanField(default=True, help_text="Whether this semester is currently active")
    
    class Meta:
        unique_together = ('program', 'number', 'session')  # Ensure uniqueness across program, number, and session
        ordering = ['program', 'number']
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def __str__(self):
        return f"{self.program.name} - Semester {self.number} ({self.session.name})"

    def save(self, *args, **kwargs):
        # Ensure semester numbers are sequential within the session and program
        if self.number > 1:
            prev_semester = Semester.objects.filter(
                program=self.program,
                session=self.session,
                number=self.number - 1
            ).first()
            if not prev_semester:
                raise ValidationError(f"Semester {self.number-1} must exist before semester {self.number} for session {self.session.name}")
        super().save(*args, **kwargs)