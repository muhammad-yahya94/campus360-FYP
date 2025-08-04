from django import forms
from .models import OfficeToHODNotification

class OfficeToHODNotificationForm(forms.ModelForm):
    class Meta:
        model = OfficeToHODNotification
        fields = ['title', 'message', 'attached_file']