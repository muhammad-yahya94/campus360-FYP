from django.db import models

class Reminder(models.Model):
    name = models.CharField(max_length=100)
    remind_at = models.DateTimeField()

    def __str__(self):
        return f"{self.name} at {self.remind_at}"
