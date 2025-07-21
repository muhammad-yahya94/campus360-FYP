from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

class StudentPasswordResetView(auth_views.PasswordResetView):
    """
    View for handling password reset requests for students.
    """
    template_name = 'students/password_reset.html'
    email_template_name = 'students/password_reset_email.html'
    subject_template_name = 'students/password_reset_subject.txt'
    success_url = reverse_lazy('students:password_reset_done')
    
    def form_valid(self, form):
        """
        If the form is valid, send the password reset email.
        """
        email = form.cleaned_data['email']
        associated_users = User.objects.filter(email=email)
        
        if associated_users.exists():
            for user in associated_users:
                # Check if the user is a student
                if hasattr(user, 'student'):
                    context = {
                        'email': user.email,
                        'domain': self.request.META['HTTP_HOST'],
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
        
        # If we get here, the email doesn't exist or the user is not a student
        messages.error(self.request, 'No student account exists with this email address.')
        return redirect('students:login')

class StudentPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """
    View displayed after a password reset email has been sent.
    """
    template_name = 'students/password_reset_done.html'

class StudentPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View for entering a new password after password reset.
    """
    template_name = 'students/password_reset_confirm.html'
    success_url = reverse_lazy('students:password_reset_complete')

class StudentPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """
    View displayed after password has been successfully reset.
    """
    template_name = 'students/password_reset_complete.html'
