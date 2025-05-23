from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from courses.models import Course, CourseOffering, Semester

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
    current_semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name='current_students', help_text="Current semester of the student")
    
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
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return f"{self.applicant.full_name} ({self.university_roll_no})"

    def save(self, *args, **kwargs):
        # Automatically create a user if not exists
        if not self.user and self.applicant.user:
            self.user = self.applicant.user
            
        # If this is a new student, set their current semester to the first semester of their program
        if not self.pk and not self.current_semester:
            first_semester = Semester.objects.filter(
                program=self.program,
                number=1
            ).first()
            if first_semester:
                self.current_semester = first_semester
                
        super().save(*args, **kwargs)
        
    def get_available_courses(self):
        """Get courses available for enrollment in current semester"""
        return CourseOffering.objects.filter(
            semester=self.current_semester,
            is_active=True,
            current_enrollment__lt=models.F('max_capacity')
        ).exclude(
            enrollments__student=self
        )
        
    def get_enrolled_courses(self):
        """Get currently enrolled courses"""
        return self.enrollments.filter(
            status='enrolled',
            course_offering__semester=self.current_semester
        )
        
    def get_completed_courses(self):
        """Get completed courses"""
        return self.enrollments.filter(status='completed')
        
    def can_enroll_in_course(self, course_offering):
        """Check if student can enroll in a course"""
        if course_offering.semester != self.current_semester:
            return False
        if course_offering.current_enrollment >= course_offering.max_capacity:
            return False
        if self.enrollments.filter(course_offering=course_offering).exists():
            return False
        return True
        
    def can_advance_semester(self):
        """Check if student can advance to next semester"""
        # Get all required courses for current semester
        required_courses = self.current_semester.course_offerings.filter(
            offering_type__in=['core', 'major']
        )
        
        # Check if all required courses are completed
        completed_courses = self.enrollments.filter(
            course_offering__in=required_courses,
            status='completed'
        )
        
        return completed_courses.count() == required_courses.count()
        
    def advance_semester(self):
        """Advance student to next semester"""
        if not self.can_advance_semester():
            raise ValidationError("Cannot advance semester: Not all required courses are completed")
            
        next_semester = Semester.objects.filter(
            program=self.program,
            number=self.current_semester.number + 1
        ).first()
        
        if not next_semester:
            raise ValidationError("No next semester available")
            
        self.current_semester = next_semester
        self.save()

# ===== Student Enrollment =====
class StudentEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments', help_text="Select the student for this enrollment.")
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='enrollments', help_text="Select the specific course offering the student is enrolling in.")
    enrollment_date = models.DateTimeField(auto_now_add=True, help_text="The date and time this enrollment was recorded.")
    status = models.CharField(max_length=20, choices=[
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='enrolled', help_text="Select the status of this course enrollment.")

    class Meta:
        unique_together = ('student', 'course_offering')
        verbose_name = "Student Enrollment"
        verbose_name_plural = "Student Enrollments"

    def __str__(self):
        return f"{self.student.applicant.full_name} - {self.course_offering}"

    def save(self, *args, **kwargs):
        # Update the current enrollment count in the course offering
        if self.status == 'enrolled':
            self.course_offering.current_enrollment += 1
            self.course_offering.save()
        super().save(*args, **kwargs)

