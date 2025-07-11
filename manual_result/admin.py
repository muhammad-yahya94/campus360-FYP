from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Custom Admin for Course
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_title', 'course_code', 'credit_hour', 'lab_work', 'semester')
    list_filter = ('semester__year_session', 'semester')
    search_fields = ('course_title', 'course_code', 'semester__name')
    autocomplete_fields = ['semester']


# Custom Admin for Semester
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'year_session')
    search_fields = ('name', 'year_session__start_year', 'year_session__end_year')


# Custom Admin for YearSession
class YearSessionAdmin(admin.ModelAdmin):
    list_display = ('start_year', 'end_year', 'department')
    search_fields = ('start_year', 'end_year', 'department__email')


# Custom Admin for StudentResult
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'student_name', 'father_name', 'course', 'total_obtained_marks', 'grade', 'status')
    search_fields = ('roll_no', 'student_name', 'father_name', 'cnic', 'course__course_title', 'course__course_code')


# Registering models with custom admin classes
admin.site.register(Course, CourseAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(YearSession, YearSessionAdmin)
admin.site.register(StudentResult, StudentResultAdmin)
