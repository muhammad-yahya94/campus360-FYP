from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession

# ===== Teacher =====
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    designation = models.CharField(max_length=100, choices=[
        ('head_of_department', 'Head of Department'),
        ('professor', 'Professor'),
        ('associate_professor', 'Associate Professor'),
        ('assistant_professor', 'Assistant Professor'),
        ('lecturer', 'Lecturer'),
        ('visiting', 'Visiting Faculty'),
    ])
    contact_no = models.CharField(max_length=15)
    qualification = models.TextField()  # e.g., PhD in Computer Science
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} ({self.designation})"

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

