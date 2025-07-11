from django.urls import path
from .views import *

urlpatterns = [
    path('UploadRresult/', upload_result, name='upload_result'),
    path('get-semesters/', get_semesters, name='get_semesters'),
    path('' , Result , name="Result"),
]

