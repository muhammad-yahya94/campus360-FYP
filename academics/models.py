from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


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




class Semester(models.Model):
    """
    Represents a semester within an academic session.
    Each semester has a specific number (1-8 for BS programs) and type (Fall/Spring).
    """
    SEMESTER_TYPES = [
        ('fall', 'Fall'),
        ('spring', 'Spring'),
    ]

    academic_session = models.ForeignKey(
        'admissions.AcademicSession',
        on_delete=models.CASCADE,
        related_name='semesters',
        help_text="Select the academic session this semester belongs to"
    )
    semester_number = models.PositiveIntegerField(
        help_text="Enter the semester number (1-8)"
    )
    semester_type = models.CharField(
        max_length=10,
        choices=SEMESTER_TYPES,
        help_text="Select whether this is a Fall or Spring semester"
    )
    start_date = models.DateField(
        help_text="Select the starting date of this semester"
    )
    end_date = models.DateField(
        help_text="Select the ending date of this semester"
    )
    registration_start = models.DateField(
        help_text="Select the start date for course registration"
    )
    registration_end = models.DateField(
        help_text="Select the end date for course registration"
    )
    classes_start = models.DateField(
        help_text="Select the date when classes begin"
    )
    mid_term_start = models.DateField(
        help_text="Select the start date of mid-term examinations"
    )
    mid_term_end = models.DateField(
        help_text="Select the end date of mid-term examinations"
    )
    final_term_start = models.DateField(
        help_text="Select the start date of final examinations"
    )
    final_term_end = models.DateField(
        help_text="Select the end date of final examinations"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Check this if this is the current semester. Only one semester can be active at a time."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"
        unique_together = ['academic_session', 'semester_number']
        ordering = ['academic_session', 'semester_number']

    def __str__(self):
        return f"{self.academic_session.name} - {self.get_semester_type_display()} Semester {self.semester_number}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other semesters
            Semester.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def is_registration_open(self):
        """Check if course registration is currently open for this semester"""
        today = timezone.now().date()
        return self.registration_start <= today <= self.registration_end

    def is_classes_running(self):
        """Check if classes are currently running for this semester"""
        today = timezone.now().date()
        return self.classes_start <= today <= self.end_date

    def is_mid_term_period(self):
        """Check if it's currently mid-term examination period"""
        today = timezone.now().date()
        return self.mid_term_start <= today <= self.mid_term_end

    def is_final_term_period(self):
        """Check if it's currently final examination period"""
        today = timezone.now().date()
        return self.final_term_start <= today <= self.final_term_end


class GradingSystem(models.Model):
    """
    Defines the grading system used for evaluating student performance.
    Each grade has a specific range of marks and corresponding grade points.
    """
    grade = models.CharField(
        max_length=2,
        unique=True,
        help_text="Enter the grade symbol (e.g., 'A+', 'A', 'B+', 'B', etc.)"
    )
    min_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Enter the minimum marks required for this grade (e.g., 85.00 for A)"
    )
    max_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Enter the maximum marks possible for this grade (e.g., 100.00 for A+)"
    )
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Enter the grade points for this grade (e.g., 4.0 for A+)"
    )
    description = models.CharField(
        max_length=50,
        help_text="Enter a description of this grade (e.g., 'Excellent', 'Very Good', etc.)"
    )
    is_passing = models.BooleanField(
        default=True,
        help_text="Check this if this grade is considered passing"
    )

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grading System"
        ordering = ['-grade_points']

    def __str__(self):
        return f"{self.grade} ({self.description})"


class StudentGrade(models.Model):
    """
    Records the grades achieved by students in their courses.
    Includes marks for different components and calculates the final grade.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="Select the student whose grade is being recorded"
    )
    course_offering = models.ForeignKey(
        'courses.CourseOffering',
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="Select the course offering for which the grade is being recorded"
    )
    mid_term_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Enter the marks obtained in mid-term examination"
    )
    final_term_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Enter the marks obtained in final examination"
    )
    assignment_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Enter the total marks obtained in assignments"
    )
    quiz_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Enter the total marks obtained in quizzes"
    )
    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Total marks obtained in the course (automatically calculated)"
    )
    grade = models.ForeignKey(
        GradingSystem,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Final grade awarded (automatically calculated based on total marks)"
    )
    remarks = models.TextField(
        blank=True,
        help_text="Any additional remarks or comments about the grade"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Grade"
        verbose_name_plural = "Student Grades"
        unique_together = ['student', 'course_offering']

    def __str__(self):
        return f"{self.student} - {self.course_offering} - {self.grade}"

    def save(self, *args, **kwargs):
        # Calculate total marks
        self.total_marks = sum(
            mark for mark in [
                self.mid_term_marks,
                self.final_term_marks,
                self.assignment_marks,
                self.quiz_marks
            ] if mark is not None
        )
        
        # Determine grade based on total marks
        self.grade = GradingSystem.objects.filter(
            min_marks__lte=self.total_marks,
            max_marks__gte=self.total_marks
        ).first()
        
        super().save(*args, **kwargs)


class Attendance(models.Model):
    """
    Records student attendance for each course.
    Tracks presence, absence, and late arrivals.
    """
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Select the student whose attendance is being recorded"
    )
    course_offering = models.ForeignKey(
        'courses.CourseOffering',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Select the course for which attendance is being recorded"
    )
    date = models.DateField(
        help_text="Select the date for which attendance is being recorded"
    )
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS,
        help_text="Select the attendance status for this student"
    )
    remarks = models.TextField(
        blank=True,
        help_text="Any additional remarks about the attendance (e.g., reason for absence)"
    )
    recorded_by = models.ForeignKey(
        'faculty_staff.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        help_text="The teacher who recorded this attendance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = ['student', 'course_offering', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.course_offering} - {self.date} - {self.status}"
