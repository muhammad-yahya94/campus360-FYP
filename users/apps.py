from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    icon = 'fas fa-users'  # FontAwesome icon for the app (optional)
    divider_title = "User Management"  # Title of the section divider in the sidebar (optional)
    priority = 5  # Determines the order of the app in the sidebar (higher values appear first, optional)
    hide = False  # Set to True to hide the app from the sidebar menu (optional)
