import logging
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm
from users.models import CustomUser
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class FacultyStaffPasswordResetView(auth_views.PasswordResetView):
    """
    View for handling password reset requests for faculty/staff.
    """
    template_name = 'faculty_staff/password_reset.html'
    email_template_name = 'faculty_staff/password_reset_email.html'
    subject_template_name = 'faculty_staff/password_reset_subject.txt'
    success_url = reverse_lazy('faculty_staff:password_reset_done')
    
    def form_valid(self, form):
        """
        If the form is valid, send the password reset email.
        """
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")
        
        try:
            associated_users = CustomUser.objects.filter(email__iexact=email)
            logger.info(f"Found {associated_users.count()} users with email: {email}")
            
            if associated_users.exists():
                for user in associated_users:
                    # Check if the user is a faculty/staff member
                    if hasattr(user, 'teacher'):
                        logger.info(f"User {user.email} is a teacher, sending reset email")
                        
                        # Generate the token and UID
                        token = default_token_generator.make_token(user)
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        
                        context = {
                            'email': user.email,
                            'domain': self.request.get_host(),  # Use get_host() instead of META['HTTP_HOST']
                            'site_name': 'Campus360',
                            'uid': uid,
                            'user': user,
                            'token': token,
                            'protocol': 'https' if self.request.is_secure() else 'http',
                        }
                        
                        # Log the context for debugging
                        logger.debug(f"Email context: {context}")
                        
                        # Render email content
                        subject = 'Password Reset Requested'
                        email_message = render_to_string(self.email_template_name, context)
                        
                        try:
                            # Create plain text version of the email
                            text_content = strip_tags(email_message)
                            
                            # Create email message with both HTML and plain text versions
                            email = EmailMultiAlternatives(
                                subject=subject,
                                body=text_content,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[user.email],
                            )
                            email.attach_alternative(email_message, "text/html")
                            email.send(fail_silently=False)
                            logger.info(f"Password reset email sent to {user.email}")
                            
                            # Log success but don't reveal it to the user (security)
                            messages.success(
                                self.request,
                                'If an account exists with this email, you will receive a password reset link.'
                            )
                            return super().form_valid(form)
                            
                        except BadHeaderError as e:
                            logger.error(f"Bad header in email: {str(e)}")
                            messages.error(self.request, 'Invalid header found in email.')
                            return super().form_invalid(form)
                            
                        except Exception as e:
                            logger.error(f"Error sending email to {user.email}: {str(e)}", exc_info=True)
                            messages.error(
                                self.request,
                                'An error occurred while sending the password reset email. Please try again later.'
                            )
                            return super().form_invalid(form)
            
            # If we get here, either the email doesn't exist or the user is not faculty/staff
            # But we don't reveal this information for security reasons
            logger.warning(f"No faculty/staff account found for email: {email}")
            
        except Exception as e:
            logger.error(f"Unexpected error in password reset: {str(e)}", exc_info=True)
            
        # Generic success message (don't reveal if email exists or not for security)
        messages.success(
            self.request,
            'If an account exists with this email, you will receive a password reset link.'
        )
        return super().form_valid(form)

class FacultyStaffPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """
    View displayed after a password reset email has been sent.
    """
    template_name = 'faculty_staff/password_reset_done.html'

class FacultyStaffPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View for entering a new password after password reset.
    """
    template_name = 'faculty_staff/password_reset_confirm.html'
    success_url = reverse_lazy('faculty_staff:password_reset_complete')

class FacultyStaffPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """
    View displayed after password has been successfully reset.
    """
    template_name = 'faculty_staff/password_reset_complete.html'
