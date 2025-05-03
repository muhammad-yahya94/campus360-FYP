from django.contrib import admin
from .models import *

# ===== Degree Types Admin =====
@admin.register(DegreeType)
class DegreeTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


# ===== Faculty Admin =====
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    model_icon = 'fas fa-users'  # Icon for Faculty

# ===== Department Admin =====
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty')
    list_filter = ('faculty',)
    search_fields = ('name', 'code')
    model_icon = 'fas fa-building'  # Icon for Department

# ===== Program Admin =====
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'degree_type', 'duration_years')
    list_filter = ('degree_type', 'department')
    search_fields = ('name', 'department__name')
    model_icon = 'fas fa-chalkboard-teacher'  # Icon for Program




