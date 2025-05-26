from django.contrib import admin
from django import forms
from .models import (
    Course,
    CourseOffering,
    StudyMaterial,
    Assignment,
    AssignmentSubmission,
    Notice,
    ExamResult,
)
from academics.models import Program, Department, Semester   
from faculty_staff.models import Teacher
from students.models import Student
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.urls import path
from django.db.models import Q

# ===== Custom Forms =====

class CourseOfferingAdminForm(forms.ModelForm):
    class Meta:
        model = CourseOffering
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['course', 'teacher', 'department', 'program', 'semester', 'academic_session']:
            self.fields[field].widget.can_add_related = False
            # Optionally allow change and delete if needed
            # self.fields[field].widget.can_change_related = False
            # self.fields[field].widget.can_delete_related = False

class AssignmentSubmissionAdminForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Remove the extra colon
        for field in ['assignment', 'student', 'graded_by']:
            self.fields[field].widget.can_add_related = False

class NoticeAdminForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Remove the extra colon
        for field in ['created_by']:
            self.fields[field].widget.can_add_related = False

class ExamResultAdminForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Remove the extra colon
        for field in ['course_offering', 'student', 'graded_by']:
            self.fields[field].widget.can_add_related = False

# ===== Custom Autocomplete Views =====

class CourseAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Course.objects.all()
        if self.q:
            qs = qs.filter(Q(code__icontains=self.q) | Q(name__icontains=self.q))
        return qs.distinct()[:20]

class TeacherAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Teacher.objects.all()
        if self.q:
            qs = qs.filter(Q(user__first_name__icontains=self.q) | Q(user__last_name__icontains=self.q))
        return qs.distinct()[:20]

class DepartmentAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Department.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
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

class AcademicSessionAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        from admissions.models import AcademicSession
        qs = AcademicSession.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()[:20]

class CourseOfferingAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = CourseOffering.objects.all()
        if self.q:
            qs = qs.filter(Q(course__code__icontains=self.q) | Q(course__name__icontains=self.q) | Q(semester__name__icontains=self.q))
        return qs.distinct()[:20]

class AssignmentAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Assignment.objects.all()
        if self.q:
            qs = qs.filter(Q(title__icontains=self.q) | Q(course_offering__course__name__icontains=self.q))
        return qs.distinct()[:20]

class StudentAutocompleteView(AutocompleteJsonView):
    def get_queryset(self):
        qs = Student.objects.all()
        if self.q:
            qs = qs.filter(applicant__full_name__icontains=self.q)
        return qs.distinct()[:20]

# ===== Admin Classes =====

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    filter_horizontal = ('prerequisites',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'credits', 'is_active')
        }),
        ('Course Details', {
            'fields': ('description', 'prerequisites')
        }),
    )

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    form = CourseOfferingAdminForm
    list_display = ('course', 'semester', 'teacher', 'offering_type', 'is_active')
    list_filter = ('is_active', 'semester__program', 'offering_type', 'department')
    search_fields = ('course__code', 'course__name', 'teacher__user__first_name', 'semester__name')
    ordering = ('semester__program', 'semester__number', 'course__code')
    autocomplete_fields = ('course', 'teacher', 'department', 'program', 'semester', 'academic_session')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'teacher', 'offering_type')
        }),
        ('Program & Department', {
            'fields': ('program', 'department')
        }),
        ('Semester & Session', {
            'fields': ('semester', 'academic_session')
        }),
        ('Enrollment Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'teacher', 'department', 'program', 'semester', 'academic_session'
        )

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('course-autocomplete/', self.admin_site.admin_view(CourseAutocompleteView.as_view()), name='course_autocomplete'),
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
            path('department-autocomplete/', self.admin_site.admin_view(DepartmentAutocompleteView.as_view()), name='department_autocomplete'),
            path('program-autocomplete/', self.admin_site.admin_view(ProgramAutocompleteView.as_view()), name='program_autocomplete'),
            path('semester-autocomplete/', self.admin_site.admin_view(SemesterAutocompleteView.as_view()), name='semester_autocomplete'),
            path('academicsession-autocomplete/', self.admin_site.admin_view(AcademicSessionAutocompleteView.as_view()), name='academicsession_autocomplete'),
        ]
        return urls

