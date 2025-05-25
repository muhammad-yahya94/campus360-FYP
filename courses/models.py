from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty, Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
import os
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
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='course_offerings', help_text="Select the academic session for this offering.")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='course_offerings', help_text="Select the semester for this offering.")
    is_active = models.BooleanField(default=True, help_text="Check if this course offering is currently active for enrollment.")
    max_capacity = models.PositiveIntegerField(default=30, help_text="Maximum number of students that can enroll in this offering.")
    current_enrollment = models.PositiveIntegerField(default=0, help_text="Current number of enrolled students.")
    
    OFFERING_TYPES = [
        ('core', 'Core / Compulsory'),
        ('major', 'Major'),
        ('minor', 'Minor'),
        ('elective', 'Elective'),
        ('foundation', 'Foundation'),
        ('gen_ed', 'General Education'),
        ('lab', 'Lab / Practical'),
        ('seminar', 'Seminar'),
        ('capstone', 'Capstone / Final Project'),
        ('internship', 'Internship / Training'),
        ('service', 'Service Course'),
        ('remedial', 'Remedial / Non-Credit'),
    ]

    offering_type = models.CharField(
        max_length=30,
        choices=OFFERING_TYPES,
        default='core',
        help_text="Specify how this course offering fits into a program."
    )

    def __str__(self):
        return f"{self.course.code} - {self.course.name} ({self.semester}, {self.academic_session})"

    class Meta:
        verbose_name = "Course Offering"
        verbose_name_plural = "Course Offerings"

