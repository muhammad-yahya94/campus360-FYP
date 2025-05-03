from django.contrib import admin
from .models import *




# Register Models
@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ('name', 'graduation_year', 'profession')
    search_fields = ('name', 'profession')

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_added')
    list_per_page = 20

