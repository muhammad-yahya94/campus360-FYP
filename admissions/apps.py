from django.apps import AppConfig

class AdmissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admissions'
    icon = 'fas fa-user-graduate'  # FontAwesome icon for the app
    divider_title = "Admissions Section"  # Title of the section divider in the sidebar
    priority = 2  # Determines the order of the app in the sidebar (higher values appear first)
    hide = False  # Set to True to hide the app from the sidebar menu
