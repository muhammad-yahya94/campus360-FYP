from django.contrib import admin
from .models import (
    Course, CourseOffering, Venue, TimetableSlot, 
    StudyMaterial, Assignment, AssignmentSubmission, 
    Notice, ExamResult, Attendance, LectureReplacement,
    Quiz, Question, Option, QuizSubmission
)
# Inline for Options in Question
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4  # Allows adding up to 4 options by default
    fields = ('text', 'is_correct')

# Inline for Questions in Quiz
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 2  # Allows adding up to 2 questions by default
    fields = ('text', 'marks')
    inlines = [OptionInline]

# Admin for Course
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'lab_work', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    filter_horizontal = ('prerequisites',)

# Admin for CourseOffering
@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'academic_session', 'semester', 'shift', 'offering_type', 'is_active')
    list_filter = ('is_active', 'shift', 'offering_type', 'academic_session', 'semester')
    search_fields = ('course__code', 'course__name', 'teacher__user__first_name', 'teacher__user__last_name')
    raw_id_fields = ('course', 'teacher', 'department', 'program')

# Admin for Venue
@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'capacity', 'is_active')
    list_filter = ('is_active', 'department')
    search_fields = ('name', 'department__name')

# Admin for TimetableSlot
@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'day', 'start_time', 'end_time', 'venue')
    list_filter = ('day', 'course_offering__academic_session', 'course_offering__semester')
    search_fields = ('course_offering__course__code', 'course_offering__course__name', 'venue__name')
    raw_id_fields = ('course_offering', 'venue')

# Admin for StudyMaterial
@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'teacher', 'topic', 'created_at')
    list_filter = ('course_offering__academic_session', 'course_offering__semester', 'created_at')
    search_fields = ('title', 'topic', 'course_offering__course__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('course_offering', 'teacher')

# Admin for Assignment
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'teacher', 'due_date', 'max_points', 'created_at')
    list_filter = ('course_offering__academic_session', 'course_offering__semester', 'due_date')
    search_fields = ('title', 'course_offering__course__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('course_offering', 'teacher')

# Admin for AssignmentSubmission
@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'marks_obtained', 'graded_by')
    list_filter = ('assignment__course_offering__academic_session', 'assignment__course_offering__semester', 'submitted_at', 'graded_at')
    search_fields = ('student__applicant__full_name', 'assignment__title')
    raw_id_fields = ('assignment', 'student', 'graded_by')
    date_hierarchy = 'submitted_at'

# Admin for Notice
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content', 'created_by__user__first_name', 'created_by__user__last_name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('created_by',)

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'student', 'remarks', 'graded_by', 'graded_at')
    list_filter = ('course_offering__academic_session', 'course_offering__semester', 'graded_at')
    search_fields = ('student__applicant__full_name', 'course_offering__course__name')
    raw_id_fields = ('course_offering', 'student', 'graded_by')
    date_hierarchy = 'graded_at'
    

# Admin for Attendance
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_offering', 'date', 'status', 'shift', 'recorded_at')
    list_filter = ('status', 'course_offering__academic_session', 'course_offering__semester', 'date', 'shift')
    search_fields = ('student__applicant__full_name', 'course_offering__course__name')
    date_hierarchy = 'date'
    raw_id_fields = ('student', 'course_offering', 'recorded_by')

# Admin for Quiz
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'publish_flag', 'timer_seconds', 'created_at')
    list_filter = ('publish_flag', 'course_offering__academic_session', 'course_offering__semester', 'created_at')
    search_fields = ('title', 'course_offering__course__name')
    date_hierarchy = 'created_at'
    inlines = [QuestionInline]
    raw_id_fields = ('course_offering',)

# Admin for Question
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'marks', 'created_at')
    list_filter = ('quiz__course_offering__academic_session', 'quiz__course_offering__semester', 'created_at')
    search_fields = ('text', 'quiz__title')
    date_hierarchy = 'created_at'
    inlines = [OptionInline]

# Admin for Option
@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    list_filter = ('is_correct', 'question__quiz__course_offering__academic_session')
    search_fields = ('text', 'question__text')

# Admin for QuizSubmission
@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'submitted_at', 'score')
    list_filter = ('quiz__course_offering__academic_session', 'quiz__course_offering__semester', 'submitted_at')
    search_fields = ('student__applicant__full_name', 'quiz__title')
    date_hierarchy = 'submitted_at'
    raw_id_fields = ('student', 'quiz')
    
    
    
admin.site.register(LectureReplacement)
   