from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'designation', 'is_active', 'hire_date')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'qualification', 'contact_no')
    raw_id_fields = ('user',)  # Better for performance than dropdown with many users
    date_hierarchy = 'hire_date'
    ordering = ('-hire_date',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'contact_no')
        }),
        ('Professional Information', {
            'fields': ('department', 'designation', 'qualification')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'is_active'),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'department', 'department__faculty')