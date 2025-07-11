from django.db import models
from django.utils import timezone
from users.models import CustomUser


class YearSession(models.Model):
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    department = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.start_year}-{self.end_year}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not hasattr(self, 'semester_set') or not self.semester_set.exists():
            for i in range(1, 9):
                Semester.objects.create(
                    name=f"Semester {i}", 
                    number=i, 
                    year_session=self
                )


class Semester(models.Model):
    name = models.CharField(max_length=50)
    number = models.PositiveIntegerField()
    year_session = models.ForeignKey(
        YearSession, 
        on_delete=models.CASCADE,
        related_name='semesters'
    )
    
    class Meta:
        ordering = ['number']
        unique_together = ('number', 'year_session')
    
    def __str__(self):
        return f"{self.name} ({self.year_session})"


class Course(models.Model):
    CREDIT_HOUR_CHOICES = [
        (0, '0 Credit Hour'),
        (1, '1 Credit Hour'),
        (2, '2 Credit Hours'),
        (3, '3 Credit Hours'),
        (4, '4 Credit Hours'),
        (5, '5 Credit Hours'),
        (6, '6 Credit Hours'),
    ]

    LAB_WORK_CHOICES = [
        (0, 'No Lab Sessions'),
        (1, '1 Lab Session'),
        (6, '6 Lab Session'),
    ]
    
    opt = models.BooleanField(default=False)
    course_title = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, unique=True)
    credit_hour = models.IntegerField(choices=CREDIT_HOUR_CHOICES, default=3)
    lab_work = models.IntegerField(choices=LAB_WORK_CHOICES, default=0)
    semester = models.ForeignKey(
        'Semester', 
        on_delete=models.CASCADE, 
        related_name='courses'
    )
    
    class Meta:
        ordering = ['course_code']
        unique_together = ('course_code', 'semester')

    def __str__(self):
        return f"{self.course_title} ({self.course_code})"



class StudentResult(models.Model):
    STATUS_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('INCOMPLETE', 'Incomplete'),
        ('WITHDRAWN', 'Withdrawn'),
        ('NOT_NOTIFIED', 'Result Not Notified'),
    ]
    
    roll_no = models.CharField(max_length=20, db_index=True)
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    cnic = models.CharField(max_length=20, blank=True, null=True)
    session = models.CharField(max_length=20)
    attempt = models.PositiveIntegerField(default=1)
    internal_marks = models.FloatField(null=True, blank=True)
    mid_term_marks = models.FloatField(null=True, blank=True)
    final_term_marks = models.FloatField(null=True, blank=True)
    practical_work = models.FloatField(null=True, blank=True)
    total_obtained_marks = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='NOT_NOTIFIED',
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='student_results'
    )

    class Meta:
        ordering = ['course__course_code', 'roll_no']
        unique_together = ('roll_no', 'course')
        verbose_name = 'Student Result'
        verbose_name_plural = 'Student Results'

    def __str__(self):
        return f"{self.student_name} ({self.roll_no}) - {self.course.course_code}"
    
    def save(self, *args, **kwargs):
        # Calculate total marks if not provided
        if self.total_obtained_marks is None:
            self.total_obtained_marks = (
                (self.internal_marks or 0) + 
                (self.mid_term_marks or 0) + 
                (self.final_term_marks or 0) + 
                (self.practical_work or 0)
            )
        
        # Calculate percentage if not provided and total_marks is available
        if self.percentage is None and self.course and self.course.credit_hour > 0:
            max_marks = self.course.credit_hour * 20  # Assuming 20 marks per credit hour
            if max_marks > 0:
                self.percentage = (self.total_obtained_marks / max_marks) * 100
        
        super().save(*args, **kwargs)
