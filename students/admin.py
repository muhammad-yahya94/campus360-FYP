from django.contrib import admin
from django import forms
from .models import Student, StudentSemesterEnrollment, CourseEnrollment  # Added CourseEnrollment
from courses.models import CourseOffering, Course
from admissions.models import Applicant
from users.models import CustomUser
from academics.models import Program, Semester
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.urls import path
from django.db.models import Q

# ===== Custom Forms =====
class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['applicant', 'user', 'program', 'current_semester']:
            self.fields[field].widget.can_add_related = False
        
        if 'program' in self.data:
            try:
                program_id = int(self.data.get('program'))
                self.fields['current_semester'].queryset = Semester.objects.filter(program_id=program_id).order_by('number')
            except (ValueError, TypeError):
                self.fields['current_semester'].queryset = Semester.objects.none()
        elif self.instance.pk and self.instance.program:
            self.fields['current_semester'].queryset = Semester.objects.filter(program=self.instance.program).order_by('number')
        else:
            self.fields['current_semester'].queryset = Semester.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('current_semester') and cleaned_data.get('program'):
            first_semester = Semester.objects.filter(program=cleaned_data['program'], number=1).first()
            if first_semester:
                cleaned_data['current_semester'] = first_semester
        return cleaned_data

class StudentSemesterEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = StudentSemesterEnrollment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['student', 'semester']:
            self.fields[field].widget.can_add_related = False
        # Remove course_offering from form fields since it's not a model field anymore

class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['course', 'teacher', 'semester']:
            self.fields[field].widget.can_add_related = False

# ===== Custom Autocomplete Views =====
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

# ===== Admin Classes =====
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('applicant', 'program', 'current_semester', 'university_roll_no', 'current_status', 'enrollment_date')
    list_filter = ('current_status', 'program', 'current_semester')
    search_fields = ('applicant__full_name', 'university_roll_no', 'college_roll_no', 'user__email')
    autocomplete_fields = ('applicant', 'user', 'program', 'current_semester')
    readonly_fields = ('enrollment_date', 'graduation_date')
    
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

    def save_model(self, request, obj, form, change):
        if not obj.current_semester and obj.program:
            first_semester = Semester.objects.filter(program=obj.program, number=1).first()
            if first_semester:
                obj.current_semester = first_semester
        super().save_model(request, obj, form, change)

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
    list_display = ('student', 'semester', 'enrollment_date', 'status')  # Removed course_offering
    list_filter = ('status', 'enrollment_date', 'semester__program', 'semester__number')  # Removed course_offering__course
    search_fields = ('student__applicant__full_name', 'semester__name')  # Removed course_offering references
    autocomplete_fields = ('student', 'semester')  # Removed course_offering
    readonly_fields = ('enrollment_date',)
    ordering = ('-enrollment_date',)
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'semester')  # Removed course_offering
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__applicant',
            'semester__program',
            # Removed course_offering__course since it's not a field
        )

    def save_model(self, request, obj, form, change):
        if obj.status == 'enrolled' and not change:
            latest_enrollment = StudentSemesterEnrollment.objects.filter(
                student=obj.student,
                status='enrolled'
            ).order_by('-enrollment_date').first()
            if not latest_enrollment or obj.enrollment_date > latest_enrollment.enrollment_date:
                obj.student.current_semester = obj.semester
                obj.student.save()
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('student-autocomplete/', self.admin_site.admin_view(StudentAutocompleteView.as_view()), name='student_autocomplete'),
            path('semester-autocomplete/', self.admin_site.admin_view(SemesterAutocompleteView.as_view()), name='semester_autocomplete'),
            # Removed course-offering-autocomplete since it's not needed
        ]
        return urls

# Optionally register CourseEnrollment if you want to manage it in admin
@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student_semester_enrollment', 'course_offering', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date', 'course_offering__course', 'course_offering__semester')
    search_fields = ('student_semester_enrollment__student__applicant__full_name', 'course_offering__course__code')
    autocomplete_fields = ('student_semester_enrollment', 'course_offering')
    readonly_fields = ('enrollment_date',)

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