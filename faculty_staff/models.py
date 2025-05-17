from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from django.utils.text import slugify

# Teacher Designation Choices
DESIGNATION_CHOICES = [
    ('head_of_department', 'Head of Department'),
    ('professor', 'Professor'),
    ('associate_professor', 'Associate Professor'),
    ('assistant_professor', 'Assistant Professor'),
    ('lecturer', 'Lecturer'),
    ('visiting', 'Visiting Faculty'),
]

# ===== Teacher =====
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    designation = models.CharField(max_length=100, choices=DESIGNATION_CHOICES)
    contact_no = models.CharField(max_length=15)
    qualification = models.TextField()  # e.g., PhD in Computer Science
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} ({self.designation})"

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"


# ===== Office =====
class Office(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='offices/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=100, help_text="A unique identifier for the office page URL.")

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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='officestaff_profile')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='staff')
    position = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):  
        return f"{(self.user.get_full_name() or self.user.first_name)} ({self.position})"



    class Meta:
        verbose_name = "Office Staff"
        verbose_name_plural = "Office Staff"

