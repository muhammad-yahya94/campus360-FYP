from django import forms
from .models import AdmissionCycle

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
        
        
        
   