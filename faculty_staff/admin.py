from django.contrib import admin
from .models import Teacher, Office, OfficeStaff

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'is_active')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    list_editable = ('is_active',)

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(OfficeStaff)
class OfficeStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'office', 'position', 'contact_no')
    list_filter = ('office',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')