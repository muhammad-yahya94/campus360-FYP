from django.contrib import admin
from .models import *
from .forms import AdmissionCycleForm
from django.utils.html import format_html


# ===== Academic Session Admin =====
@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    search_fields = ('name',)


# ===== Admission procedure =====
@admin.register(AdmissionCycle)
class AdmissionCycle(admin.ModelAdmin):
    form = AdmissionCycleForm
    
    list_display = ('program', 'session', 'application_start', 'application_end', 'is_open')
    list_filter = ('program','is_open')
    search_fields = ('program__title',)



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
    list_display = ('full_name', 'user_email', 'program', 'status', 'applied_at', 'view_photo')
    list_filter = ('status', 'program', 'department', 'faculty', 'applied_at')
    search_fields = ('full_name', 'user__email', 'cnic', 'contact_no')
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

# @admin.register(AcademicQualification)
# class AcademicQualificationAdmin(admin.ModelAdmin):
#     list_display = ('applicant_name', 'level', 'exam_passed', 'passing_year', 'board')
#     list_filter = ('level', 'board')
#     search_fields = ('applicant__full_name', 'exam_passed', 'roll_no')
    
#     def applicant_name(self, obj):
#         return obj.applicant.full_name
#     applicant_name.short_description = 'Applicant'
#     applicant_name.admin_order_field = 'applicant__full_name'

# @admin.register(ExtraCurricularActivity)
# class ExtraCurricularActivityAdmin(admin.ModelAdmin):
#     list_display = ('applicant_name', 'activity', 'position', 'achievement', 'activity_year')
#     search_fields = ('applicant__full_name', 'activity', 'achievement')
    
#     def applicant_name(self, obj):
#         return obj.applicant.full_name
#     applicant_name.short_description = 'Applicant'
#     applicant_name.admin_order_field = 'applicant__full_name'