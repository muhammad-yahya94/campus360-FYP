from django.contrib import admin
from django import forms
from .models import (
    Course,
    CourseOffering,
)
from academics.models import Program, Department
from faculty_staff.models import Teacher

# ===== Custom Forms =====

class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['course', 'teacher', 'department', 'program', 'semester']:
            self.fields[field].widget.can_add_related = False
            self.fields[field].widget.can_change_related = False
            self.fields[field].widget.can_delete_related = False

# ===== Admin Classes =====

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    filter_horizontal = ('prerequisites',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'credits', 'is_active')
        }),
        ('Course Details', {
            'fields': ('description', 'prerequisites')
        }),
    )

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    form = CourseOfferingAdminForm
    list_display = ('course', 'semester', 'teacher', 'offering_type', 'is_active', 'current_enrollment', 'max_capacity')
    list_filter = ('is_active', 'semester__program',  'offering_type', 'department')
    search_fields = ('course__code', 'course__name', 'teacher__user__username', 'semester__name')
    ordering = ('semester__program', 'semester__number', 'course__code')
    raw_id_fields = ('course', 'teacher', 'department', 'program', 'semester', 'academic_session')
    list_editable = ('is_active', 'max_capacity')
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'teacher', 'offering_type')
        }),
        ('Program & Department', {
            'fields': ('program', 'department')
        }),
        ('Semester & Session', {
            'fields': ('semester', 'academic_session')
        }),
        ('Enrollment Settings', {
            'fields': ('is_active', 'max_capacity', 'current_enrollment')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'department', 'program', 'semester', 'academic_session'
        )
