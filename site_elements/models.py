from django.db import models
from users.models import CustomUser





class Slider(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='slider/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Alumni(models.Model):
    name = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField()
    profession = models.CharField(max_length=200)
    testimonial = models.TextField()
    image = models.ImageField(upload_to='alumni/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Gallery(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='gallery/')
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


