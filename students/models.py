from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty , Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from django.utils import timezone


class Student(models.Model):
    applicant = models.OneToOneField(
        'admissions.Applicant',
        on_delete=models.CASCADE,
        related_name='student_profile',
        primary_key=True,
        help_text="Select the applicant record associated with this student."
    )
    user = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
        help_text="Select the user account linked to this student profile (optional, automatically linked if available)."
    )
    Registration_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Enter the student's unique registration number."
    )
    university_roll_no = models.IntegerField(blank=True,null=True, help_text="Enter the student's official university roll number.")
    college_roll_no = models.IntegerField(blank=True,null=True, help_text="Enter the student's college roll number (if applicable).")
    enrollment_date = models.DateField(help_text="Select the official date when the student was enrolled.")
    graduation_date = models.DateField(null=True, blank=True, help_text="Select the date when the student graduated (optional).")
    program = models.ForeignKey('academics.Program', on_delete=models.CASCADE, related_name='students', help_text="The program the student is enrolled in")
    
    current_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('graduated', 'Graduated'),
            ('withdrawn', 'Withdrawn'),
        ],
        default='active',
        help_text="Select the current academic status of the student."
    )
    
    emergency_contact = models.CharField(max_length=100, blank=True, help_text="Enter the name of an emergency contact person.")
    emergency_phone = models.CharField(max_length=15, blank=True, help_text="Enter the phone number for the emergency contact.")
    role = models.CharField(
        max_length=2,
        choices=[('CR', 'Class Representative'), ('GR', 'Girls Representative')],
        null=True,
        blank=True,
        help_text="Select the student's role (CR/GR) if applicable."
    )
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return f"{self.applicant.full_name} ({self.university_roll_no})"
        

class StudentSemesterEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_enrollments', help_text="Select the student for this semester enrollment.")
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='semester_enrollments', help_text="Select the semester the student is enrolling in.")
    enrollment_date = models.DateTimeField(auto_now_add=True, help_text="The date and time this enrollment was recorded.")
    status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='enrolled', help_text="Select the status of this semester enrollment.")

    class Meta:
        verbose_name = "Student Semester Enrollment"
        verbose_name_plural = "Student Semester Enrollments"
        unique_together = ('student', 'semester')  # Ensure one enrollment per student per semester

    def __str__(self):
        return f"{self.student.applicant.full_name} - {self.semester}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class CourseEnrollment(models.Model):
    student_semester_enrollment = models.ForeignKey(StudentSemesterEnrollment, on_delete=models.CASCADE, related_name='course_enrollments')
    course_offering = models.ForeignKey('courses.CourseOffering', on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True, help_text="The date and time this course enrollment was recorded.")
    status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='enrolled', help_text="Select the status of this course enrollment.")

    class Meta:
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"
        unique_together = ('student_semester_enrollment', 'course_offering')  # Prevent duplicate enrollments in the same course

    def __str__(self):
        return f"{self.student_semester_enrollment.student.applicant.full_name} - {self.course_offering}"
    
    
class StudentFundPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
    ]

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fund_payments'
    )
    fund = models.ForeignKey(
        'faculty_staff.DepartmentFund',
        on_delete=models.CASCADE,
        related_name='student_payments'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text="Payment status for this fund"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount paid by the student"
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the payment was made"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional notes about the payment"
    )
    proof = models.FileField(
        upload_to='payment_proofs/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Upload proof of payment (PDF, JPG, or PNG)"
    )
    verified_by = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments',
        help_text="Student who verified this payment (CR/GR)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'fund')
        verbose_name = "Student Fund Payment"
        verbose_name_plural = "Student Fund Payments"

    def __str__(self):
        return f"{self.student} - {self.fund}: {self.get_status_display()}"