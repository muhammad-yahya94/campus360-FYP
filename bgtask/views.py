from django.shortcuts import render, redirect
from .forms import ReminderForm
from .tasks import notify_user
from django.utils import timezone

def create_reminder(request):
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save()
            notify_user(reminder.id, schedule={'run_at': reminder.remind_at})
            print('run successfully......')
            # return render(request, 'reminder/success.html', {'reminder': reminder})
    else:
        form = ReminderForm()
    return render(request, 'form.html', {'form': form})

