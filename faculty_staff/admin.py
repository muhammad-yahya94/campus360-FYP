from django.contrib import admin
from .models import Teacher, Office, OfficeStaff, DESIGNATION_CHOICES
from users.models import CustomUser
from academics.models import Department

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'contact_no', 'hire_date', 'is_active', 'linkedin_url', 'twitter_url', 'personal_website')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'contact_no', 'department__name', 'linkedin_url', 'twitter_url', 'personal_website']
    autocomplete_fields = ['user', 'department']

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'contact_no')
        }),
        ('Professional Information', {
            'fields': ('department', 'designation', 'qualification', 'experience')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'is_active'),
            'classes': ('collapse')
        }),
        ('Social Media and Links', {
            'fields': ('linkedin_url', 'twitter_url', 'personal_website'),
            'classes': ('collapse')
        }),
    )

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_email', 'contact_phone')
    search_fields = ['name', 'location', 'contact_email', 'contact_phone', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(OfficeStaff)
class OfficeStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'office', 'position', 'contact_no')
    list_filter = ('office', 'position')
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'office__name', 'position']
    autocomplete_fields = ['user', 'office']