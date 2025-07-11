from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from users.models import CustomUser
from .models import Course, YearSession, Semester




class YearSessionForm(forms.ModelForm):
    """Form for creating and updating YearSession instances."""
    class Meta:
        model = YearSession
        fields = ['start_year', 'end_year', 'department']
        widgets = {
            'start_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Start Year',
                'min': 2000,
                'max': 2100
            }),
            'end_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'End Year',
                'min': 2000,
                'max': 2100
            }),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_year = cleaned_data.get('start_year')
        end_year = cleaned_data.get('end_year')
        
        if start_year and end_year and end_year <= start_year:
            raise ValidationError("End year must be greater than start year.")
        
        return cleaned_data


class SemesterForm(forms.ModelForm):
    """Form for creating and updating Semester instances."""
    class Meta:
        model = Semester
        fields = ['name', 'number', 'year_session']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Semester Name'
            }),
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Semester Number',
                'min': 1,
                'max': 12
            }),
            'year_session': forms.Select(attrs={'class': 'form-control'}),
        }


class CourseAndExcelUploadForm(forms.Form):
    """Form for uploading course data and Excel files with student results."""
    course_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Course Title'
        })
    )
    
    course_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Course Code'
        })
    )
    
    credit_hour = forms.ChoiceField(
        choices=Course.CREDIT_HOUR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=3
    )
    
    opt = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        label="Optional Course",
        help_text="Check if this is an optional course"
    )
    
    lab_work = forms.ChoiceField(
        choices=Course.LAB_WORK_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=0,
        help_text="Select lab work hours if applicable"
    )
    
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': '.xlsx, .xls'
        }),
        help_text="Upload Excel file with student results (.xlsx or .xls)",
        required=False
    )
    
    session = forms.ModelChoiceField(
        queryset=YearSession.objects.all().order_by('-start_year'),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'hx-get': '/manual/get_semesters/',
            'hx-trigger': 'change',
            'hx-target': '#id_semester'
        }),
        help_text="Select academic session"
    )
    
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.none(),  # Will be populated via AJAX
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_semester'
        }),
        help_text="Select semester",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have a session_id in the GET parameters, update the semester queryset
        session_id = self.data.get('session') or self.initial.get('session')
        if session_id:
            try:
                self.fields['semester'].queryset = Semester.objects.filter(
                    year_session_id=session_id
                ).order_by('number')
            except (ValueError, TypeError):
                self.fields['semester'].queryset = Semester.objects.none()
        else:
            self.fields['semester'].queryset = Semester.objects.none()

