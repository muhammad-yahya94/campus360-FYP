from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from students.models import Student
from .Face_Attandence import face_attandence_detection
from courses.models import CourseOffering
import base64
import cv2
import numpy as np


@require_POST
def face_attendance_detect_simple(request):
    print("face_attendance_detect_simple called")
    """
    Simple API endpoint to call face_attandence_detection function directly with enrolled students.
    """
    try:
        print(f"[DEBUG] face_attendance_detect_simple called with method: {request.method}")
        print(f"[DEBUG] POST data: {request.POST}")
        
        course_offering_id = request.POST.get('course_offering_id')
        print(f"[DEBUG] course_offering_id: {course_offering_id}")
        
        if not course_offering_id:
            print("[DEBUG] No course_offering_id provided")
            return JsonResponse({'success': False, 'message': 'Course offering ID is required.'}, status=400)

        course_offering = get_object_or_404(CourseOffering, id=course_offering_id)
        print(f"[DEBUG] Found course offering: {course_offering}")

        from students.models import CourseEnrollment
        enrollments = CourseEnrollment.objects.filter(
            course_offering=course_offering,
            status='enrolled'
        ).select_related('student_semester_enrollment__student')
        
        print(f"[DEBUG] Found {enrollments.count()} enrollments")

        students = [enrollment.student_semester_enrollment.student for enrollment in enrollments]
        print(f"[DEBUG] Processing {len(students)} students")

        detected_faces = face_attandence_detection(students)
        print(f"[DEBUG] Face detection completed, detected {len(detected_faces)} faces")

        return JsonResponse({
            'success': True,
            'detected_faces_count': len(detected_faces),
            'message': f'Face attendance detection called. Detected {len(detected_faces)} faces.'
        })
        
    except Exception as e:
        print(f"[ERROR] Exception in face_attendance_detect_simple: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
