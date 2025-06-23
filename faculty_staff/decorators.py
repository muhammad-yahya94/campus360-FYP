from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden

def hod_required(view_func):
    """
    Decorator to restrict access to only Head of Department users.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'teacher_profile'):
            return HttpResponseForbidden("You do not have permission to access this page.")
        if request.user.teacher_profile.designation != 'head_of_department':
            return HttpResponseForbidden("Only the Head of Department can access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def hod_or_professor_required(view_func):
    """
    Decorator to restrict access to Head of Department or Professor users.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'teacher_profile'):
            return HttpResponseForbidden("You do not have permission to access this page.")
        if request.user.teacher_profile.designation not in ['head_of_department', 'professor']:
            return HttpResponseForbidden("Only the Head of Department or Professors can access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view