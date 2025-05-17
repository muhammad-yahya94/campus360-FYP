from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
import os
from django.core.exceptions import ValidationError
from django.utils import timezone

# ===== Semester =====
class Semester(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50)  # e.g., Semester 1, Fall 2024 - Semester 1
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.program.name} - {self.name}"

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.filter(program=self.program, is_current=True).exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

# ===== Course =====
class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=10, unique=True)  # e.g., CS101
    name = models.CharField(max_length=200)  # e.g., Introduction to Programming
    credits = models.PositiveIntegerField()  # e.g., 3
    COURSE_TYPES = [
        ('core', 'Core'),
        ('elective', 'Elective'),
        ('lab', 'Laboratory'),
        ('seminar', 'Seminar'),
    ]
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='core')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='required_for')

    def __str__(self):
        return f"{self.code}: {self.name}"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

# ===== Course Offering =====
class CourseOffering(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='course_offerings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_offerings')


    class Meta:
        unique_together = ('semester', 'course', 'teacher')
        verbose_name = "Course Offering"
        verbose_name_plural = "Course Offerings"


# ===== Course Offering Teacher Change =====
class CourseOfferingTeacherChange(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='teacher_changes')
    old_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='old_course_offerings')
    new_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='new_course_offerings')
    change_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Change for {self.course_offering}: {self.old_teacher} to {self.new_teacher} on {self.change_date}"

    class Meta:
        verbose_name = "Course Offering Teacher Change"
        verbose_name_plural = "Course Offering Teacher Changes"

# ===== Assignment =====
class Assignment(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)  # e.g., "Programming Assignment 1"
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)  # e.g., 100 points
    ASSIGNMENT_TYPES = [
        ('homework', 'Homework'),
        ('project', 'Project'),
        ('quiz', 'Quiz'),
        ('lab', 'Lab'),
        ('essay', 'Essay'),
    ]
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='homework')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

    class Meta:
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def clean(self):
        if self.due_date < timezone.now():
            raise ValidationError("Due date cannot be in the past.")
        if self.course_offering.semester.end_date < self.due_date.date():
            raise ValidationError("Due date cannot be after the semester end date.")

# ===== Submission =====
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='submissions/%Y/%m/%d/', blank=True, null=True)
    text = models.TextField(blank=True)  # For text-based submissions
    grade = models.PositiveIntegerField(blank=True, null=True)  # e.g., 85 out of 100
    feedback = models.TextField(blank=True)  # Teacher's feedback

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    class Meta:
        unique_together = ('assignment', 'student')  # One submission per student per assignment
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

    def clean(self):
        # Ensure student is enrolled in the course (assuming CustomUser has a role or enrollment logic)
        if not self.student.is_student:  # Assuming CustomUser has an is_student field or similar
            raise ValidationError("Only students can submit assignments.")
        if self.submitted_at > self.assignment.due_date:
            raise ValidationError("Submission is past the due date.")
        if self.grade is not None and self.grade > self.assignment.max_points:
            raise ValidationError(f"Grade cannot exceed {self.assignment.max_points} points.")