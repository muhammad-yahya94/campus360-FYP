from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from faculty_staff.models import OfficeStaff

User = get_user_model()

class OfficerUpdateForm(forms.ModelForm):
    """Form for updating officer profile information."""
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/*',
            'id': 'profile_picture'
        }),
        help_text='JPG, GIF or PNG. Max size 2MB'
    )
    contact_no = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '+92 300 1234567'
        })
    )

    class Meta:
        model = User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'email',
            'info',
            'contact_no'  # This will be saved to the OfficeStaff model
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'info': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full h-24',
                'placeholder': 'Tell us a bit about yourself...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.officer_profile = None
        if 'instance' in kwargs and hasattr(kwargs['instance'], 'officestaff_profile'):
            self.officer_profile = kwargs['instance'].officestaff_profile
            initial = kwargs.get('initial', {})
            initial['contact_no'] = self.officer_profile.contact_no or ''
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture and hasattr(profile_picture, 'size') and profile_picture.size > 2 * 1024 * 1024:
            raise ValidationError("Image file too large (max 2MB).")
        return profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Update or create officer profile
            if not hasattr(user, 'officestaff_profile'):
                self.officer_profile = OfficeStaff.objects.create(
                    user=user,
                    contact_no=self.cleaned_data.get('contact_no', '')
                )
            else:
                self.officer_profile.contact_no = self.cleaned_data.get('contact_no', '')
                self.officer_profile.save()
                
        return user


class OfficerPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Tailwind styling."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'Current password',
            'autocomplete': 'current-password',
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        })

from .models import OfficeToHODNotification

class OfficeToHODNotificationForm(forms.ModelForm):
    class Meta:
        model = OfficeToHODNotification
        fields = ['title', 'message', 'attached_file']