from django import forms
from .models import Teacher
from users.models import CustomUser

class TeacherForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Teacher
        fields = ['designation', 'contact_no', 'qualification', 'hire_date', 'is_active', 
                 'linkedin_url', 'twitter_url', 'personal_website', 'experience']
        widgets = {
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'personal_website': forms.URLInput(attrs={'class': 'form-control'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(
            teacher_profile__user__email=email if self.instance and self.instance.user else None
        ).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        if self.instance and self.instance.user:
            # Update existing user
            user = self.instance.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
            user.save()
        else:
            # Create new user
            user = CustomUser.objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            teacher.user = user

        if commit:
            teacher.save()
        return teacher

