from django.contrib import admin
from django import forms
from .models import Student, StudentEnrollment

# Custom form for StudentAdmin to hide related data outside dropdowns
class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['applicant'].widget.can_add_related = False
        self.fields['applicant'].widget.can_change_related = False
        self.fields['applicant'].widget.can_delete_related = False
        self.fields['user'].widget.can_add_related = False
        self.fields['user'].widget.can_change_related = False
        self.fields['user'].widget.can_delete_related = False

# Custom form for StudentEnrollmentAdmin to hide related data outside dropdowns
class StudentEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].widget.can_add_related = False
        self.fields['student'].widget.can_change_related = False
        self.fields['student'].widget.can_delete_related = False
        self.fields['course_offering'].widget.can_add_related = False
        self.fields['course_offering'].widget.can_change_related = False
        self.fields['course_offering'].widget.can_delete_related = False

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm  # Use the custom form
    list_display = ('get_full_name', 'university_roll_no', 'college_roll_no', 'current_status', 'enrollment_date')
    list_filter = ('current_status', 'applicant__department', 'enrollment_date')
    search_fields = (
        'applicant__full_name', 
        'university_roll_no', 
        'college_roll_no',
        'applicant__cnic'
    )
    # Remove raw_id_fields to use dropdowns
    # raw_id_fields = ('applicant', 'user')  # Comment this out
    date_hierarchy = 'enrollment_date'
    ordering = ('-enrollment_date',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('applicant', 'user')
        }),
        ('Academic Information', {
            'fields': ('university_roll_no', 'college_roll_no', 'enrollment_date', 'graduation_date')
        }),
        ('Status & Emergency', {
            'fields': ('current_status', 'emergency_contact', 'emergency_phone'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.applicant.full_name
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'applicant__full_name'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'applicant', 'user', 'applicant__department'
        )

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    form = StudentEnrollmentAdminForm  # Use the custom form
    list_display = ('get_student_name', 'get_course_name', 'get_teacher', 'status', 'enrollment_date')
    list_filter = ('status', 'course_offering__semester', 'course_offering__course__department')
    search_fields = (
        'student__full_name',
        'course_offering__course__name',
        'course_offering__course__code'
    )
    # Remove raw_id_fields to use dropdowns
    # raw_id_fields = ('student', 'course_offering')  # Comment this out
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course_offering')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    def get_student_name(self, obj):
        return obj.student.full_name
    get_student_name.short_description = 'Student'
    get_student_name.admin_order_field = 'student__full_name'

    def get_course_name(self, obj):
        return obj.course_offering.course.name
    get_course_name.short_description = 'Course'
    get_course_name.admin_order_field = 'course_offering__course__name'

    def get_teacher(self, obj):
        return obj.course_offering.teacher
    get_teacher.short_description = 'Teacher'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student',
            'course_offering',
            'course_offering__course',
            'course_offering__teacher',
            'course_offering__semester'
        )