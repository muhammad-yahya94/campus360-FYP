from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Faculty, Department, Program,
    Semester,
)
from django.utils import timezone

# ===== Faculty Admin =====    
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'slug']  # 'description' exists in Faculty model
    model_icon = 'fas fa-users'  # Icon for Faculty

# ===== Department Admin =====
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'code')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('faculty',)
    search_fields = ['name', 'code', 'slug', 'introduction', 'details', 'faculty__name']  # 'introduction' and 'details' exist
    autocomplete_fields = ['faculty']
    model_icon = 'fas fa-building'  # Icon for Department

# ===== Program Admin =====
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'degree_type', 'duration_years', 'total_semesters', 'start_year', 'end_year', 'is_active')
    list_filter = ('department__faculty', 'department', 'degree_type', 'is_active', 'start_year', 'end_year')
    search_fields = [
        'name', 'degree_type',  # Removed 'description'
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
        # Removed 'Additional Information' section since 'description' doesn't exist
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
    list_display = ('program', 'number', 'name', 'is_active')
    list_filter = ('program', 'is_active')
    search_fields = [
        'program__name',
        'number',
        'name',
        'description',  # 'description' exists in Semester model
        'program__start_year',
        'program__end_year'
    ]
    autocomplete_fields = ['program']
    fieldsets = (
        ('Basic Information', {
            'fields': ('program', 'number', 'name', 'is_active')
        }),
        ('Dates', {
            'fields': ('start_time', 'end_time')
        }),
        ('Description', {  # Added to include the 'description' field
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )