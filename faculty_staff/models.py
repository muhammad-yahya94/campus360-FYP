from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from django.utils.text import slugify
from django.conf import settings # Import settings for User model

# ===== Teacher =====
class Teacher(models.Model):
    # Designation Choices
    DESIGNATION_CHOICES = [
        ('head_of_department', 'Head of Department'),
        ('professor', 'Professor'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile', help_text="Select the user account associated with this teacher.")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers', help_text="Select the department this teacher belongs to.")
    designation = models.CharField(max_length=100, choices=DESIGNATION_CHOICES, help_text="Select the official designation or role of the teacher within the department.")
    contact_no = models.CharField(max_length=15, help_text="Enter the primary contact phone number for the teacher.")
    qualification = models.TextField(help_text="Enter the highest academic qualification of the teacher (e.g., PhD in Computer Science).")  # e.g., PhD in Computer Science
    hire_date = models.DateField(help_text="Select the date when the teacher was hired.")
    is_active = models.BooleanField(default=True, help_text="Check this if the teacher's profile is currently active.")
    # New fields for social media and experience
    linkedin_url = models.URLField(max_length=200, blank=True, null=True, help_text="Enter the LinkedIn profile URL for the teacher (optional).")
    twitter_url = models.URLField(max_length=200, blank=True, null=True, help_text="Enter the Twitter profile URL for the teacher (optional).")
    personal_website = models.URLField(max_length=200, blank=True, null=True, help_text="Enter the personal website URL for the teacher (optional).")
    experience = models.TextField(blank=True, null=True, help_text="Provide a summary of the teacher's professional experience.")

    def __str__(self):
        return f"{self.user.first_name} ({self.designation})"

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

class TeacherDetails(models.Model):
    # Employment Type Choices
    EMPLOYMENT_TYPE_CHOICES = [
        ('visitor', 'Visitor'),
        ('contract', 'Contract Based'),
        ('permanent', 'Permanent'),
    ]

    # Status Choices
    STATUS_CHOICES = [
        ('on_break', 'On Break'),
        ('on_lecture', 'On Lecture'),
        ('on_leave', 'On Leave'),
        ('available', 'Available'),
    ]

    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, related_name='details', help_text="Select the teacher to associate these details with.")
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True, null=True, help_text="Select the employment type of the teacher (optional).")
    salary_per_lecture = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Enter the teacher's salary per lecture (optional).")
    fixed_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Enter the teacher's fix salary (optional).")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True, help_text="Select the current status of the teacher (optional).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Automatically updated with the last modification date.")

    def __str__(self):
        return f"{self.teacher.user.first_name}'s Details ({self.employment_type or 'N/A'})"

    class Meta:
        verbose_name = "Teacher Details"
        verbose_name_plural = "Teacher Details"

# ===== Office =====
class Office(models.Model):
    name = models.CharField(max_length=100, help_text="Enter the name of the administrative office (e.g., Registrar Office).")
    description = models.TextField(blank=True, null=True, help_text="Provide a brief description of the office and its functions.")
    image = models.ImageField(upload_to='offices/', blank=True, null=True, help_text="Upload an image representing the office.")
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Enter the physical location or building of the office.")
    contact_email = models.EmailField(blank=True, null=True, help_text="Enter the official email address for the office.")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Enter the official phone number for the office.")
    slug = models.SlugField(unique=True, max_length=100, help_text="A unique identifier for the office page URL. Automatically generated if left blank.")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Office"
        verbose_name_plural = "Offices"


# ===== Office Staff =====
class OfficeStaff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='officestaff_profile', help_text="Select the user account associated with this staff member.")
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='staff', help_text="Select the office this staff member belongs to.")
    position = models.CharField(max_length=100, help_text="Enter the position or role of the staff member within the office.")
    contact_no = models.CharField(max_length=15, blank=True, null=True, help_text="Enter the contact phone number for the office staff member (optional).")

    def __str__(self):
        return f"{(self.user.get_full_name() or self.user.first_name)} ({self.position})"



    class Meta:
        verbose_name = "Office Staff"
        verbose_name_plural = "Office Staff"