@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'uploaded_by', 'uploaded_at', 'is_active')
    list_filter = ('is_active', 'course_offering__semester__program', 'uploaded_by')
    search_fields = ('title', 'description', 'course_offering__course__name', 'uploaded_by__user__first_name')
    autocomplete_fields = ('course_offering', 'uploaded_by')
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Material Information', {
            'fields': ('course_offering', 'title', 'description', 'file')
        }),
        ('Upload Details', {
            'fields': ('uploaded_by', 'uploaded_at', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course_offering', 'uploaded_by')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('courseoffering-autocomplete/', self.admin_site.admin_view(CourseOfferingAutocompleteView.as_view()), name='courseoffering_autocomplete'),
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
        ]
        return urls

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_offering', 'created_by', 'due_date', 'total_marks', 'is_active')
    list_filter = ('is_active', 'course_offering__semester__program', 'created_by')
    search_fields = ('title', 'description', 'course_offering__course__name', 'created_by__user__first_name')
    autocomplete_fields = ('course_offering', 'created_by')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('course_offering', 'title', 'description', 'file', 'due_date', 'total_marks')
        }),
        ('Creation Details', {
            'fields': ('created_by', 'created_at', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course_offering', 'created_by')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('courseoffering-autocomplete/', self.admin_site.admin_view(CourseOfferingAutocompleteView.as_view()), name='courseoffering_autocomplete'),
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
        ]
        return urls

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    form = AssignmentSubmissionAdminForm
    list_display = ('assignment', 'student', 'submitted_at', 'marks_obtained', 'graded_by', 'graded_at')
    list_filter = ('assignment__course_offering__semester__program', 'student', 'graded_by')
    search_fields = ('student__applicant__full_name', 'assignment__title', 'graded_by__user__first_name')
    autocomplete_fields = ('assignment', 'student', 'graded_by')
    readonly_fields = ('submitted_at', 'graded_at')
    
    fieldsets = (
        ('Submission Details', {
            'fields': ('assignment', 'student', 'file', 'submitted_at')
        }),
        ('Grading Information', {
            'fields': ('marks_obtained', 'feedback', 'graded_by', 'graded_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assignment', 'student', 'graded_by')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('assignment-autocomplete/', self.admin_site.admin_view(AssignmentAutocompleteView.as_view()), name='assignment_autocomplete'),
            path('student-autocomplete/', self.admin_site.admin_view(StudentAutocompleteView.as_view()), name='student_autocomplete'),
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
        ]
        return urls

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    form = NoticeAdminForm
    list_display = ('title', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_by')
    search_fields = ('title', 'content', 'created_by__user__first_name')
    autocomplete_fields = ('created_by',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Notice Information', {
            'fields': ('title', 'content')
        }),
        ('Creation Details', {
            'fields': ('created_by', 'created_at', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
        ]
        return urls

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    form = ExamResultAdminForm
    list_display = ('course_offering', 'student', 'exam_type', 'total_marks', 'marks_obtained', 'graded_by', 'graded_at')
    list_filter = ('exam_type', 'course_offering__semester__program', 'student', 'graded_by')
    search_fields = ('student__applicant__full_name', 'course_offering__course__name', 'graded_by__user__first_name')
    autocomplete_fields = ('course_offering', 'student', 'graded_by')
    readonly_fields = ('graded_at',)
    
    fieldsets = (
        ('Result Information', {
            'fields': ('course_offering', 'student', 'exam_type', 'total_marks', 'marks_obtained', 'remarks')
        }),
        ('Grading Details', {
            'fields': ('graded_by', 'graded_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course_offering', 'student', 'graded_by')

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('courseoffering-autocomplete/', self.admin_site.admin_view(CourseOfferingAutocompleteView.as_view()), name='courseoffering_autocomplete'),
            path('student-autocomplete/', self.admin_site.admin_view(StudentAutocompleteView.as_view()), name='student_autocomplete'),
            path('teacher-autocomplete/', self.admin_site.admin_view(TeacherAutocompleteView.as_view()), name='teacher_autocomplete'),
        ]
        return urls
    
