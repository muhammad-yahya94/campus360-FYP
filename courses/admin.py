from django.contrib import admin
from django import forms
from .models import Semester, Course, CourseOffering

# Custom form for SemesterAdmin to hide related data outside dropdowns
class SemesterAdminForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].widget.can_add_related = False
        self.fields['program'].widget.can_change_related = False
        self.fields['program'].widget.can_delete_related = False

# Custom form for CourseOfferingAdmin to hide related data outside dropdowns
class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].widget.can_add_related = False
        self.fields['course'].widget.can_change_related = False
        self.fields['course'].widget.can_delete_related = False
        self.fields['semester'].widget.can_add_related = False
        self.fields['semester'].widget.can_change_related = False
        self.fields['semester'].widget.can_delete_related = False
        self.fields['teacher'].widget.can_add_related = False
        self.fields['teacher'].widget.can_change_related = False
        self.fields['teacher'].widget.can_delete_related = False

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    form = SemesterAdminForm
    list_display = ('name', 'program', 'start_date', 'end_date', 'is_current')  # Updated to use 'program'
    list_filter = ('program', 'is_current')  # Updated to use 'program'
    search_fields = ('name', 'program__name')  # Updated to use 'program'
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('program')  # Updated to use 'program'

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
    list_display = ('course', 'teacher', 'semester', 'room', 'schedule')
    list_filter = ('semester__program', 'course__department', 'teacher')  # Updated to use 'semester__program'
    search_fields = ('course__code', 'course__name', 'teacher__full_name', 'room')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'semester', 'semester__program'  # Updated to use 'semester__program'
        )
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'semester')
        }),
        ('Teaching Details', {
            'fields': ('teacher', 'room', 'schedule')
        }),
    )