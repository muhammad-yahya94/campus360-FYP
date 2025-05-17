# university/context_processors.py

from academics.models import Faculty
from faculty_staff.models import Office

def faculty_context(request):
    faculties = Faculty.objects.prefetch_related('departments__programs').all()
    return {'nav_faculties': faculties}

def offices_context(request):
    offices = Office.objects.all()
    return {'nav_offices': offices}
