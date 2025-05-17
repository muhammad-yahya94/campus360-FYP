from django.contrib import admin
from django import forms
from .models import (
    Semester,
    Course,
    CourseOffering,
    CourseOfferingTeacherChange,
    Assignment,
    Submission
)

# ===== Custom Forms =====

class SemesterAdminForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].widget.can_add_related = False
        self.fields['program'].widget.can_change_related = False
        self.fields['program'].widget.can_delete_related = False

class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['course', 'semester', 'teacher']:
            self.fields[field].widget.can_add_related = False
            self.fields[field].widget.can_change_related = False
            self.fields[field].widget.can_delete_related = False

# ===== Admin Classes =====

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    form = SemesterAdminForm
    list_display = ('name', 'program', 'start_date', 'end_date', 'is_current')
    list_filter = ('program', 'is_current')
    search_fields = ('name', 'program__name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('program')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'program', 'course_type', 'credits', 'is_active')
    list_filter = ('department', 'program', 'course_type', 'is_active')
    search_fields = ('code', 'name', 'description')
    filter_horizontal = ('prerequisites',)
    raw_id_fields = ('department', 'program')

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Academic Details', {
            'fields': ('department', 'program', 'course_type', 'credits')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',),
            'classes': ('collapse',)
        }),
    )

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    form = CourseOfferingAdminForm
    list_display = ('course', 'teacher', 'semester')
    list_filter = ('semester__program', 'course__department', 'teacher')
    search_fields = ('course__code', 'course__name', 'teacher__full_name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'semester', 'semester__program'
        )

    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'semester')
        }),
        ('Teaching Details', {
            'fields': ('teacher',)
        }),
    )

@admin.register(CourseOfferingTeacherChange)
class CourseOfferingTeacherChangeAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'old_teacher', 'new_teacher', 'change_date')
    list_filter = ('change_date', 'old_teacher', 'new_teacher')
    search_fields = ('course_offering__course__name', 'old_teacher__full_name', 'new_teacher__full_name')
    date_hierarchy = 'change_date'
    ordering = ('-change_date',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'assignment_type', 'due_date', 'max_points')
    list_filter = ('assignment_type', 'due_date')
    search_fields = ('title', 'description', 'course_offering__course__name')
    date_hierarchy = 'due_date'
    ordering = ('-due_date',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'grade')
    list_filter = ('submitted_at', 'grade')
    search_fields = ('assignment__title', 'student__username', 'student__email')
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',)
