from django.contrib import admin
from django import forms
from .models import Student, StudentSemesterEnrollment, CourseEnrollment
from courses.models import CourseOffering, Course
from admissions.models import Applicant
from users.models import CustomUser
from academics.models import Program, Semester
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.urls import path
from django.db.models import Q

class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['applicant', 'user', 'program']:
            self.fields[field].widget.can_add_related = False

class StudentSemesterEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = StudentSemesterEnrollment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['student', 'semester']:
            self.fields[field].widget.can_add_related = False

class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['course', 'teacher', 'semester']:
            self.fields[field].widget.can_add_related = False

class ApplicantAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Applicant.objects.all()
        if self.q:
            qs = qs.filter(full_name__icontains=self.q)
        return qs.distinct()[:20]

class CustomUserAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = CustomUser.objects.all()
        if self.q:
            qs = qs.filter(Q(email__icontains=self.q) | Q(first_name__icontains=self.q) | Q(last_name__icontains=self.q))
        return qs.distinct()[:20]

class ProgramAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Program.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()[:20]

class SemesterAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Semester.objects.all()
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(number__icontains=self.q))
        return qs.distinct()[:20]

class StudentAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Student.objects.all()
        if self.q:
            qs = qs.filter(applicant__full_name__icontains=self.q)
        return qs.distinct()[:20]

class CourseAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Course.objects.all()
        if self.q:
            qs = qs.filter(Q(code__icontains=self.q) | Q(title__icontains=self.q))
        return qs.distinct()[:20]

class CourseOfferingAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = CourseOffering.objects.all().select_related('course', 'semester')
        if self.q:
            qs = qs.filter(Q(course__code__icontains=self.q) | Q(course__name__icontains=self.q) | Q(semester__name__icontains=self.q))
        return qs.distinct()[:20]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('applicant', 'program', 'Registration_number', 'university_roll_no', 'applicant__session', 'applicant__shift', 'current_status', 'enrollment_date')
    list_filter = ('current_status', 'program')  
    search_fields = ('applicant__full_name', 'Registration_number', 'university_roll_no', 'college_roll_no', 'user__email', 'program__name', 'program__degree_type', 'program__department__name')
    autocomplete_fields = ('applicant', 'user', 'program')
    readonly_fields = ('enrollment_date', 'graduation_date')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('applicant', 'user', 'Registration_number', 'university_roll_no', 'college_roll_no', 'role',)
        }),
        ('Academic Information', {
            'fields': ('program', 'enrollment_date', 'graduation_date', 'current_status')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_phone'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'applicant', 'user', 'program'
        )

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('applicant-autocomplete/', self.admin_site.admin_view(ApplicantAutocompleteView.as_view()), name='applicant_autocomplete'),
            path('user-autocomplete/', self.admin_site.admin_view(CustomUserAutocompleteView.as_view()), name='user_autocomplete'),
            path('program-autocomplete/', self.admin_site.admin_view(ProgramAutocompleteView.as_view()), name='program_autocomplete'),
            path('semester-autocomplete/', self.admin_site.admin_view(SemesterAutocompleteView.as_view()), name='semester_autocomplete'),
        ]
        return urls

@admin.register(StudentSemesterEnrollment)
class StudentSemesterEnrollmentAdmin(admin.ModelAdmin):
    form = StudentSemesterEnrollmentAdminForm
    list_display = ('student', 'semester', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date', 'semester__program', 'semester__number')
    search_fields = ('student__applicant__full_name', 'semester__name')
    autocomplete_fields = ('student', 'semester')
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'semester')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__applicant',
            'semester__program',
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('student-autocomplete/', self.admin_site.admin_view(StudentAutocompleteView.as_view()), name='student_autocomplete'),
            path('semester-autocomplete/', self.admin_site.admin_view(SemesterAutocompleteView.as_view()), name='semester_autocomplete'),
        ]
        return urls

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student_roll_no', 'student_name', 'course_offering', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date', 'course_offering__course', 'course_offering__semester')
    search_fields = (
        'student_semester_enrollment__student__applicant__full_name', 
        'student_semester_enrollment__student__university_roll_no',
        'course_offering__course__code',
        'course_offering__course__name'
    )
    autocomplete_fields = ('student_semester_enrollment', 'course_offering')
    list_select_related = (
        'student_semester_enrollment__student',
        'student_semester_enrollment__student__applicant',
        'course_offering__course',
        'course_offering__semester'
    )
    
    def student_roll_no(self, obj):
        return obj.student_semester_enrollment.student.university_roll_no
    student_roll_no.short_description = 'Roll No'
    student_roll_no.admin_order_field = 'student_semester_enrollment__student__university_roll_no'
    
    def student_name(self, obj):
        return obj.student_semester_enrollment.student.applicant.full_name
    student_name.short_description = 'Student Name'
    student_name.admin_order_field = 'student_semester_enrollment__student__applicant__full_name'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_semester_enrollment__student__applicant',
            'course_offering__course',
            'course_offering__semester'
        )

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('student-semester-enrollment-autocomplete/', self.admin_site.admin_view(StudentAutocompleteView.as_view()), name='student_semester_enrollment_autocomplete'),
            path('course-offering-autocomplete/', self.admin_site.admin_view(CourseOfferingAutocompleteView.as_view()), name='course_offering_autocomplete'),
        ]
        return urls