from django.contrib import admin
from .models import Faculty, Department, Program


# ===== Faculty Admin =====
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    model_icon = 'fas fa-users'  # Icon for Faculty

# ===== Department Admin =====
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'code')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('faculty',)
    search_fields = ['name', 'code']
    autocomplete_fields = ['faculty']
    model_icon = 'fas fa-building'  # Icon for Department

# ===== Program Admin =====
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'degree_type', 'duration_years', 'total_semesters')
    list_filter = ('department__faculty', 'department', 'degree_type')
    search_fields = ['name', 'degree_type']
    autocomplete_fields = ['department']
    model_icon = 'fas fa-chalkboard-teacher'  # Icon for Program




