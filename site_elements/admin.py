from django.contrib import admin
from .models import Slider, Alumni, Gallery




# Register Models
@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ['title']

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('name', 'graduation_year', 'profession')
    list_filter = ('graduation_year',)
    search_fields = ['name', 'profession']

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_added')
    search_fields = ['title']
    date_hierarchy = 'date_added'

