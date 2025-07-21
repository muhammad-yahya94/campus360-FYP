import logging
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from students.models import Student
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def send_assignment_notification(assignment):
    """
    Send email notification to class representatives (CR/GR) about a new assignment.
    """
    try:
        # Get the course offering and program
        course_offering = assignment.course_offering
        program = course_offering.program
        
        # Get all active students in the program who are CR or GR
        representatives = Student.objects.filter(
            program=program,
            is_active=True,
            role__in=['CR', 'GR']
        ).select_related('applicant')
        
        if not representatives.exists():
            logger.warning(f"No CR/GR found for program {program}")
            return False
        
        # Prepare email content
        subject = f"New Assignment: {assignment.title}"
        
        for rep in representatives:
            try:
                context = {
                    'assignment': assignment,
                    'recipient_name': rep.applicant.full_name,
                    'role': rep.get_role_display(),
                    'course_name': course_offering.course.name,
                    'due_date': assignment.due_date,
                    'max_points': assignment.max_points,
                    'description': assignment.description,
                }
                
                html_message = render_to_string('emails/new_assignment_notification.html', context)
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[rep.applicant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Assignment notification sent to {rep.applicant.email}")
                
            except Exception as e:
                logger.error(f"Error sending assignment notification to {rep.applicant.email}: {str(e)}")
                continue
                
        return True
        
    except Exception as e:
        logger.error(f"Error in send_assignment_notification: {str(e)}")
        return False

def send_quiz_notification(quiz):
    """
    Send email notification to class representatives (CR/GR) about a new quiz.
    """
    try:
        # Get the course offering and program
        course_offering = quiz.course_offering
        program = course_offering.program
        
        # Get all active students in the program who are CR or GR
        representatives = Student.objects.filter(
            program=program,
            is_active=True,
            role__in=['CR', 'GR']
        ).select_related('applicant')
        
        if not representatives.exists():
            logger.warning(f"No CR/GR found for program {program}")
            return False
        
        # Calculate total marks
        total_marks = sum(question.marks for question in quiz.questions.all())
        
        # Prepare email content
        subject = f"New Quiz: {quiz.title}"
        
        for rep in representatives:
            try:
                context = {
                    'quiz': quiz,
                    'recipient_name': rep.applicant.full_name,
                    'role': rep.get_role_display(),
                    'course_name': course_offering.course.name,
                    'total_questions': quiz.questions.count(),
                    'total_marks': total_marks,
                    'time_limit': f"{quiz.timer_seconds // 60} minutes",
                }
                
                html_message = render_to_string('emails/new_quiz_notification.html', context)
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[rep.applicant.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Quiz notification sent to {rep.applicant.email}")
                
            except Exception as e:
                logger.error(f"Error sending quiz notification to {rep.applicant.email}: {str(e)}")
                continue
                
        return True
        
    except Exception as e:
        logger.error(f"Error in send_quiz_notification: {str(e)}")
        return False
