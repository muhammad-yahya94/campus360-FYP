from django.apps import AppConfig

class AnnouncementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'announcements'
    icon = 'fas fa-file-alt'  # FontAwesome icon for the app
    divider_title = "Announcements Section"  # Title of the section divider in the sidebar
    priority = 3  # Determines the order of the app in the sidebar (higher values appear first)
    hide = False  # Set to True to hide the app from the sidebar menu
