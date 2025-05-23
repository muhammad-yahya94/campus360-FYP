from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Faculty, Department, Program,
    Semester, GradingSystem,
    StudentGrade, Attendance
)


# ===== Faculty Admin =====
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'slug']
    model_icon = 'fas fa-users'  # Icon for Faculty

# ===== Department Admin =====
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'code')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('faculty',)
    search_fields = ['name', 'code', 'slug', 'introduction', 'details', 'faculty__name']
    autocomplete_fields = ['faculty']
    model_icon = 'fas fa-building'  # Icon for Department

# ===== Program Admin =====
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'degree_type', 'duration_years', 'total_semesters', 'start_year', 'end_year', 'is_active')
    list_filter = ('department__faculty', 'department', 'degree_type', 'is_active', 'start_year', 'end_year')
    search_fields = [
        'name', 'degree_type', 'description',
        'department__name', 'department__code',
        'department__faculty__name'
    ]
    autocomplete_fields = ['department']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'department', 'degree_type', 'duration_years', 'total_semesters')
        }),
        ('Program Status', {
            'fields': ('start_year', 'end_year', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('start_year', 'end_year')
        return self.readonly_fields


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_session', 'semester_number', 'semester_type', 
                   'is_active', 'registration_status', 'classes_status')
    list_filter = ('academic_session', 'semester_type', 'is_active')
    search_fields = [
        'academic_session__name',
        'semester_number',
        'semester_type',
        'academic_session__start_year',
        'academic_session__end_year'
    ]
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['academic_session']
    fieldsets = (
        ('Basic Information', {
            'fields': ('academic_session', 'semester_number', 'semester_type', 'is_active')
        }),
        ('Dates', {
            'fields': (
                'start_date', 'end_date',
                'registration_start', 'registration_end',
                'classes_start',
                'mid_term_start', 'mid_term_end',
                'final_term_start', 'final_term_end'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def registration_status(self, obj):
        if obj.is_registration_open():
            return format_html('<span style="color: green;">Open</span>')
        return format_html('<span style="color: red;">Closed</span>')
    registration_status.short_description = 'Registration Status'

    def classes_status(self, obj):
        if obj.is_classes_running():
            return format_html('<span style="color: green;">Running</span>')
        return format_html('<span style="color: red;">Not Running</span>')
    classes_status.short_description = 'Classes Status'


@admin.register(GradingSystem)
class GradingSystemAdmin(admin.ModelAdmin):
    list_display = ('grade', 'min_marks', 'max_marks', 'grade_points', 
                   'description', 'is_passing')
    list_filter = ('is_passing',)
    search_fields = [
        'grade', 'description',
        'min_marks', 'max_marks',
        'grade_points'
    ]
    ordering = ('-grade_points',)


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_offering', 'total_marks', 'grade', 
                   'created_at')
    list_filter = ('grade', 'course_offering')
    search_fields = [
        'student__user__email',
        'student__user__first_name',
        'student__user__last_name',
        'course_offering__course__name',
        'course_offering__course__code',
        'grade__grade',
        'grade__description',
        'remarks'
    ]
    readonly_fields = ('total_marks', 'created_at', 'updated_at')
    autocomplete_fields = ['student', 'course_offering', 'grade']
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'course_offering')
        }),
        ('Marks', {
            'fields': (
                'mid_term_marks', 'final_term_marks',
                'assignment_marks', 'quiz_marks',
                'total_marks', 'grade'
            )
        }),
        ('Additional Information', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_offering', 'date', 'status', 
                   'recorded_by', 'created_at')
    list_filter = ('status', 'date', 'course_offering')
    search_fields = [
        'student__user__email',
        'student__user__first_name',
        'student__user__last_name',
        'course_offering__course__name',
        'course_offering__course__code',
        'recorded_by__user__email',
        'recorded_by__user__first_name',
        'recorded_by__user__last_name',
        'remarks',
        'status'
    ]
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['student', 'course_offering', 'recorded_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'course_offering', 'date', 'status')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set recorded_by when creating new record
            obj.recorded_by = request.user.teacher
        super().save_model(request, obj, form, change)




