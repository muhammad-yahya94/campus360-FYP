from django.contrib import admin
from .models import *

# ===== Degree Types Admin =====
@admin.register(DegreeType)
class DegreeTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    model_icon = 'fas fa-graduation-cap'  # Icon for DegreeType

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

# ===== Academic Session Admin =====
@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    search_fields = ('name',)
    model_icon = 'fas fa-calendar-alt'  # Icon for AcademicSession

# ===== Semester Admin =====
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'start_date', 'end_date')
    list_filter = ('session',)
    model_icon = 'fas fa-calendar'  # Icon for Semester

# ===== Admission Cycle Admin =====
@admin.register(AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    list_display = ('program', 'session', 'application_start', 'application_end', 'is_open')
    list_filter = ('program', 'session')
    search_fields = ('program__name',)
    model_icon = 'fas fa-calendar-check'  # Icon for AdmissionCycle

# ===== Applicant Admin =====
@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'program', 'admission_cycle', 'status', 'applied_at')
    
    def user__username(self, obj):
        return obj.user.username
    user__username.short_description = 'Username'
    
    model_icon = 'fas fa-user-tie'  # Icon for Applicant

# ===== Course Admin =====
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'credits')
    list_filter = ('department',)
    search_fields = ('code', 'title')
    model_icon = 'fas fa-book'  # Icon for Course

# ===== Enrollment Admin =====
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'grade')
    list_filter = ('semester', 'course')
    search_fields = ('student__username', 'course__title')
    model_icon = 'fas fa-user-graduate'  # Icon for Enrollment






from django.contrib import admin
from .models import Slider, Alumni, Gallery, News, Event
from django_ckeditor_5.widgets import CKEditor5Widget
from django import forms

# -------------------------------
# CKEditor 5 Admin Configuration
# -------------------------------
# (No need for separate forms - CK5 integrates directly)

# Register Models
@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('name', 'graduation_year', 'profession')
    search_fields = ('name', 'profession')

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_added')
    list_per_page = 20

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'is_published')
    list_filter = ('is_published',)
    
    # CKEditor 5 integration
    formfield_overrides = {
        models.TextField: {
            'widget': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"},
                config_name="extends"  # Uses the 'extends' config from settings
            )
        }
    }

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location')
    search_fields = ('title', 'location')
    
    # CKEditor 5 integration
    formfield_overrides = {
        models.TextField: {
            'widget': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"},
                config_name="extends"  # Same config as News
            )
        }
    }