from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from autoslug import AutoSlugField

class News(models.Model):
    title = models.CharField(max_length=200, help_text="Enter the title of the news article.")
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False, help_text="A unique, web-friendly identifier for the news article. Automatically generated from the title.")
    content = CKEditor5Field('Text', config_name='default', help_text="Enter the main content of the news article.")
    published_date = models.DateTimeField(auto_now_add=True, help_text="The date and time the news article was published.")
    is_published = models.BooleanField(default=True, help_text="Check this to make the news article visible on the website.")
    
    class Meta:
        verbose_name = 'News'
        verbose_name_plural = 'News'
    
    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=200, help_text="Enter the title of the event.")
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False, help_text="A unique, web-friendly identifier for the event. Automatically generated from the title.")
    description = CKEditor5Field('Text', config_name='default', help_text="Provide a detailed description of the event.")
    event_start_date = models.DateTimeField(
        help_text="Select the date and time when the event starts (YYYY-MM-DD HH:MM)."
    )
    event_end_date = models.DateTimeField(
        help_text="Select the date and time when the event ends (YYYY-MM-DD HH:MM)."
    )
    location = models.CharField(max_length=200, help_text="Enter the location where the event will take place.")
    image = models.ImageField(upload_to='events/', blank=True, null=True, help_text="Upload an image related to the event (optional).")
    created_at = models.DateField(auto_now=False, auto_now_add=False, help_text="The date when this event record was created.")
    
    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
    
    def __str__(self):
        return self.title
