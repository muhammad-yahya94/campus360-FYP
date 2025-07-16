from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty , Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from django.utils import timezone


# ===== Student Model =====
class Student(models.Model):
    applicant = models.OneToOneField(
        Applicant,
        on_delete=models.CASCADE,
        related_name='student_profile',
        primary_key=True,
        help_text="Select the applicant record associated with this student."
    )
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
        help_text="Select the user account linked to this student profile (optional, automatically linked if available)."
    )
    university_roll_no = models.IntegerField(blank=True,null=True, help_text="Enter the student's official university roll number.")
    college_roll_no = models.IntegerField(blank=True,null=True, help_text="Enter the student's college roll number (if applicable).")
    enrollment_date = models.DateField(help_text="Select the official date when the student was enrolled.")
    graduation_date = models.DateField(null=True, blank=True, help_text="Select the date when the student graduated (optional).")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='students', help_text="The program the student is enrolled in")
    
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
        # Update the student's current_semester
        if self.status == 'enrolled':
            self.student.current_semester = self.semester
            self.student.save()
        elif self.status in ['completed', 'dropped']:
            # Find the most recent active semester enrollment
            latest_enrollment = StudentSemesterEnrollment.objects.filter(
                student=self.student,
                status='enrolled'
            ).exclude(id=self.id).order_by('-enrollment_date').first()
            if latest_enrollment:
                self.student.current_semester = latest_enrollment.semester
            else:
                # Fall back to the first semester of the program
                first_semester = Semester.objects.filter(
                    program=self.student.program,
                    number=1
                ).first()
                self.student.current_semester = first_semester
            self.student.save()
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