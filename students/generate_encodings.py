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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DeepFace configuration
DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'Facenet')
DEEPFACE_DETECTOR = 'opencv' 


def extract_face_single(photo):
    """
    Extract faces from a single photo (NumPy array).
    """
    faces = []
    if not isinstance(photo, np.ndarray):
        logger.error("Photo must be a NumPy array")
        return faces, "Photo must be a NumPy array"
    try:
        if photo.shape[0] < 100 or photo.shape[1] < 100:
            logger.warning("Image has low resolution")
            return faces, "Image has low resolution"
        rgb_img = cv.cvtColor(photo, cv.COLOR_BGR2RGB)
        
        # Use a robust detector and enforce detection
        result = DeepFace.extract_faces(
            rgb_img,
            detector_backend=DEEPFACE_DETECTOR,
            enforce_detection=False,
            align=True
        )
        
        # Ensure exactly one face is detected
        if len(result) != 1:
            logger.warning(f"Expected one face, but found {len(result)}")
            return faces, f"Expected one face, but found {len(result)}"
        
        # Check confidence score
        confidence = result[0]['confidence']
        if confidence < 0.6:
            return faces, f"Low confidence face detection ({confidence})"
        
        # Validate facial area dimensions
        facial_area = result[0]['facial_area']
        x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
        
        # Extract the face
        face_img = rgb_img[y:y+h, x:x+w]
        faces.append(face_img)
        logger.info("Face extracted")
        
        return faces, None
    except Exception as e:
        logger.error(f"Error extracting face: {e}")
        return faces, f"Error extracting face: {str(e)}"

def extract_faces(photos):
    """
    Extract faces from a list of photos using parallel processing.
    
    Args:
        photos (list): List of images as NumPy arrays.
    
    Returns:
        tuple: (List of detected face regions (NumPy arrays), error message if any).
    """
    try:
        logger.debug(f"Extracting faces from {len(photos)} photos")
        with ThreadPoolExecutor() as executor:
            results = executor.map(extract_face_single, photos)
        faces = []
        errors = []
        for sublist, error in results:
            faces.extend(sublist)
            if error:
                errors.append(error)
        logger.debug(f"Extracted {len(faces)} faces")
        return faces, errors if errors else None
    except Exception as e:
        logger.error(f"Error in parallel face extraction: {e}")
        return [], f"Error in parallel face extraction: {str(e)}"

def store_embeddings(faces,student):
    """
    Store face embeddings in the database.
    
    Args:
        faces (list): List of face regions (NumPy arrays).
        ecode (EmbeddingsEncode): EmbeddingsEncode instance.
        cnic (str): Student's CNIC number.
    
    Returns:
        tuple: (bool: True if embeddings stored successfully, str: error message if any).
    """
    try:
        logger.debug(f"Storing embeddings for {student.university_roll_no}")
        existing_embeddings = StudentEmbedding.objects.filter(university_roll_no=student.university_roll_no)
        if existing_embeddings.exists():
            count = existing_embeddings.count()
            existing_embeddings.delete()
            logger.info(f"Deleted {count} existing embeddings for university roll  {student.university_roll_no}")

        for i, face in enumerate(faces):
            try:
                # Ensure face is in RGB format
                if face.shape[-1] == 3:
                    face_rgb = face
                else:
                    face_rgb = cv.cvtColor(face, cv.COLOR_BGR2RGB)
                embedding = DeepFace.represent(
                    face_rgb,
                    model_name='Facenet512',
                    enforce_detection=False,
                    detector_backend='skip'
                )
                if not embedding or not isinstance(embedding, list) or len(embedding) != 1:
                    logger.error(f"Invalid embedding format for face {i+1} of cnic {student.university_roll_no}")
                    return False, f"Invalid embedding format for face {i+1}"
                embedding_vector = embedding[0]["embedding"]
                
                embedding_binary = pickle.dumps(embedding_vector)
                StudentEmbedding.objects.create(
                    student=student,
                    university_roll_no=student.university_roll_no,
                    embedding_data=embedding_binary
                )
                logger.info(f"Generated embedding {i+1}/{len(faces)} for {student.university_roll_no}")
            except Exception as e:
                logger.error(f"Error generating embedding for face {i+1} of {student.university_roll_no}: {e}")
                return False, f"Error generating embedding for face {i+1}: {str(e)}"
        logger.info(f"Successfully processed {len(faces)} faces for {student.university_roll_no}")
        return True, None
    except Exception as e:
        logger.error(f"Error storing embeddings for {student.university_roll_no}: {e}")
        return False, f"Error storing embeddings: {str(e)}"

def generate_embeddings(photos,student):
    try:
        if not photos:
            logger.warning("No photos provided for embedding generation")
            return False, "No photos provided"
        
        # Extract faces from the photos
        logger.debug("Calling extract_faces")
        faces, face_errors = extract_faces(photos)
        if not faces:
            logger.warning("No valid faces extracted from the provided photos")
            return False, face_errors[0] if face_errors else "No valid faces extracted"
        if len(faces) < 10:
            logger.warning(f"Not enough faces extracted for {student.university_roll_no}: {len(faces)} found, at least 10 required")
            return False, f"Not enough faces extracted for {student.university_roll_no}: {len(faces)} found, at least 10 required"
        # Store embeddings in the database
        logger.debug("Calling store_embeddings")
        success, error = store_embeddings(faces,student)
        if success:
            logger.info(f"Embeddings generated and stored successfully for {len(faces)} faces of {student.university_roll_no}")
            return True, None
        else:
            return False, error
    except Exception as e:
        return False, f"Error in generate_embeddings: {str(e)}"