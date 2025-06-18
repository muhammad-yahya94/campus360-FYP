from background_task import background
from .models import Reminder

@background(schedule=0)
def notify_user(reminder_id):
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        print(f"⏰ Reminder Triggered for: {reminder.name} at {reminder.remind_at}")
        # You can add email sending here if needed
    except Reminder.DoesNotExist:
        print("Reminder not found.")
