from admissions.models import Applicant
from .models import Student


# context_processors.py
def student_full_name(request):
    if request.user.is_authenticated:
        try:
            applicant = Applicant.objects.get(user=request.user)
            # Check if a student profile exists
            if hasattr(applicant, 'student_profile'):
                return {
                    'student_full_name': applicant.full_name
                }
        except Applicant.DoesNotExist:
            pass
    return {
        'student_full_name': None
    }

   