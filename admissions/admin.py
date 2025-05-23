from django.contrib import admin
from .models import *
from .forms import AdmissionCycleForm
from django.utils.html import format_html
from users.models import CustomUser
from admissions.models import AcademicSession
from academics.models import Program, Department, Faculty


# ===== Academic Session Admin =====
@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_year', 'end_year', 'is_active')
    list_filter = ('is_active',)
    search_fields = ['name']


# ===== Admission procedure =====
@admin.register(AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    form = AdmissionCycleForm
    
    list_display = ('program', 'session', 'application_start', 'application_end', 'is_open')
    list_filter = ('session', 'program__department__faculty', 'program__department', 'program', 'is_open')
    search_fields = ['program__name', 'session__name']
    autocomplete_fields = ['program', 'session']



class AcademicQualificationInline(admin.TabularInline):
    model = AcademicQualification
    extra = 1
    fields = ('exam_passed', 'passing_year', 'marks_obtained', 'total_marks', 'division')
    readonly_fields = ('exam_passed', 'passing_year', 'marks_obtained', 'total_marks', 'division')

class ExtraCurricularActivityInline(admin.TabularInline):
    model = ExtraCurricularActivity
    extra = 1
    fields = ('activity', 'position', 'achievement', 'activity_year')
    readonly_fields = ('activity', 'position', 'achievement', 'activity_year')

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'program', 'status', 'applied_at')
    list_filter = ('status', 'program__department__faculty', 'program__department', 'program', 'applied_at')
    search_fields = ['full_name', 'cnic', 'program__name']
    autocomplete_fields = ['user', 'faculty', 'department', 'program']
    raw_id_fields = ['user']
    readonly_fields = ('applied_at', 'created_at')
    fieldsets = (
        ('Application Information', {
            'fields': ('user', 'faculty', 'department', 'program', 'status', 'applied_at')
        }),
        ('Personal Information', {
            'fields': (
                'applicant_photo', 'full_name', 'religion', 'caste', 
                'cnic', 'dob', 'contact_no', 'identification_mark'
            )
        }),
        ('Father/Guardian Information', {
            'fields': (
                'father_name', 'father_occupation', 'father_cnic',
                'monthly_income', 'relationship', 'permanent_address'
            )
        }),
        ('Declaration', {
            'fields': ('declaration',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    inlines = [AcademicQualificationInline, ExtraCurricularActivityInline]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def view_photo(self, obj):
        if obj.applicant_photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.applicant_photo.url)
        return "-"
    view_photo.short_description = 'Photo'

@admin.register(AcademicQualification)
class AcademicQualificationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'exam_passed', 'passing_year', 'marks_obtained', 'total_marks', 'division', 'board', 'view_certificate')
    list_filter = ('passing_year', 'board')
    search_fields = ('applicant__full_name', 'exam_passed', 'board')
    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant',)
        }),
        ('Qualification Details', {
            'fields': ('exam_passed', 'passing_year')
        }),
        ('Marks Information', {
            'fields': ('marks_obtained', 'total_marks', 'division')
        }),
        ('Additional Information', {
            'fields': ('board', 'subjects')
        }),
        ('Document', {
            'fields': ('certificate_file',),
            'description': 'Upload certificate or transcript (PDF, JPG, PNG)'
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('applicant',)
        return ()

    def save_model(self, request, obj, form, change):
        if 'certificate_file' in request.FILES:
            file = request.FILES['certificate_file']
            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                self.message_user(request, "Invalid file type. Please upload PDF, JPG, or PNG files only.", level='error')
                return
            # Validate file size (5MB limit)
            if file.size > 5 * 1024 * 1024:  # 5MB in bytes
                self.message_user(request, "File size too large. Maximum size is 5MB.", level='error')
                return
            obj.certificate_file = file
        super().save_model(request, obj, form, change)

    def view_certificate(self, obj):
        if obj.certificate_file:
            return format_html('<a href="{}" target="_blank">View Certificate</a>', obj.certificate_file.url)
        return "No certificate uploaded"
    view_certificate.short_description = 'Certificate'

@admin.register(ExtraCurricularActivity)
class ExtraCurricularActivityAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'activity', 'position', 'achievement', 'activity_year', 'view_certificate')
    list_filter = ('activity_year',)
    search_fields = ('applicant__full_name', 'activity', 'position', 'achievement')
    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant',)
        }),
        ('Activity Details', {
            'fields': ('activity', 'position', 'achievement', 'activity_year')
        }),
        ('Document', {
            'fields': ('certificate_file',),
            'description': 'Upload certificate or proof of participation/achievement (PDF, JPG, PNG)'
        })
    )

    def save_model(self, request, obj, form, change):
        if 'certificate_file' in request.FILES:
            file = request.FILES['certificate_file']
            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                self.message_user(request, "Invalid file type. Please upload PDF, JPG, or PNG files only.", level='error')
                return
            # Validate file size (5MB limit)
            if file.size > 5 * 1024 * 1024:  # 5MB in bytes
                self.message_user(request, "File size too large. Maximum size is 5MB.", level='error')
                return
            obj.certificate_file = file
        super().save_model(request, obj, form, change)

    def view_certificate(self, obj):
        if obj.certificate_file:
            return format_html('<a href="{}" target="_blank">View Certificate</a>', obj.certificate_file.url)
        return "No certificate uploaded"
    view_certificate.short_description = 'Certificate'