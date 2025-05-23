from django.contrib import admin
from django import forms
from .models import Student, StudentEnrollment
from admissions.models import Applicant
from users.models import CustomUser
from courses.models import CourseOffering, Semester

# Custom form for StudentAdmin
class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['applicant', 'user', 'program', 'current_semester']:
            self.fields[field].widget.can_add_related = False
            self.fields[field].widget.can_change_related = False
            self.fields[field].widget.can_delete_related = False
            
        # Filter semesters based on selected program
        if 'program' in self.data:
            try:
                program_id = int(self.data.get('program'))
                self.fields['current_semester'].queryset = Semester.objects.filter(program_id=program_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.program:
            self.fields['current_semester'].queryset = Semester.objects.filter(program=self.instance.program)

# Custom form for StudentEnrollmentAdmin
class StudentEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['student', 'course_offering']:
            self.fields[field].widget.can_add_related = False
            self.fields[field].widget.can_change_related = False
            self.fields[field].widget.can_delete_related = False

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('applicant', 'program', 'current_semester', 'university_roll_no', 'current_status')
    list_filter = ('current_status', 'program', 'current_semester__learning_level')
    search_fields = ('applicant__full_name', 'university_roll_no', 'college_roll_no')
    raw_id_fields = ('applicant', 'user')
    readonly_fields = ('enrollment_date',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('applicant', 'user', 'university_roll_no', 'college_roll_no')
        }),
        ('Academic Information', {
            'fields': ('program', 'current_semester', 'enrollment_date', 'graduation_date', 'current_status')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'applicant', 'user', 'program', 'current_semester'
        )

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    form = StudentEnrollmentAdminForm
    list_display = ('student', 'course_offering', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date', 'course_offering__semester__program', 'course_offering__semester__learning_level')
    search_fields = ('student__applicant__full_name', 'course_offering__course__code', 'course_offering__course__name')
    raw_id_fields = ('student', 'course_offering')
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course_offering')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__applicant',
            'course_offering__course',
            'course_offering__semester',
            'course_offering__academic_session'
        )