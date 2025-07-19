from django import template
from courses.models import LectureReplacement 
from datetime import date

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



register = template.Library()

@register.filter
def lookup_replacements(course_offering_id):
    replacements = LectureReplacement.objects.filter(course_offering_id=course_offering_id).select_related('original_teacher', 'replacement_teacher')
    return [
        {
            'original_teacher': f"{r.original_teacher.user.get_full_name()}",
            'replacement_teacher': f"{r.replacement_teacher.user.get_full_name()}",
            'replacement_type': r.replacement_type,
            'replacement_date': r.replacement_date,
            'is_active': (
                r.replacement_type == 'permanent' or
                (r.replacement_type == 'temporary' and r.replacement_date and date.today() >= r.replacement_date)
            )
        }
        for r in replacements
    ]