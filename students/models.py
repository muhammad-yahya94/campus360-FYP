from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty , Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
import logging
import pickle

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)



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
    
class EmbeddingsEncode(models.Model):
    session = models.CharField(max_length=50, help_text="Academic session (e.g., 2022-2026)")
    program = models.CharField(max_length=50, help_text="Program name (e.g., BSCS)")
    shift = models.CharField(
        max_length=20,
        choices=[('Morning', 'morning'), ('Evening', 'evening')],
        default='Morning',
        help_text="Shift of the program (e.g., Morning, Evening)"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of creation")

    class Meta:
        verbose_name = "Embedding Encode"
        verbose_name_plural = "Embedding Encodes"
        indexes = [
            models.Index(fields=['session', 'program', 'shift']),
        ]

    def __str__(self):
        return f"{self.session} - {self.program} - {self.shift}"
    
class FaceEmbedding(models.Model):
    ecode = models.ForeignKey(
        EmbeddingsEncode,
        on_delete=models.CASCADE,
        help_text="Reference to EmbeddingsEncode record"
    )
    cnic = models.CharField(max_length=15, help_text="Unique CNIC of the student (e.g., 12345-6789012-3)")
    embeddings = models.BinaryField(help_text="Serialized face embedding data")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of creation")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp of last update")

    def set_embedding(self, embedding_array):
        """Convert numpy array to binary for storage"""
        try:
            self.embeddings = pickle.dumps(embedding_array)
        except Exception as e:
            logger.error(f"Serialization error for embedding: {e}")
            raise

    def get_embedding(self):
        """Deserialize binary data to numpy array"""
        try:
            return pickle.loads(self.embeddings)
        except Exception as e:
            logger.warning(f"Deserialization error: {e}")
            return None

    class Meta:
        verbose_name = "Face Embedding"
        verbose_name_plural = "Face Embeddings"
        indexes = [
            models.Index(fields=['ecode', 'cnic']),
        ]

    def __str__(self):
        return f"FaceEmbedding for ecode {self.ecode.id} and cnic {self.cnic.cnic}"