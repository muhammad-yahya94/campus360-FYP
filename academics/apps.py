from django.apps import AppConfig

class AcademicsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academics'
    icon = 'fas fa-building'  # FontAwesome icon for the app
    divider_title = "Academic Modules"  # Title of the section divider in the sidebar
    hide = False  # Set to True to hide the app from the sidebar menu
