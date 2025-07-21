import random
import string
from django.contrib import admin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Teacher, Office, OfficeStaff, TeacherDetails

CustomUser = get_user_model()

def send_welcome_email(user, password, template='faculty_staff/account_created_email.html'):
    """Helper function to send welcome email with credentials"""
    subject = 'Your Campus360 Account Has Been Created'
    html_message = render_to_string(template, {
        'first_name': user.first_name,
        'email': user.email,
        'password': password,
    })
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Failed to send email to {user.email}: {str(e)}')
        return False

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'is_active')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    list_editable = ('is_active',)
    
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        
        if is_new and not obj.user_id:
            # Generate random 8-digit password
            password = ''.join(random.choices(string.digits, k=8))
            
            # Create user if it doesn't exist
            user = CustomUser.objects.create(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name,
            )
            user.set_password(password)
            user.save()
            obj.user = user
            
            # Send welcome email
            # login_url = request.build_absolute_uri('/faculty/login/')
            send_welcome_email(user, password)
        
        super().save_model(request, obj, form, change)

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(OfficeStaff)
class OfficeStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'office', 'position', 'contact_no')
    list_filter = ('office',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        
        if is_new and not obj.user_id:
            # Generate random 8-digit password
            password = ''.join(random.choices(string.digits, k=8))
            
            # Create user if it doesn't exist
            user = CustomUser.objects.create(
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name,
            )
            user.set_password(password)
            user.save()
            obj.user = user
            
            # Send welcome email with office login URL
            # login_url = request.build_absolute_uri('/office/login/')  # Adjust URL as needed
            send_welcome_email(user, password)
        
        super().save_model(request, obj, form, change)