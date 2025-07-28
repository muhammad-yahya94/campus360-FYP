import os
import logging
import cv2 as cv
import numpy as np
import pickle
from django.conf import settings
from django.utils.text import slugify
from deepface import DeepFace
from students.models import StudentEmbedding
from concurrent.futures import ThreadPoolExecutor
import cv2
from deepface import DeepFace
from scipy.spatial.distance import cosine, euclidean

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepFace configuration
DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'Facenet')
DEEPFACE_DETECTOR = 'opencv'  # Use a more robust detector

def load_embeddings(students):
    print("Loading embeddings for students")
    embedding_codes = StudentEmbedding.objects.filter( university_roll_no__in=[student.university_roll_no for student in students])
    if not embedding_codes:
        logger.warning(f"No embedding codes found for students: {[student.university_roll_no for student in students]}")
        return []
    return embedding_codes

def liveface_detection(embedding_codes, camera_name):
    """Perform live face detection using given embedding codes and compare with cosine similarity"""
    detected_faces = []
    # Assume embedding_codes is a list of tuples: [(embedding, university_roll_number), ...]
    stored_embeddings = [np.array(emb[0]) for emb in embedding_codes]  # Extract embeddings
    roll_numbers = [emb[1] for emb in embedding_codes]  # Extract corresponding roll numbers
    threshold = 0.4  # Cosine similarity threshold (adjust based on model, e.g., 0.4 for Facenet)

    # Open video capture
    cap = cv.VideoCapture(camera_name)
    if not cap.isOpened():
        logger.error(f"Could not open camera {camera_name}")
        return detected_faces

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                break

            # Display the frame
            cv.imshow('Live Face Detection', frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

            try:
                # Extract embeddings from the frame
                faces = DeepFace.represent(
                    img=frame,
                    model_name=DEEPFACE_MODEL,
                    detector_backend=DEEPFACE_DETECTOR,
                    enforce_detection=False
                )

                # Process each detected face
                for face in faces:
                    face_embedding = np.array(face["embedding"])
                    # Compare with each stored embedding
                    for idx, stored_emb in enumerate(stored_embeddings):
                        distance = cosine(stored_emb, face_embedding)
                        if distance <= threshold:
                            # Add match details with university_roll_number to detected_faces
                            detected_faces.append({
                                "university_roll_number": roll_numbers[idx],
                                "cosine_distance": distance,
                                "face_location": face.get("facial_area", {}),
                                "match": True
                            })
                        else:
                            detected_faces.append({
                                "university_roll_number": roll_numbers[idx],
                                "cosine_distance": distance,
                                "face_location": face.get("facial_area", {}),
                                "match": False
                            })

            except Exception as e:
                logger.warning(f"No faces detected or error in processing frame: {str(e)}")

    finally:
        cap.release()
        cv.destroyAllWindows()

    return detected_faces

def face_attandence_detection(students):
    # """Main function to detect faces for attendance"""
    print("Face attendance detection started")
    print(f"Number of students: {len(students)}")
    if not students:
        logger.warning("No students provided for face attendance detection.")
        return []
    
    try:
        embedding_codes = load_embeddings(students)
        print(f"Loaded {len(embedding_codes)} embedding codes")

        # if not embedding_codes:
        #     logger.warning(f"No embedding codes found")
        #     return []
            
        # Perform face detection (default camera 0)
        detected_faces = liveface_detection(embedding_codes, 0)
        print(f"Detected faces are {detected_faces}")
        logger.info(f"Detected {len(detected_faces)} faces")
        return detected_faces
        
    except Exception as e:
        logger.error(f"Error in face_attandence_detection: {str(e)}")
        return []
