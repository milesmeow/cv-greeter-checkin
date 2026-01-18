"""
Face recognition module.

Handles face detection, encoding, and matching against the visitor database.
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass

# face_recognition is a wrapper around dlib
import face_recognition


@dataclass
class RecognitionResult:
    """Result of a face recognition attempt."""
    success: bool
    visitor_id: Optional[int] = None
    visitor_name: Optional[str] = None
    confidence: float = 0.0
    face_encoding: Optional[np.ndarray] = None
    face_location: Optional[Tuple[int, int, int, int]] = None
    message: str = ""


class FaceRecognizer:
    """
    Handles face detection and recognition.
    
    Uses the face_recognition library which is built on dlib.
    Face encodings are 128-dimensional vectors that can be compared
    using Euclidean distance.
    """
    
    def __init__(self, tolerance: float = 0.6):
        """
        Initialize the face recognizer.
        
        Args:
            tolerance: How strict face matching should be.
                      Lower = stricter (fewer false positives, more false negatives)
                      Higher = more lenient (more false positives, fewer false negatives)
                      Default 0.6 is a good balance.
        """
        self.tolerance = tolerance
    
    def detect_and_encode(self, image: np.ndarray) -> RecognitionResult:
        """
        Detect faces in an image and encode the first one found.

        Args:
            image: RGB image as numpy array

        Returns:
            RecognitionResult with face_encoding and face_location if found
        """
        # Ensure image is in correct format for face_recognition
        # Must be 8-bit RGB (uint8, 3 channels), contiguous in memory
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)
        if len(image.shape) == 2:
            # Grayscale - convert to RGB
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:
            # RGBA - drop alpha channel
            image = image[:, :, :3]

        # Ensure array is contiguous (required by dlib)
        if not image.flags['C_CONTIGUOUS']:
            image = np.ascontiguousarray(image)

        # Debug: print image info
        print(f"Image shape: {image.shape}, dtype: {image.dtype}, contiguous: {image.flags['C_CONTIGUOUS']}")

        # Find all faces in the image
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            return RecognitionResult(
                success=False,
                message="No face detected. Please ensure face is visible to camera."
            )
        
        if len(face_locations) > 1:
            return RecognitionResult(
                success=False,
                message=f"Multiple faces detected ({len(face_locations)}). Please ensure only one person is in frame."
            )
        
        # Get the face encoding
        face_location = face_locations[0]
        encodings = face_recognition.face_encodings(image, [face_location])
        
        if not encodings:
            return RecognitionResult(
                success=False,
                message="Could not encode face. Please try again."
            )
        
        return RecognitionResult(
            success=True,
            face_encoding=encodings[0],
            face_location=face_location,
            message="Face detected successfully."
        )
    
    def find_match(
        self, 
        face_encoding: np.ndarray, 
        known_encodings: List[Tuple[int, str, np.ndarray]]
    ) -> RecognitionResult:
        """
        Compare a face encoding against known visitors.
        
        Args:
            face_encoding: The 128-dim encoding to match
            known_encodings: List of (visitor_id, name, encoding) tuples
            
        Returns:
            RecognitionResult with match info if found
        """
        if not known_encodings:
            return RecognitionResult(
                success=False,
                face_encoding=face_encoding,
                message="No registered visitors yet."
            )
        
        # Extract just the encodings for comparison
        ids = [k[0] for k in known_encodings]
        names = [k[1] for k in known_encodings]
        encodings = [k[2] for k in known_encodings]
        
        # Calculate distances to all known faces
        distances = face_recognition.face_distance(encodings, face_encoding)
        
        # Find the best match
        best_idx = np.argmin(distances)
        best_distance = distances[best_idx]
        
        # Convert distance to confidence (0-1, higher is better)
        # distance of 0 = perfect match (confidence 1.0)
        # distance of tolerance = threshold match (confidence ~0.5)
        confidence = max(0, 1 - (best_distance / self.tolerance))
        
        if best_distance <= self.tolerance:
            return RecognitionResult(
                success=True,
                visitor_id=ids[best_idx],
                visitor_name=names[best_idx],
                confidence=confidence,
                face_encoding=face_encoding,
                message=f"Welcome back, {names[best_idx]}!"
            )
        else:
            return RecognitionResult(
                success=False,
                confidence=confidence,
                face_encoding=face_encoding,
                message="Face not recognized. New visitor?"
            )
    
    def recognize(
        self,
        image: np.ndarray,
        known_encodings: List[Tuple[int, str, np.ndarray]]
    ) -> RecognitionResult:
        """
        Full recognition pipeline: detect, encode, and match.
        
        This is the main method to use for check-in.
        
        Args:
            image: RGB image as numpy array
            known_encodings: List of (visitor_id, name, encoding) tuples
            
        Returns:
            RecognitionResult with full match info
        """
        # Step 1: Detect and encode face
        detection_result = self.detect_and_encode(image)
        
        if not detection_result.success:
            return detection_result
        
        # Step 2: Try to match against known faces
        match_result = self.find_match(
            detection_result.face_encoding,
            known_encodings
        )
        
        # Preserve face location from detection
        match_result.face_location = detection_result.face_location
        
        return match_result
    
    def set_tolerance(self, tolerance: float):
        """
        Adjust the matching tolerance.
        
        Args:
            tolerance: New tolerance value (0.4-0.8 typical range)
        """
        self.tolerance = max(0.1, min(1.0, tolerance))


def draw_face_box(
    image: np.ndarray,
    face_location: Tuple[int, int, int, int],
    name: str = "",
    color: Tuple[int, int, int] = (0, 255, 0)
) -> np.ndarray:
    """
    Draw a box around a detected face.
    
    Args:
        image: RGB image as numpy array
        face_location: (top, right, bottom, left) coordinates
        name: Name to display (optional)
        color: RGB color for the box
        
    Returns:
        Image with box drawn
    """
    import cv2
    
    top, right, bottom, left = face_location
    
    # Draw rectangle
    cv2.rectangle(image, (left, top), (right, bottom), color, 2)
    
    # Draw name label if provided
    if name:
        cv2.rectangle(image, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            image, name, (left + 6, bottom - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
        )
    
    return image
