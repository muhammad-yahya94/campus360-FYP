from django.db import models


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
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
