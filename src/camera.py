"""
Camera module for webcam capture.

Handles webcam initialization, frame capture, and cleanup.
"""

import cv2
import numpy as np
from typing import Optional, Tuple


class Camera:
    """Manages webcam capture for the check-in system."""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera.
        
        Args:
            camera_index: Which camera to use (0 = default/first camera)
        """
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_running = False
    
    def start(self) -> bool:
        """
        Start the camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        if self._is_running:
            return True
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_index}")
            return False
        
        # Set camera properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self._is_running = True
        return True
    
    def stop(self):
        """Release the camera."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self._is_running = False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Returns:
            BGR image as numpy array, or None if capture failed
        """
        if not self._is_running or self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        return frame
    
    def get_frame_rgb(self) -> Optional[np.ndarray]:
        """
        Capture a frame and convert to RGB.
        
        The face_recognition library expects RGB format.
        
        Returns:
            RGB image as numpy array, or None if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def get_frame_for_display(self) -> Optional[np.ndarray]:
        """
        Capture a frame ready for Tkinter display.
        
        Flips horizontally (mirror effect) for more natural interaction.
        
        Returns:
            RGB image as numpy array, or None if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        # Mirror the image for more natural feel
        frame = cv2.flip(frame, 1)
        
        # Convert BGR to RGB for display
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def capture_for_recognition(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Capture a frame for face recognition.
        
        Returns:
            Tuple of (display_frame, recognition_frame)
            - display_frame: Mirrored RGB for UI display
            - recognition_frame: Non-mirrored RGB for face_recognition
            
            Returns (None, None) if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None, None
        
        # Display frame (mirrored)
        display_frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        
        # Recognition frame (not mirrored - face_recognition needs consistent orientation)
        recognition_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return display_frame, recognition_frame
    
    @property
    def is_running(self) -> bool:
        """Check if camera is currently capturing."""
        return self._is_running
    
    @staticmethod
    def list_available_cameras(max_cameras: int = 5) -> list:
        """
        Find available camera indices.
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            List of available camera indices
        """
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
