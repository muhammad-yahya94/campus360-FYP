# faculty_staff/context_processors.py
from admissions.models import AcademicSession

def academic_sessions_processor(request):
    sessions = AcademicSession.objects.all().order_by('-start_year')
    return {
        'academic_sessions': sessions
    }
