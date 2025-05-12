from django.contrib import admin
from .models import Semester, Course, CourseOffering

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'start_date', 'end_date', 'is_current')
    list_filter = ('session', 'is_current')
    search_fields = ('name', 'session__name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'program', 'course_type', 'credits', 'is_active')
    list_filter = ('department', 'program', 'course_type', 'is_active')
    search_fields = ('code', 'name', 'description')
    filter_horizontal = ('prerequisites',)  # For better many-to-many management
    raw_id_fields = ('department', 'program')  # Useful if you have many departments/programs
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Academic Details', {
            'fields': ('department', 'program', 'course_type', 'credits')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
    )

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'semester', 'room', 'schedule')
    list_filter = ('semester', 'course__department', 'teacher')
    search_fields = ('course__code', 'course__name', 'teacher__full_name', 'room')
    raw_id_fields = ('course', 'teacher', 'semester')  # Better for performance with many records
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'semester', 'semester__session'
        )
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'semester')
        }),
        ('Teaching Details', {
            'fields': ('teacher', 'room', 'schedule')
        }),
    )