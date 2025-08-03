from django.db import models
from users.models import CustomUser
from academics.models import Program, Department, Faculty, Semester
from admissions.models import Applicant, AcademicSession
from faculty_staff.models import Teacher
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import os
from django.utils import timezone


import re  
from django.core.exceptions import ValidationError
from django.db import models

class Course(models.Model):
    opt = models.BooleanField(default=False)
    code = models.CharField(max_length=10, unique=True, help_text="Enter the unique course code (e.g., CS101).")
    name = models.CharField(max_length=200, help_text="Enter the full name of the course (e.g., Introduction to Programming).")
    credits = models.PositiveIntegerField(help_text="Enter the number of credit hours for this course.")
    lab_work = models.IntegerField(default=0, help_text="Enter the number of lab hours per week for this course (if applicable).")
    is_active = models.BooleanField(default=True, help_text="Check this if the course is currently active and can be offered.")
    description = models.TextField(blank=True, help_text="Provide a brief description or syllabus summary for the course.")
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='required_for', help_text="Select any courses that are required to be completed before taking this course (optional).")

    def clean(self):
        # Validate that code is alphanumeric
        if not re.match(r'^[A-Za-z0-9]+$', self.code):
            raise ValidationError({'code': 'Course code must contain only letters and numbers.'})
        # Convert code to uppercase
        self.code = self.code.upper()

    def save(self, *args, **kwargs):
        # Convert code to uppercase before saving
        self.code = self.code.upper()
        # Run full validation
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.name}"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

# ===== Course Offering =====
class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings', help_text="Select the core course being offered.")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_offerings', help_text="Select the teacher assigned to teach this course offering.")
    replacement_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='replacement_course_offerings')  # Active replacement
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
    name = models.CharField(max_length=100, help_text="Enter the name of the venue (e.g., Room , Lab A).")
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
        # Validate time logic
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

        # Skip conflict checks if this is part of a replacement being created
        is_replacement = hasattr(self, '_is_replacement') and self._is_replacement
        
        # Only check for conflicts if the semester is active
        if self.course_offering.semester.is_active:
            # Venue conflict check - only check against other active semesters
            overlapping_slots = TimetableSlot.objects.filter(
                course_offering__academic_session=self.course_offering.academic_session,
                course_offering__semester__is_active=True,  # Only check against active semesters
                day=self.day,
                venue=self.venue,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.id)

            if overlapping_slots.exists() and not is_replacement:
                raise ValidationError(
                    f"Venue {self.venue.name} is already booked on {self.get_day_display()} from {self.start_time} to {self.end_time} "
                    f"for an active semester."
                )

        # Get the teacher to check - use replacement_teacher if this is a replacement
        teacher_to_check = self.course_offering.replacement_teacher if is_replacement else self.course_offering.teacher
        
        if teacher_to_check:  # Only check if we have a teacher to check
            # Teacher conflict check - only check against active semesters
            teacher_slots = TimetableSlot.objects.filter(
                course_offering__teacher=teacher_to_check,
                course_offering__semester__is_active=True,  # Only check against active semesters
                day=self.day,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.id)

            for slot in teacher_slots:
                # Only check if both semesters are active
                if slot.course_offering.semester.is_active and self.course_offering.semester.is_active:
                    # Skip if this is the same course being replaced
                    if is_replacement and slot.course_offering_id == self.course_offering_id:
                        continue
                        
                    raise ValidationError(
                        f"Time conflict: Teacher {teacher_to_check.user.get_full_name()} is already scheduled on "
                        f"{self.get_day_display()} from {slot.start_time} to {slot.end_time} for an active semester."
                    )

