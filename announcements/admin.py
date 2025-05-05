from django.contrib import admin
from .models import *
from django_ckeditor_5.widgets import CKEditor5Widget



@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    
    list_display = ('title','slug', 'published_date', 'is_published')
    list_filter = ('is_published',)
    
    # CKEditor 5 integration
    formfield_overrides = {
        models.TextField: {
            'widget': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"},
                config_name="extends"  
            )
        }
    }



@admin.register(Event)
class EventAdmin(admin.ModelAdmin):


    list_display = ('title','slug', 'event_start_date', 'event_end_date', 'location')
    search_fields = ('title', 'location')

    formfield_overrides = {
        models.TextField: {
            'widget': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"},
                config_name="extends"
            )
        }
    }

