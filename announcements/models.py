from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from autoslug import AutoSlugField

class News(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False)
    content = CKEditor5Field('Text', config_name='default')
    published_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False)
    description = CKEditor5Field('Text', config_name='default')
    event_start_date = models.DateTimeField(
        help_text="Select date YYYY-MM-DD (e.g., 2023-12-31) and time HH:MM (e.g., 14:30)"
    )
    event_end_date = models.DateTimeField(
        help_text="Select date YYYY-MM-DD (e.g., 2023-12-31) and time HH:MM (e.g., 14:30)"
    )
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateField(auto_now=False, auto_now_add=False)
    def __str__(self):
        return self.title
