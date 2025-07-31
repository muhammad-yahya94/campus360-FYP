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
from django.core.mail import send_mail
from django.conf import settings

class OfficePasswordResetView(auth_views.PasswordResetView):
    """
    View for handling password reset requests for office staff.
    """
    template_name = 'fee_management/password_reset.html'
    email_template_name = 'fee_management/password_reset_email.html'
    subject_template_name = 'fee_management/password_reset_subject.txt'
    success_url = reverse_lazy('fee_management:password_reset_done')
    
    def form_valid(self, form):
        """
        If the form is valid, send the password reset email.
        """
        email = form.cleaned_data['email']
        associated_users = CustomUser.objects.filter(email__iexact=email)
        
        if associated_users.exists():
            for user in associated_users:
                # Check if the user is an office staff member
                if hasattr(user, 'officestaff_profile'):
                    context = {
                        'email': user.email,
                        'domain': self.request.get_host(), 
                        'site_name': 'Campus360',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https' if self.request.is_secure() else 'http',
                    }
                    
                    subject = 'Password Reset Requested'
                    email_message = render_to_string(self.email_template_name, context)
                    
                    try:
                        send_mail(
                            subject=subject,
                            message=email_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        messages.error(self.request, f'Error sending email: {str(e)}')
                        return super().form_invalid(form)
                    
                    return super().form_valid(form)
        
        # If we get here, the email doesn't exist or the user is not an office staff
        messages.error(self.request, 'No office staff account exists with this email address.')
        return redirect('fee_management:office_login')

class OfficePasswordResetDoneView(auth_views.PasswordResetDoneView):
    """
    View displayed after a password reset email has been sent.
    """
    template_name = 'fee_management/password_reset_done.html'

class OfficePasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View for entering a new password after password reset.
    """
    template_name = 'fee_management/password_reset_confirm.html'
    success_url = reverse_lazy('fee_management:password_reset_complete')

class OfficePasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """
    View displayed after password has been successfully reset.
    """
    template_name = 'fee_management/password_reset_complete.html'
