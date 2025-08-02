import random
import string
import logging
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Teacher, Office, OfficeStaff, TeacherDetails, ExamDateSheet, DepartmentFund

# Set up logging
logger = logging.getLogger(__name__)

CustomUser = get_user_model()

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'department', 'is_active')
    list_filter = ('is_active', 'designation', 'department')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

    def save_model(self, request, obj, form, change):
        # Save the teacher instance first
        super().save_model(request, obj, form, change)

        # Check if this is a new teacher (not an update)
        if not change:
            # Generate a random password for the user if needed
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            obj.user.set_password(password)
            obj.user.save()

            # Prepare the email content
            subject = "Welcome to Campus360 - Your Faculty Account"
            context = {
                'first_name': obj.user.first_name,
                'email': obj.user.email,
                'password': password,
                # 'login_url': 'https://your-site.com/login',  # Update with your actual login URL
            }
            message = render_to_string('faculty_staff/account_created_email.html', context)

            # Send the email
            try:
                obj.user.email_user(
                    subject=subject,
                    message='',  # Plain text message is empty since we're using HTML
                    from_email='princeyahya052@gmail.com',  # Update with your sender email
                    html_message=message
                )
                print(f"Email sent to {obj.user.email}")
            except Exception as e:
                print(f"Failed to send email to {obj.user.email}: {str(e)}")

@admin.register(TeacherDetails)
class TeacherDetailsAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_designation', 'get_qualification', 'get_contact_no', 'get_hire_date', 'get_experience')
    list_filter = ('teacher__designation', 'teacher__hire_date', 'teacher__department')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'teacher__user__email', 'teacher__qualification', 'teacher__contact_no')
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('teacher',)
        }),
        ('Employment Details', {
            'fields': ('employment_type', 'salary_per_lecture', 'fixed_salary', 'status')
        }),
        ('System Information', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name() or f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
        return 'No Teacher'
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'teacher__user__first_name'
    
    def get_designation(self, obj):
        if obj.teacher:
            return obj.teacher.get_designation_display()
        return 'No Designation'
    get_designation.short_description = 'Designation'
    get_designation.admin_order_field = 'teacher__designation'
    
    def get_qualification(self, obj):
        if obj.teacher:
            return obj.teacher.qualification
        return 'No Qualification'
    get_qualification.short_description = 'Qualification'
    get_qualification.admin_order_field = 'teacher__qualification'
    
    def get_contact_no(self, obj):
        if obj.teacher:
            return obj.teacher.contact_no
        return 'No Contact'
    get_contact_no.short_description = 'Contact No'
    get_contact_no.admin_order_field = 'teacher__contact_no'
    
    def get_hire_date(self, obj):
        if obj.teacher:
            return obj.teacher.hire_date
        return 'No Hire Date'
    get_hire_date.short_description = 'Hire Date'
    get_hire_date.admin_order_field = 'teacher__hire_date'
    
    def get_experience(self, obj):
        if obj.teacher:
            return obj.teacher.experience or 'No Experience Listed'
        return 'No Experience'
    get_experience.short_description = 'Experience'
    get_experience.admin_order_field = 'teacher__experience'

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(OfficeStaff)
class OfficeStaffAdmin(admin.ModelAdmin):
    list_display = ('get_email', 'office', 'position', 'contact_no')
    list_filter = ('office',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def get_email(self, obj):
        return obj.user.email if obj.user else 'No user'
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Remove fields that are now in CustomUser
        for field in ['email', 'first_name', 'last_name']:
            if field in form.base_fields:
                del form.base_fields[field]
        return form
    
    def save_model(self, request, obj, form, change):
        # Save the office staff instance first
        super().save_model(request, obj, form, change)

        # Check if this is a new office staff (not an update)
        if not change:
            # Validate that the user has a valid email
            if not obj.user or not obj.user.email:
                print(f"No valid email for user associated with OfficeStaff {obj}")
                logger.error(f"No valid email for user associated with OfficeStaff {obj}")
                messages.error(request, "Cannot send email: No valid email address for the user.")
                return

            # Generate a random password for the user if needed
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            obj.user.set_password(password)
            obj.user.save()

            # Prepare the email content
            subject = "Welcome to Campus360 - Your Officer Account"
            context = {
                'first_name': obj.user.first_name,
                'email': obj.user.email,
                'password': password,
                # 'login_url': 'https://your-site.com/login',  # Update with your actual login URL
            }
            try:  
                template_path = 'faculty_staff/account_created_email.html'
                print(f"Looking for template at: {template_path}")
                message = render_to_string(template_path, context)
                print("Template rendered successfully")
            except Exception as e:
                print(f"Failed to render email template for {obj.user.email}: {str(e)}")
                logger.error(f"Failed to render email template for {obj.user.email}: {str(e)}")
                messages.error(request, f"Failed to render email template: {str(e)}")
                return

            # Send the email
            try:
                obj.user.email_user(
                    subject=subject,
                    message='',  # Plain text message is empty since we're using HTML
                    from_email='princeyahya052@gmail.com',  # Update with your sender email
                    html_message=message
                )
                print(f"Email sent to {obj.user.email}")
                logger.info(f"Email sent to {obj.user.email}")
                messages.success(request, f"Email sent to {obj.user.email}")
            except Exception as e:
                print(f"Failed to send email to {obj.user.email}: {str(e)}")
                logger.error(f"Failed to send email to {obj.user.email}: {str(e)}")
                messages.error(request, f"Failed to send email to {obj.user.email}: {str(e)}")


@admin.register(DepartmentFund)
class DepartmentFundAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'department', 'fundtype', 'amount', 'due_date', 'is_active')
    list_filter = ('is_active', 'department', 'fundtype', 'created_at')
    search_fields = ('description', 'fundtype', 'department__name')
    filter_horizontal = ('academic_sessions', 'programs', 'semesters')
    date_hierarchy = 'created_at'
    list_editable = ('is_active', 'amount', 'due_date')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('hod', 'department', 'fundtype', 'amount', 'description')
        }),
        ('Date Information', {
            'fields': ('due_date', 'created_at')
        }),
        ('Associations', {
            'fields': ('academic_sessions', 'programs', 'semesters')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    # Custom method to handle the many-to-many relationship with students
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'students':
            kwargs['queryset'] = db_field.remote_field.model._default_manager.all()
            return db_field.formfield(**kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(ExamDateSheet)
class ExamDateSheetAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'exam_type', 'exam_date', 'start_time', 'end_time', 'exam_center', 'academic_session', 'semester', 'program')
    list_filter = ('exam_type', 'academic_session', 'semester', 'program')
    search_fields = ('course_offering__course__code', 'course_offering__course__name', 'exam_center', 'exam_type')
    list_editable = ('exam_date', 'start_time', 'end_time', 'exam_center')
    ordering = ('exam_date', 'start_time')
    date_hierarchy = 'exam_date'

    def get_readonly_fields(self, request, obj=None):
        # Make created_at and updated_at readonly in the admin
        return ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # Ensure clean method is called to enforce validation
        obj.clean()
        super().save_model(request, obj, form, change)