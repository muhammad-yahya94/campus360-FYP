from django.contrib import admin
from django import forms
from .models import (
    Course,
    CourseOffering
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
        for field in ['course', 'teacher', 'department', 'program']:
            self.fields[field].widget.can_add_related = False
            self.fields[field].widget.can_change_related = False
            self.fields[field].widget.can_delete_related = False

# ===== Admin Classes =====

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'is_active')
    list_filter = ('is_active',)
    search_fields = ['code', 'name']
    autocomplete_fields = ['prerequisites']
    filter_horizontal = ['prerequisites']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active', 'credits')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',),
            'classes': ('collapse',)
        }),
    )

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    form = CourseOfferingAdminForm
    list_display = ('course', 'teacher', 'department', 'program', 'offering_type')
    list_filter = ('offering_type', 'department', 'program', 'teacher__department')
    search_fields = ['course__name', 'course__code', 'teacher__user__first_name', 'teacher__user__last_name', 'department__name', 'program__name']
    autocomplete_fields = ['course', 'teacher', 'department', 'program']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'department', 'program'
        )

    fieldsets = (
        ('Course Offering Information', {
            'fields': ('course', 'teacher', 'department', 'program', 'offering_type')
        }),
    )
