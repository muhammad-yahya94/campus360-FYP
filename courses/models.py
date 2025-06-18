from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty, Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
# from students.models import Student
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
    current_enrollment = models.IntegerField()
    shift = models.CharField(
        max_length=10,
        choices=[
            ('morning', 'Morning'),
            ('evening', 'Evening'),
            ('both', 'Both')
        ],
        default='morning',
        help_text="Select the shift for this course offering."
    )
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
        return f"{self.course.code}  {self.course.name} - {self.semester.name} ({self.academic_session.name})"


    class Meta:
        verbose_name = "Course Offering"
        verbose_name_plural = "Course Offerings"








# ===== Study Material =====
class StudyMaterial(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='study_materials', help_text="The course offering this study material belongs to.")
    title = models.CharField(max_length=200, help_text="Title of the study material (e.g., 'Lecture 1 Notes').")
    description = models.TextField(blank=True, help_text="Brief description of the study material.")
    file = models.FileField(upload_to='study_materials/', help_text="Upload the study material file (e.g., PDF, PPT).")
    uploaded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='uploaded_materials', help_text="The teacher who uploaded this material.")
    uploaded_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the material was uploaded.")
    is_active = models.BooleanField(default=True, help_text="Check if this study material is currently accessible to students.")

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

    class Meta:
        verbose_name = "Study Material"
        verbose_name_plural = "Study Materials"

# ===== Assignment =====
class Assignment(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='assignments', help_text="The course offering this assignment belongs to.")
    title = models.CharField(max_length=200, help_text="Title of the assignment (e.g., 'Assignment 1: Python Basics').")
    description = models.TextField(blank=True, help_text="Detailed description or instructions for the assignment.")
    file = models.FileField(upload_to='assignments/', null=True, blank=True, help_text="Upload the assignment file (e.g., PDF with questions).")
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_assignments', help_text="The teacher who created this assignment.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the assignment was created.")
    due_date = models.DateTimeField(help_text="The deadline for submitting the assignment.")
    total_marks = models.PositiveIntegerField(default=100, help_text="Total marks for the assignment.")
    is_active = models.BooleanField(default=True, help_text="Check if this assignment is currently active and visible to students.")

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

    class Meta:
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"





# ===== Assignment Submission =====
class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', help_text="The assignment this submission is for.")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='submissions', help_text="The student who submitted this assignment.")
    file = models.FileField(upload_to='submissions/', help_text="The file submitted by the student.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the submission was made.")
    marks_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained by the student for this submission.")
    feedback = models.TextField(blank=True, help_text="Feedback from the teacher on this submission.")
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='graded_submissions', help_text="The teacher who graded this submission.")
    graded_at = models.DateTimeField(null=True, blank=True, help_text="The date and time when the submission was graded.")

    def __str__(self):
        return f"Submission by {self.student} for {self.assignment}"

    class Meta:
        unique_together = ('assignment', 'student')
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"

# ===== Notice Board =====
class Notice(models.Model):
    title = models.CharField(max_length=200, help_text="Title of the notice (e.g., 'Exam Schedule Update').")
    content = models.TextField(help_text="The content of the notice.")
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_notices', help_text="The teacher who created this notice.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the notice was created.")
    is_active = models.BooleanField(default=True, help_text="Check if this notice is currently visible to students.")

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

    class Meta:
        verbose_name = "Notice"
        verbose_name_plural = "Notices"

# ===== Marks After Exams =====
class ExamResult(models.Model):
    EXAM_TYPES = [
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('sessional', 'Sessoinal'),
        ('project', 'Project'),
        ('practical', 'Practical Exam'),
    ]

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='exam_results', help_text="The course offering this exam result is for.")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_results', help_text="The student this result pertains to.")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, help_text="The type of exam (e.g., Midterm, Final).")
    total_marks = models.PositiveIntegerField(default=100, help_text="Total marks for this exam.")
    marks_obtained = models.PositiveIntegerField(help_text="Marks obtained by the student in this exam.")
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='graded_results', help_text="The teacher who graded this exam.")
    graded_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the result was recorded.")
    remarks = models.TextField(blank=True, help_text="Additional remarks or comments on the student's performance.")

    def __str__(self):
        return f"{self.student} - {self.exam_type} ({self.course_offering})"

    class Meta:
        unique_together = ('course_offering', 'student', 'exam_type')
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"