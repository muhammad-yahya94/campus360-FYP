from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher





# ===== Semester =====
class Semester(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50)  # e.g., Semester 1, Fall 2024 - Semester 1
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.session.name} - {self.name}"

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def save(self, *args, **kwargs):
        # Ensure only one semester is current per session
        if self.is_current:
            Semester.objects.filter(session=self.session, is_current=True).exclude(id=self.id).update(is_current=False)
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
    schedule = models.CharField(max_length=200, blank=True)  # e.g., Mon/Wed 10:00-11:30
    room = models.CharField(max_length=50, blank=True)  # e.g., Room A-101

    class Meta:
        unique_together = ('semester', 'course', 'teacher')  
        verbose_name = "Course Offering"
        verbose_name_plural = "Course Offerings"

    def __str__(self):
        return f"{self.course} - {self.teacher} ({self.semester})"


