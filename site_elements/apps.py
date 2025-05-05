from django.apps import AppConfig

class SiteElementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_elements'
    icon = 'fas fa-images'  # FontAwesome icon for the app
    divider_title = "Site Elements"  # Title of the section divider in the sidebar
    priority = 4  # Determines the order of the app in the sidebar (higher values appear first)
    hide = False  # Set to True to hide the app from the sidebar menu
