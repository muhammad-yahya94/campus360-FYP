from django.db import models
from users.models import CustomUser


class Slider(models.Model):
    title = models.CharField(max_length=200, help_text="Enter a title for the slider image.")
    image = models.ImageField(upload_to='slider/', help_text="Upload the image for the slider.")
    is_active = models.BooleanField(default=True, help_text="Check to make this slider image active on the website.")
    
    def __str__(self):
        return self.title

class Alumni(models.Model):
    name = models.CharField(max_length=100, help_text="Enter the name of the alumnus/alumna.")
    graduation_year = models.PositiveIntegerField(help_text="Enter the year the alumnus/alumna graduated.")
    profession = models.CharField(max_length=200, help_text="Enter the current profession or occupation of the alumnus/alumna.")
    testimonial = models.TextField(help_text="Enter the testimonial or quote from the alumnus/alumna.")
    image = models.ImageField(upload_to='alumni/', blank=True, null=True, help_text="Upload a picture of the alumnus/alumna (optional).")
    
    def __str__(self):
        return self.name

class Gallery(models.Model):
    title = models.CharField(max_length=200, help_text="Enter a title for the gallery image.")
    image = models.ImageField(upload_to='gallery/', help_text="Upload the image for the gallery.")
    date_added = models.DateTimeField(auto_now_add=True, help_text="The date and time the image was added to the gallery.")
    
    def __str__(self):
        return self.title


