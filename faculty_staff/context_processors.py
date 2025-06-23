# faculty_staff/context_processors.py
from admissions.models import AcademicSession
from .models import Teacher, TeacherDetails
def academic_sessions_processor(request):
    sessions = AcademicSession.objects.all().order_by('-start_year')
    return {
        'academic_sessions': sessions
    }




def teacher_details_status(request):
    context = {}
    if request.user.is_authenticated and hasattr(request.user, 'teacher_profile'):
        teacher = request.user.teacher_profile
        details = getattr(teacher, 'details', None)
        status = details.status if details and details.status else "N/A"
        context['teacher_status'] = status
        context['teacher_full_name'] = request.user.get_full_name()
    return context