class LectureReplacement(models.Model):
    REPLACEMENT_TYPES = [
        ('temporary', 'Temporary'),
        ('permanent', 'Permanent'),
    ]

    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='replacements',
        help_text="Select the course offering for which the teacher is being replaced."
    )
    original_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='replaced_lectures',
        help_text="Select the original teacher being replaced."
    )
    replacement_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='replacement_lectures',
        help_text="Select the teacher who will replace the original teacher."
    )
    replacement_type = models.CharField(
        max_length=10,
        choices=REPLACEMENT_TYPES,
        default='temporary',
        help_text="Specify if the replacement is temporary (one day) or permanent."
    )
    replacement_date = models.DateField(
        null=True,
        blank=True,
        help_text="For temporary replacements, specify the date of the replacement. Leave blank for permanent replacements."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the replacement was created."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the replacement is still active."
    )

    def __str__(self):
        return f"{self.replacement_teacher} replacing {self.original_teacher} for {self.course_offering} ({self.replacement_type})"

    class Meta:
        verbose_name = "Lecture Replacement"
        verbose_name_plural = "Lecture Replacements"
        unique_together = ['course_offering', 'original_teacher', 'replacement_date']

    def clean(self):
        if self.course_offering.teacher != self.original_teacher:
            raise ValidationError(
                f"The original teacher {self.original_teacher} does not match the course offering's assigned teacher {self.course_offering.teacher}."
            )
        if self.original_teacher == self.replacement_teacher:
            raise ValidationError("The replacement teacher cannot be the same as the original teacher.")
        if self.replacement_type == 'temporary' and not self.replacement_date:
            raise ValidationError("A replacement date must be provided for temporary replacements.")
        if self.replacement_type == 'permanent' and self.replacement_date:
            raise ValidationError("Permanent replacements should not have a specific replacement date.")
        if self.replacement_date:
            timetable_slots = self.course_offering.timetable_slots.all()
            for slot in timetable_slots:
                conflicting_slots = TimetableSlot.objects.filter(
                    course_offering__teacher=self.replacement_teacher,
                    day=slot.day,
                    start_time__lt=slot.end_time,
                    end_time__gt=slot.start_time
                ).exclude(course_offering__id=self.course_offering.id)
                if conflicting_slots.exists():
                    raise ValidationError(
                        f"Replacement teacher {self.replacement_teacher} has a scheduling conflict on {slot.get_day_display()} from {slot.start_time} to {slot.end_time}."
                    )
        if self.replacement_type == 'temporary' and self.replacement_date and self.replacement_date < timezone.now().date():
            self.is_active = False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.update_course_offering()

    def update_course_offering(self):
        """Update CourseOffering based on replacement status."""
        if not self.is_active or (self.replacement_type == 'temporary' and self.replacement_date and self.replacement_date < timezone.now().date()):
            self.course_offering.replacement_teacher = None
            self.course_offering.teacher = self.original_teacher
            self.course_offering.save()
            if self.is_active:
                self.is_active = False
                super().save(update_fields=['is_active'])
        else:
            self.course_offering.replacement_teacher = self.replacement_teacher
            self.course_offering.teacher = self.replacement_teacher
            self.course_offering.save()




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
        ordering = ['-created_at']





