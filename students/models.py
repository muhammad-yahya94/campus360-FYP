from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from courses.models import Course , CourseOffering 

# ===== Student Model =====
class Student(models.Model):
    applicant = models.OneToOneField(
        Applicant,
        on_delete=models.CASCADE,
        related_name='student_profile',
        primary_key=True
    )
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    university_roll_no = models.IntegerField(blank=True,null=True)
    college_roll_no = models.IntegerField(blank=True,null=True)
    enrollment_date = models.DateField()  # Official enrollment date
    graduation_date = models.DateField(null=True, blank=True)
    current_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('graduated', 'Graduated'),
            ('withdrawn', 'Withdrawn'),
        ],
        default='active'
    )
    # You can add more student-specific fields here
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
      

    def __str__(self):
        return f"{self.applicant.full_name} ({self.university_roll_no})"

    def save(self, *args, **kwargs):
        # Automatically create a user if not exists
        if not self.user and self.applicant.user:
            self.user = self.applicant.user
        super().save(*args, **kwargs)





# ===== Student Enrollment =====
class StudentEnrollment(models.Model):
    student = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='enrollments')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
    ('enrolled', 'Enrolled'),
    ('completed', 'Completed'),
    ('dropped', 'Dropped'),
], default='enrolled')



    class Meta:
        unique_together = ('student', 'course_offering')  # Prevent duplicate enrollments
        verbose_name = "Student Enrollment"
        verbose_name_plural = "Student Enrollments"

    def __str__(self):
        return f"{self.student.full_name} - {self.course_offering.course}"

