from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    event_start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }
        ),
        input_formats=['%Y-%m-%dT%H:%M']  # format for datetime-local
    )
    event_end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Event
        fields = '__all__'