# ===== Assignment Submission =====
class AssignmentSubmission(models.Model):
    SUBMISSION_TYPES = [
        ('text', 'Rich Text'),
        ('code', 'Code'),
    ]
    
    CODE_LANGUAGES = [
        ('none', 'None'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('c', 'C'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('php', 'PHP'),
        ('sql', 'SQL'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', help_text="The assignment this submission is for.")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='submissions', help_text="The student who submitted this assignment.")
    text_content = models.TextField(blank=True, help_text="Rich text content of the submission.")
    code_content = models.TextField(blank=True, help_text="Code content of the submission.")
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPES, default='text', help_text="Type of submission content.")
    code_language = models.CharField(max_length=20, choices=CODE_LANGUAGES, default='none', help_text="Programming language for code submissions.")
    formatted_content = models.TextField(blank=True, help_text="Formatted content for display purposes.")
    file = models.FileField(upload_to='submissions/', blank=True, null=True, help_text="The file submitted by the student.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the submission was made.")
    marks_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained by the student for this submission.")
    feedback = models.TextField(blank=True, help_text="Feedback from the teacher on this submission.")
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='graded_submissions', help_text="The teacher who graded this submission.")
    graded_at = models.DateTimeField(null=True, blank=True, help_text="The date and time when the submission was graded.")

    def __str__(self):
        return f"Submission by {self.student} for {self.assignment}"

    def save(self, *args, **kwargs):
        # Format content based on submission type
        if self.submission_type == 'code' and self.code_content:
            # For code submissions, preserve line breaks and formatting
            self.formatted_content = self.code_content
        elif self.submission_type == 'text' and self.text_content:
            # For text submissions, keep the rich text formatting
            self.formatted_content = self.text_content
        else:
            self.formatted_content = self.text_content or self.code_content
        
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('assignment', 'student')
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"




# Notice Types and Priority Levels


class Notice(models.Model):
    NOTICE_TYPES = (
    ('general', 'General'),
    ('academic', 'Academic'),
    ('event', 'Event'),
    ('exam', 'Exam'),
    ('holiday', 'Holiday'),
    ('other', 'Other'),
)

    PRIORITY_LEVELS = (
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    programs = models.ManyToManyField(Program, related_name='notices', blank=True, help_text="Select programs this notice applies to (leave blank for all programs).")
    sessions = models.ManyToManyField(AcademicSession, related_name='notices', blank=True, help_text="Select academic sessions this notice applies to (leave blank for all sessions).")
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(
        upload_to='notices/attachments/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'])]
    )
    created_by = models.ForeignKey('faculty_staff.Teacher', on_delete=models.SET_NULL, null=True, related_name='created_notices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['notice_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_currently_active(self):
        now = timezone.now()
        if self.valid_until:
            return self.is_active and (self.valid_from <= now <= self.valid_until)
        return self.is_active and (self.valid_from <= now)

    @property
    def filename(self):
        return self.attachment.name.split('/')[-1] if self.attachment else None

    def get_target_audience(self):
        if self.programs.exists():
            progs = list(self.programs.values_list('name', flat=True))
            if len(progs) > 3:
                return f"{', '.join(progs[:3])} and {len(progs) - 3} more"
            return ', '.join(progs)
        if self.sessions.exists():
            sess = list(self.sessions.values_list('name', flat=True))
            if len(sess) > 3:
                return f"{', '.join(sess[:3])} and {len(sess) - 3} more"
            return ', '.join(sess)
        return "All Programs and Sessions"
    
    
class ExamResult(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='exam_results', help_text="The course offering this exam result is for.")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_results', help_text="The student this result pertains to.")
    
    # Midterm Exam Marks
    midterm_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained in Midterm Exam.")
    midterm_total = models.PositiveIntegerField(help_text="Total marks for Midterm Exam (credit_hours * 4).")
    
    # Final Exam Marks
    final_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained in Final Exam.")
    final_total = models.PositiveIntegerField(help_text="Total marks for Final Exam (credit_hours * 14).")
    
    # Sessional Marks
    sessional_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained in Sessional.")
    sessional_total = models.PositiveIntegerField(help_text="Total marks for Sessional (credit_hours * 2).")
    
    # Practical Marks
    practical_obtained = models.PositiveIntegerField(null=True, blank=True, help_text="Marks obtained in Practical.")
    practical_total = models.PositiveIntegerField(help_text="Total marks for practical (credit_hours * 20).")
    
    # Calculated fields
    total_marks = models.FloatField(default=0.0, help_text="Overall marks obtained for the exam result.")
    percentage = models.FloatField(null=True, blank=True, help_text="Overall percentage for the exam result.")
    
    # Common fields
    is_fail = models.BooleanField(default=False, help_text="Indicates if the student failed this course.")
    is_published = models.BooleanField(default=False, help_text="Whether the result is published to students")
    published_at = models.DateTimeField(null=True, blank=True, help_text="When the result was published to students")
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='graded_results', help_text="The teacher who graded this exam.")
    graded_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the result was recorded.")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks or comments on the student's performance.")

    def save(self, *args, **kwargs):
        # Calculate total marks based on course credit_hours
        if self.course_offering and self.course_offering.course:
            self.midterm_total = self.course_offering.course.credits * 4
            self.final_total = self.course_offering.course.credits * 14
            self.sessional_total = self.course_offering.course.credits * 2
            self.practical_total = self.course_offering.course.lab_work * 20
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - Exam Results ({self.course_offering})"
           
    def get_total_max_marks(self):
        """Calculate total maximum marks across all exam types"""
        total = 0
        for field in ['midterm', 'final', 'sessional', 'practical']:
            total += getattr(self, f"{field}_total", 0)
        return total

    class Meta:
        unique_together = ('course_offering', 'student')
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



class Quiz(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255, help_text="Topic name for the quiz")
    publish_flag = models.BooleanField(default=False, help_text="Check to make this quiz visible to students.")
    timer_seconds = models.PositiveIntegerField(
        choices=[
            (15, '15 seconds'),
            (30, '30 seconds'),
            (45, '45 seconds'),
            (60, '1 minute')
        ],
        default=30,
        help_text="Duration per question for all questions."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.course_offering})"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    marks = models.PositiveIntegerField(default=1, help_text="Marks for this question.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text[:50]}... (MCQ)"  

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} (Correct: {self.is_correct})"

class QuizSubmission(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.PositiveIntegerField(default=0)
    answers = models.JSONField(default=dict)  # Store {question_id: selected_option_id}

    def __str__(self):
        return f"{self.student} - {self.quiz} (Score: {self.score})"