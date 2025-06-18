from django.urls import path
from .views import create_reminder

urlpatterns = [
    path('', create_reminder, name='create_reminder'),
]
