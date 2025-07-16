from django import forms
from .models import AdmissionCycle, Applicant, AcademicQualification, ExtraCurricularActivity

class AdmissionCycleForm(forms.ModelForm):
    application_start = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }
        ),
        input_formats=['%Y-%m-%dT%H:%M']  # format for datetime-local
    )
    application_end = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = AdmissionCycle
        fields = '__all__'

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = '__all__'
        exclude = ('user', 'status', 'rejection_reason')

class AcademicQualificationForm(forms.ModelForm):
    class Meta:
        model = AcademicQualification
        fields = '__all__'
        exclude = ('applicant',)

class ExtraCurricularActivityForm(forms.ModelForm):
    class Meta:
        model = ExtraCurricularActivity
        fields = '__all__'
        exclude = ('applicant',)