import os
import logging
import cv2 as cv
import numpy as np
import pickle
from django.conf import settings
from django.utils.text import slugify
from deepface import DeepFace
from students.models import EmbeddingsEncode, FaceEmbedding
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepFace configuration
DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'Facenet')
DEEPFACE_DETECTOR = 'retinaface'  # Use a more robust detector

def get_embeddigcode(session_name, program_name, shift):
    """Get the embedding code for students in given session, program and shift"""
    from students.models import Student
    from django.db.models import Q
    
    # Get students matching the criteria
    students = Student.objects.filter(
        Q(applicant__session__name=session_name) &
        Q(program__name=program_name) &
        Q(applicant__shift=shift)
    ).select_related('applicant', 'program')
    
    # Get their embedding codes
    embedding_codes = []
    for student in students:
        if hasattr(student, 'face_embedding'):
            embedding_codes.append(student.face_embedding.encoding)
    
    return embedding_codes

def liveface_detection(embedding_codes, camera_name):
    """Perform live face detection using given embedding codes"""
    import cv2
    from deepface import DeepFace
    
    cap = cv2.VideoCapture(camera_name)
    detected_faces = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        try:
            # Detect faces in frame
            detections = DeepFace.extract_faces(
                frame,
                detector_backend=DEEPFACE_DETECTOR,
                enforce_detection=False
            )
            
            for detection in detections:
                if detection['confidence'] > 0.9:  # Only consider confident detections
                    # Compare with known embeddings
                    result = DeepFace.verify(
                        img1_path=frame,
                        img2_path=detection['face'],
                        model_name=DEEPFACE_MODEL,
                        detector_backend=DEEPFACE_DETECTOR,
                        distance_metric='cosine',
                        enforce_detection=False
                    )
                    
                    if result['verified']:
                        detected_faces.append({
                            'face': detection['face'],
                            'confidence': result['distance']
                        })
                        
        except Exception as e:
            logger.error(f"Face detection error: {str(e)}")
            continue
            
    cap.release()
    return detected_faces

def face_attandence_detection(session_name, program_name, shift):
    """Main function to detect faces for attendance"""
    logger.info(f"Starting face attendance for {session_name}, {program_name}, {shift}")
    
    try:
        # Get embeddings for students in this session/program/shift
        embedding_codes = get_embeddigcode(session_name, program_name, shift)
        
        if not embedding_codes:
            logger.warning(f"No embedding codes found for {session_name}/{program_name}/{shift}")
            return []
            
        # Perform face detection (default camera 0)
        detected_faces = liveface_detection(embedding_codes, 0)
        
        logger.info(f"Detected {len(detected_faces)} faces")
        return detected_faces
        
    except Exception as e:
        logger.error(f"Error in face_attandence_detection: {str(e)}")
        return []
