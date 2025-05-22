from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
import os
from django.core.exceptions import ValidationError
from django.utils import timezone


# ===== Course =====
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="Enter the unique course code (e.g., CS101).")  # e.g., CS101
    name = models.CharField(max_length=200, help_text="Enter the full name of the course (e.g., Introduction to Programming).")  # e.g., Introduction to Programming
    credits = models.PositiveIntegerField(help_text="Enter the number of credit hours for this course.")  # e.g., 3
    is_active = models.BooleanField(default=True, help_text="Check this if the course is currently active and can be offered.")
    description = models.TextField(blank=True, help_text="Provide a brief description or syllabus summary for the course.")
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='required_for', help_text="Select any courses that are required to be completed before taking this course (optional).")

    def __str__(self):
        return f"{self.code}: {self.name}"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

# ===== Course Offering =====
class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings', help_text="Select the core course being offered.")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_offerings', help_text="Select the teacher assigned to teach this course offering.")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='course_offerings', null=True, blank=True, help_text="Select the department offering this course (optional).")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='course_offerings', null=True, blank=True, help_text="Select the program this course offering belongs to (optional).")
    OFFERING_TYPES = [
        ('core', 'Core / Compulsory'),             # Required for all students in a program
        ('major', 'Major'),                        # Courses for a student's major field
        ('minor', 'Minor'),                        # Courses for a minor/secondary field
        ('elective', 'Elective'),                  # Optional courses chosen by the student
        ('foundation', 'Foundation'),              # Bridging or basic level courses
        ('gen_ed', 'General Education'),           # Broad courses in humanities, sciences, etc.
        ('lab', 'Lab / Practical'),                # Practical or laboratory-based courses
        ('seminar', 'Seminar'),                    # Small-group, discussion or presentation-based
        ('capstone', 'Capstone / Final Project'),  # Final year project or thesis
        ('internship', 'Internship / Training'),   # Practical industry training
        ('service', 'Service Course'),             # Courses offered by one department to others
        ('remedial', 'Remedial / Non-Credit'),     # For students needing academic support
    ]

    offering_type = models.CharField(
    max_length=30,
    choices=OFFERING_TYPES,
    default='core',
    help_text="Specify how this course offering fits into a program (e.g., Major, Elective, Foundation, etc.)."
)


    class Meta:
        unique_together = ('course', 'teacher', 'program', 'department', 'offering_type')
        verbose_name = "Course Offering"
        verbose_name_plural = "Course Offerings"

