from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty, Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from django.core.exceptions import ValidationError
import os
from django.utils import timezone


# ===== Course =====
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="Enter the unique course code (e.g., CS101).")  # e.g., CS101
    name = models.CharField(max_length=200, help_text="Enter the full name of the course (e.g., Introduction to Programming).")  # e.g., Introduction to Programming
    credits = models.PositiveIntegerField(help_text="Enter the number of credit hours for this course.")  # e.g., 3
    lab_work = models.IntegerField(default=0, help_text="Enter the number of lab hours per week for this course (if applicable).")  # e.g., 2
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






class Venue(models.Model):
    name = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class TimetableSlot(models.Model):
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    course_offering = models.ForeignKey('CourseOffering', on_delete=models.CASCADE, related_name='timetable_slots')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.ForeignKey('Venue', on_delete=models.PROTECT)

    class Meta:
        unique_together = ['course_offering', 'day', 'start_time', 'venue']

    def clean(self):
        # Basic validation
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

        # Check for scheduling conflicts
        overlapping_slots = TimetableSlot.objects.filter(
            course_offering__academic_session=self.course_offering.academic_session,
            day=self.day,
            venue=self.venue,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)

        if overlapping_slots.exists():
            raise ValidationError(f"Venue {self.venue.name} is already booked on {self.get_day_display()} from {self.start_time} to {self.end_time}.")

        # Check for teacher conflicts
        teacher_slots = TimetableSlot.objects.filter(
            course_offering__teacher=self.course_offering.teacher,
            course_offering__academic_session=self.course_offering.academic_session,
            day=self.day,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)

        if teacher_slots.exists():
            raise ValidationError(f"Teacher {self.course_offering.teacher} is already scheduled on {self.get_day_display()} from {self.start_time} to {self.end_time}.")

    def __str__(self):
        return f"{self.course_offering.course.code} - {self.get_day_display()} {self.start_time} to {self.end_time} at {self.venue.name}"



# ===== Study Material =====
class StudyMaterial(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='study_materials')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='study_materials')
    topic = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField()
    useful_links = models.TextField(blank=True, help_text="Enter URLs separated by newlines")
    video_link = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='study_materials/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

# ===== Assignment =====
class Assignment(models.Model):
    course_offering = models.ForeignKey('CourseOffering', on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField(null=True, blank=True)
    max_points = models.PositiveIntegerField()
    resource_file = models.FileField(upload_to='assignments/resources/', max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

    class Meta:
        verbose_name_plural = 'assignments'





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
        return f"{self.title} by {self.created_by.user.get_full_name()}"

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
    remarks = models.TextField(blank=True,null=True, help_text="Additional remarks or comments on the student's performance.")

    def __str__(self):
        return f"{self.student} - {self.exam_type} ({self.course_offering})"

    class Meta:
        unique_together = ('course_offering', 'student', 'exam_type')
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"
        
        
        


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    )
    SHIFT_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='attendances')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, null=True, blank=True)  # For 'both' shift courses
    recorded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='recorded_attendances')
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'course_offering', 'date', 'shift')
        ordering = ['date', 'student']

    def __str__(self):
        return f"{self.student.applicant.full_name} - {self.course_offering.course.code} - {self.date} - {self.status} - {self.shift or 'N/A'}"        